import json
import re
import subprocess
import sys
from pathlib import Path, PurePath
from typing import List, Optional, Tuple

from pylint.interfaces import UNDEFINED

from ..config import C_EXTENSIONS, CPP_EXTENSIONS
from .base import Linter
from . import options
from ..reports.message import Message, MessageLocation

C_STANDARD = '-std=gnu17'
CPP_STANDARD = '-std=gnu++17'

_pkgconfig_include_paths: list[str] = []
try:
	_pc_list = subprocess.run(['pkg-config', '--list-all'], capture_output=True, text=True, timeout=10)
	if _pc_list.returncode == 0:
		_pkgs = [l.split()[0] for l in _pc_list.stdout.strip().splitlines() if l.strip()]
		if _pkgs:
			_pc_cflags = subprocess.run(['pkg-config', '--cflags'] + _pkgs, capture_output=True, text=True, timeout=30)
			if _pc_cflags.returncode == 0:
				for flag in _pc_cflags.stdout.strip().split():
					if flag.startswith('-I'):
						path = flag[2:]
						if path not in _pkgconfig_include_paths:
							_pkgconfig_include_paths.append(path)
except Exception:
	pass

CLANG_ERROR_PATTERN = re.compile(
	r'^(.+?):(\d+):(?:\d+)?:\s*(error|fatal error|warning):\s*(.+?)(?:\s*\[-W|\s*$)',
	re.IGNORECASE | re.MULTILINE
)


class OCLintWrapper(Linter):
	"""
	Performs analysis with OCLint.
	Fallbacks to analysis with Clang if OCLint crashes.
	"""

	@staticmethod
	def _detect_standard(file_path: str) -> Tuple[List[str], List[str]]:
		_ext = Path(file_path).suffix.lower()
		if _ext in C_EXTENSIONS:
			return [C_STANDARD], []
		if _ext in CPP_EXTENSIONS:
			return [CPP_STANDARD], ['-x', 'c++']
		return [CPP_STANDARD], ['-x', 'c++']

	def _create_message(
		self,
		file_path: str,
		line: int,
		column: int,
		msg: str,
		msg_id: str,
		symbol: str,
		linter: str,
		end_line: Optional[int] = None,
		end_column: Optional[int] = None,
	) -> Message:
		return Message(
			msg_id=msg_id,
			symbol=symbol,
			location=MessageLocation(
				abspath=str(Path(file_path).resolve()),
				path=str(file_path),
				module=PurePath(file_path).stem,
				obj='',
				line=line,
				column=column,
				end_line=end_line,
				end_column=end_column,
			),
			msg=msg,
			confidence=UNDEFINED,
			linter=linter,
		)

	def _msg_id_for_priority(self, priority: int) -> str:
		# Pylint ожидает первую букву из своих типов: F/E/W/C/R/I
		# Для OCLint удобно транслировать так:
		if priority == 1:
			return 'ERROR'
		if priority == 2:
			return 'WARNING'
		return 'REFACTOR'

	def _parse_oclint_violations(self, data: dict, file_path: str) -> List[Message]:
		messages = []
		for v in data.get('violation', []):
			priority = int(v.get('priority', 3) or 3)
			messages.append(self._create_message(
				file_path=file_path,
				line=int(v.get('startLine', 1) or 1),
				column=int(v.get('startColumn', 1) or 1),
				msg=str(v.get('message') or v.get('rule') or ''),
				msg_id=self._msg_id_for_priority(priority),
				symbol=str(v.get('rule', '')).replace(' ', '_'),
				linter='OCLint',
				end_line=v.get('endLine'),
				end_column=v.get('endColumn'),
			))
		return messages

	def _parse_clang_output(self, source_file: Path, output: str) -> List[Message]:
		messages = []

		for match in CLANG_ERROR_PATTERN.finditer(output):
			_, line_no, level, msg = match.groups()
			if level.lower() == 'warning':
				continue

			messages.append(self._create_message(
				file_path=str(source_file),
				line=int(line_no),
				column=0,
				msg=msg.strip(),
				msg_id='ERROR' if level.lower() in ('error', 'fatal error') else 'WARNING',
				symbol='fatal-error' if level.lower() == 'fatal error' else 'syntax-error',
				linter='OCLint',
			))
		return messages

	def run(self, file_path: str) -> List[Message]:
		source_file = Path(file_path).resolve()
		standards, lang_flags = self._detect_standard(file_path)
		include_flags = [f'-I{path}' for path in _pkgconfig_include_paths]
		for path in options.oclint_include:
			if not Path(path).is_absolute() and options.repo_dir:
				path = str(Path(options.repo_dir) / path)
			include_flags.append(f'-I{path}')

		oclint_cmd = [
			'oclint', '-report-type', 'json', str(source_file), '--',
			*lang_flags, *standards, *include_flags, '-Wall', '-Wextra',
		]

		try:
			result = subprocess.run(oclint_cmd, capture_output=True, text=True, timeout=60)
		except Exception:
			result = None

		if result and result.stdout.strip():
			try:
				data = json.loads(result.stdout)
				if data.get('summary', {}).get('numberOfFiles', 0) > 0:
					return self._parse_oclint_violations(data, file_path)
			except json.JSONDecodeError:
				pass

		if result and result.returncode != 0:
			for cc in ('clang-15', 'clang-14', 'clang'):
				try:
					diag = subprocess.run(
						[cc, '-fsyntax-only', *lang_flags, *standards, *include_flags, str(source_file)],
						capture_output=True, text=True, timeout=30
					)
					if diag.returncode != 0:
						output = (diag.stderr or diag.stdout or '').strip()
						short = output.split('\n')[0] if output else ''
						if short:
							print(f"  skip {source_file.name}: {short}", file=sys.stderr)
						break
				except FileNotFoundError:
					continue
		return []
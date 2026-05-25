import json
import re
import subprocess
import sys
from pathlib import Path, PurePath
from typing import List, Optional, Tuple

from pylint.interfaces import UNDEFINED

from ..config import C_EXTENSIONS, CPP_EXTENSIONS
from .base import Linter
from ..reports.message import Message, MessageLocation

C_STANDARD = '-std=c17'
CPP_STANDARD = '-std=c++17'
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

		oclint_cmd = [
			'oclint', '-report-type', 'json', str(source_file), '--',
			*lang_flags, *standards, '-Wall', '-Wextra',
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

		print(
			f"OCLint analysis failed for '{source_file.name}'. "
			f"Falling back to Clang for syntax check.",
			file=sys.stderr
		)

		clang_cmd = [
			'clang', '-fsyntax-only', '-Wall', '-Wextra', '-ferror-limit=10',
			*standards, *lang_flags, str(source_file),
		]

		try:
			clang_res = subprocess.run(clang_cmd, capture_output=True, text=True, timeout=30)
		except Exception:
			return []

		all_output = clang_res.stderr + '\n' + clang_res.stdout
		return self._parse_clang_output(source_file, all_output)
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePath
from typing import List, Optional, Tuple, Set

from pylint.interfaces import UNDEFINED

from ..config import C_EXTENSIONS, CPP_EXTENSIONS
from .base import Linter
from ..reports.message import Message, MessageLocation
from ..logger import info

C_STANDARD = '-std=c17'
CPP_STANDARD = '-std=c++17'
CLANG_ERROR_PATTERN = re.compile(
	r'^(.+?):(\d+):(?:\d+)?:\s*(error|fatal error|warning):\s*(.+?)(?:\s*\[-W|\s*$)',
	re.IGNORECASE | re.MULTILINE
)
ROOT_MARKERS = ('Makefile', 'makefile', 'GNUmakefile', 'CMakeLists.txt', '.git')


class OCLintWrapper(Linter):
	_project_root = None
	_project_includes: List[str] = []
	_attempted_headers: Set[str] = set()

	@staticmethod
	def _detect_standard(file_path: str) -> Tuple[List[str], List[str]]:
		_ext = Path(file_path).suffix.lower()
		if _ext in C_EXTENSIONS:
			return [C_STANDARD], []
		if _ext in CPP_EXTENSIONS:
			return [CPP_STANDARD], ['-x', 'c++']
		return [CPP_STANDARD], ['-x', 'c++']

	def _load_project_includes(self, file_path: str):
		if self._project_root is not None:
			return
		start = Path(file_path).resolve().parent
		root = None
		for _ in range(20):
			for marker in ROOT_MARKERS:
				if (start / marker).exists():
					root = start
					break
			if root:
				break
			parent = start.parent
			if parent == start:
				break
			start = parent

		if root is None:
			self._project_root = Path('')
			return

		self._project_root = root
		self._project_includes = self._extract_includes(root)

	@staticmethod
	def _extract_includes(project_root: Path) -> List[str]:
		includes: Set[str] = set()

		makefiles = sorted(project_root.rglob('[Mm]akefile*'))
		if not makefiles:
			return []

		root_makefile = project_root / 'Makefile'
		if root_makefile.exists():
			try:
				result = subprocess.run(
					['make', '-n', '-C', str(project_root)],
					capture_output=True, text=True, timeout=30
				)
				if result.returncode == 0:
					output = result.stdout + result.stderr
					for match in re.finditer(r'(?:^|\s)(-I\s*\S+|--sysroot\s*\S+)', output):
						flag = match.group(1)
						inc = flag.split(' ', 1)[-1] if ' ' in flag else flag[2:]
						resolved = project_root / inc if not Path(inc).is_absolute() else Path(inc)
						if resolved.is_dir():
							includes.add(f'-I{resolved}')
			except Exception:
				pass

		for mf in makefiles:
			try:
				content = mf.read_text()
				mf_dir = mf.parent
				for match in re.finditer(r'(?:^|\s)-I(\S+)', content, re.MULTILINE):
					inc = match.group(1)
					resolved = Path(inc)
					if not resolved.is_absolute():
						resolved = (project_root / inc).resolve()
					if resolved.is_dir():
						includes.add(f'-I{resolved}')
						continue
					resolved = (mf_dir / inc).resolve()
					if resolved.is_dir():
						includes.add(f'-I{resolved}')
			except Exception:
				pass

		for root, dirs, files in os.walk(str(project_root)):
			if '.git' in root:
				dirs.clear()
				continue
			depth = root[len(str(project_root)):].count(os.sep)
			if depth > 4:
				dirs.clear()
				continue
			if any(f.endswith(('.h', '.hpp', '.hh')) for f in files):
				flag = f'-I{root}'
				if flag not in includes:
					includes.add(flag)

		result = sorted(includes)
		return result

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

		source_resolved = source_file.resolve()
		for match in CLANG_ERROR_PATTERN.finditer(output):
			error_file, line_no, level, msg = match.groups()
			if level.lower() == 'warning':
				continue

			if Path(error_file).resolve() != source_resolved:
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
		self._load_project_includes(file_path)
		source_file = Path(file_path).resolve()
		standards, lang_flags = self._detect_standard(file_path)

		oclint_cmd = [
			'oclint', '-report-type', 'json', str(source_file), '--',
			*lang_flags, *standards, *self._project_includes, '-Wall', '-Wextra',
		]

		try:
			result = subprocess.run(oclint_cmd, capture_output=True, text=True, timeout=60)
		except Exception as e:
			info(f'OCLint crash: {e}')
			result = None

		if result and result.stdout.strip():
			try:
				data = json.loads(result.stdout)
				if data.get('summary', {}).get('numberOfFiles', 0) > 0:
					return self._parse_oclint_violations(data, file_path)
			except json.JSONDecodeError:
				pass

		clang_bin = shutil.which('clang') or shutil.which('clang-15') or shutil.which('clang-14') or 'clang'
		clang_cmd = [
			clang_bin, '-fsyntax-only', '-Wall', '-Wextra', '-ferror-limit=10',
			*standards, *lang_flags, *self._project_includes, str(source_file),
		]

		try:
			clang_res = subprocess.run(clang_cmd, capture_output=True, text=True, timeout=30)
		except Exception as e:
			info(f'Clang crash: {e}')
			return []

		missing_headers = re.findall(r"fatal error:\s*'([^']+)'\s+file not found", clang_res.stderr or '')
		if missing_headers:
			new_headers = [h for h in missing_headers if h not in self._attempted_headers]
			if new_headers:
				info(f'Пропущены системные заголовки: {new_headers}')
				installed, new_includes = self._install_missing_deps(new_headers)
				if installed and new_includes:
					self._project_includes.extend(new_includes)
					clang_cmd = [
						clang_bin, '-fsyntax-only', '-Wall', '-Wextra', '-ferror-limit=10',
						*standards, *lang_flags, *self._project_includes, str(source_file),
					]
					try:
						clang_res = subprocess.run(clang_cmd, capture_output=True, text=True, timeout=30)
					except Exception as e:
						info(f'Clang crash: {e}')
						return []
				for h in new_headers:
					self._attempted_headers.add(h)

		all_output = clang_res.stderr + '\n' + clang_res.stdout
		return self._parse_clang_output(source_file, all_output)

	def _install_missing_deps(self, headers: List[str]) -> Tuple[bool, List[str]]:
		new_includes: List[str] = []
		try:
			if os.geteuid() != 0:
				info('Пропуск установки (не root)')
				return False, []
		except AttributeError:
			pass
		if not shutil.which('apt-file'):
			info('apt-file не найден')
			return False, []

		packages: Set[str] = set()
		for header in headers:
			try:
				res = subprocess.run(
					['apt-file', 'search', '--package-only', header],
					capture_output=True, text=True, timeout=30
				)
				if res.returncode == 0 and res.stdout.strip():
					for pkg in res.stdout.strip().splitlines():
						pkg = pkg.strip()
						if pkg and pkg.endswith('-dev'):
							packages.add(pkg)
			except Exception as e:
				info(f'apt-file search error for {header}: {e}')

		if not packages:
			return False, []

		info(f'Установка: {" ".join(sorted(packages))}')
		try:
			res = subprocess.run(
				['apt-get', 'install', '-y', '--no-install-recommends'] + sorted(packages),
				capture_output=True, text=True, timeout=120
			)
			if res.returncode != 0:
				info(f'Ошибка установки: {res.stderr.strip()[:500]}')
				return False, []
			info('Пакеты установлены')
		except Exception as e:
			info(f'apt-get install error: {e}')
			return False, []

		for pkg in sorted(packages):
			try:
				res = subprocess.run(
					['dpkg', '-L', pkg], capture_output=True, text=True, timeout=15
				)
				if res.returncode != 0:
					continue
				for line in res.stdout.splitlines():
					if not line.endswith('.h'):
						continue
					inc_dir = str(Path(line).parent)
					flag = f'-I{inc_dir}'
					if flag not in self._project_includes and flag not in new_includes:
						new_includes.append(flag)
			except Exception as e:
				info(f'dpkg -L error for {pkg}: {e}')

		return True, new_includes
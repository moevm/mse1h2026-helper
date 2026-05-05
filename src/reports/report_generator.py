import re
from pathlib import PurePath
from typing import List, Optional

from pylint.message import Message

TMP_PREFIX = re.compile(r'^/tmp/tmp[^/]+/')


class ReportGenerator:
	_PATH_MARKERS = {'src', 'lib', 'app', 'tests', 'pkg', 'modules', 'core'}

	def __init__(
		self,
		show_code_snippet: bool = True,
		snippet_context_lines: int = 2,
		hosting_ref: Optional[str] = None,
		hosting_repo_url: Optional[str] = None
	):
		self.show_code_snippet = show_code_snippet
		self.snippet_context_lines = snippet_context_lines

		self._hosting_info = None
		if hosting_ref and hosting_repo_url:
			self._hosting_info = {
				'ref': hosting_ref,
				'repo_url': hosting_repo_url.rstrip('/')
			}

	def generate(self, messages: List[Message]) -> str:
		if not messages:
			return 'No issues found.\n'

		messages_by_file = self._group_by_file(messages)
		lines = []

		for file_path, file_messages in messages_by_file.items():
			display_path = self._format_path(file_path)

			lines.append(f'\nFile: {display_path}\n')

			for msg in file_messages:
				lines.append(self._format_message(msg, display_path))
				lines.append('')

		return '\n'.join(lines)

	def _group_by_file(self, messages: List[Message]) -> dict:
		grouped = {}
		for msg in messages:
			key = msg.abspath
			if key not in grouped:
				grouped[key] = []
			grouped[key].append(msg)
		return grouped

	def _format_path(self, path: str) -> str:
		if not path:
			return path
		path = path.replace('\\', '/')
		path = TMP_PREFIX.sub('', path)
		return path.lstrip('/')

	def _extract_repo_path(self, file_path: str) -> str:
		"""Converts absolute path (/tmp/xxx/src/file.py) to a path inside a repository (src/file.py)"""
		normalized = file_path.replace('\\', '/')
		parts = normalized.split('/')

		for i, part in enumerate(parts):
			if part in self._PATH_MARKERS:
				return '/'.join(parts[i:])

		return parts[-1]  # fallback: file name

	def _detect_hosting(self, repo_url: str) -> str:
		return 'github' if 'github.com' in repo_url else 'forgejo'

	def _make_link(self, msg: Message) -> str:
		if not self._hosting_info:
			return f'{file_path}:{line}:{column}'

		file_path, line, column = msg.abspath, msg.line, msg.column
		commit_sha = getattr(msg, 'specified_commit', None)

		base = self._hosting_info['repo_url'].rstrip('/')

		if commit_sha:
			return f'{base}/commit/{commit_sha}'

		clean_path = self._extract_repo_path(file_path).lstrip('/')

		if clean_path:
			hosting = self._detect_hosting(base)
			ref = self._hosting_info['ref']
			if hosting == 'github':
				return f'{base}/blob/{ref}/{clean_path}#L{line}'
			else:
				return f'{base}/src/commit/{ref}/{clean_path}#L{line}'
		return f'{base}/pull/files'

	def _format_message(self, msg: Message, display_path: str) -> str:
		linter = getattr(msg, 'linter', 'Unknown linter')
		hosting_link = self._make_link(msg)

		path = (display_path or '').strip()
		if path in {'.', ''}:
			path = getattr(msg, 'module', '') or getattr(msg, 'symbol', '')

		if path:
			second_line = f'{path}:{msg.line}: {msg.msg_id}: {msg.msg}'
		else:
			second_line = f'{msg.msg_id}: {msg.msg}'

		lines = [f'[{linter}]', second_line, hosting_link]

		if self.show_code_snippet:
			snippet = self._get_code_snippet(msg.abspath, msg.line)
			if snippet:
				lines.append('')
				lines.append('  Code:')
				for snippet_line in snippet:
					lines.append(f'    {snippet_line}')

		return '\n'.join(lines)

	def _get_code_snippet(self, file_path: str, target_line: int) -> Optional[List[str]]:
		try:
			with open(file_path, 'r', encoding='utf-8') as f:
				all_lines = f.readlines()
		except (OSError, UnicodeDecodeError):
			return None

		if not all_lines or target_line < 1 or target_line > len(all_lines):
			return None

		start = max(0, target_line - self.snippet_context_lines - 1)
		end = min(len(all_lines), target_line + self.snippet_context_lines)

		snippet = []
		for i in range(start, end):
			line_num = i + 1
			marker = ' >' if line_num == target_line else '  '
			content = all_lines[i].rstrip('\n\r')
			snippet.append(f'{marker} {line_num:4d} | {content}')

		return snippet
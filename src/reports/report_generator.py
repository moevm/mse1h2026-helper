from pathlib import PurePath
from typing import List, Optional

from pylint.message import Message


class ReportGenerator:
	_PATH_MARKERS = {'src', 'lib', 'app', 'tests', 'pkg', 'modules', 'core'}

	def __init__(
		self,
		show_code_snippet: bool = True,
		snippet_context_lines: int = 2,
		github_ref: Optional[str] = None,
		github_repo_url: Optional[str] = None
	):
		self.show_code_snippet = show_code_snippet
		self.snippet_context_lines = snippet_context_lines

		self._github_info = None
		if github_ref and github_repo_url:
			self._github_info = {
				'ref': github_ref,
				'repo_url': github_repo_url.rstrip('/')
			}

	def generate(self, messages: List[Message]) -> str:
		if not messages:
			return 'No issues found by Pylint.\n'

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

		normalized = str(PurePath(path)).replace('\\', '/')
		parts = normalized.split('/')

		for i, part in enumerate(parts):
			if part in self._PATH_MARKERS and i + 1 < len(parts):
				return '/'.join(parts[i:]).lstrip('/')

		clean_parts = [p for p in parts if p]
		if len(clean_parts) >= 2:
			return '/'.join(clean_parts[-2:])
		return clean_parts[-1] if clean_parts else normalized

	def _make_github_link(self, file_path: str, line: int, column: int) -> str:
		if not self._github_info:
			return f'{file_path}:{line}:{column}'

		clean_path = file_path.replace('\\', '/').lstrip('/')
		base = self._github_info['repo_url']
		ref = self._github_info['ref']

		if ref:
			return f'{base}/blob/{ref}/{clean_path}#L{line}'
		return f'{base}/pull/files'

	def _format_message(self, msg: Message, display_path: str) -> str:
		github_link = self._make_github_link(display_path, msg.line, msg.column)

		first_line = '[Pylint]'
		second_line = f'{display_path}:{msg.line}: {msg.msg_id}: {msg.msg}'
		third_line = f'{github_link}'

		lines = [first_line, second_line, third_line]

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
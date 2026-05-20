import re
from pathlib import Path
from typing import List, Optional

from .message import Message
from ..logger import warning

TMP_PREFIX = re.compile(r'^/tmp/tmp[^/]+/')


class PullRequestReportGenerator:
	def __init__(
		self,
		pr,
		show_code_snippet: bool = True,
		snippet_context_lines: int = 2
	):
		self.pr = pr
		self.show_code_snippet = show_code_snippet
		self.snippet_context_lines = snippet_context_lines

	def generate(self, messages: List[Message]) -> str:
		if not messages:
			return 'No issues found.\n'

		messages_by_file = self._group_by_file(messages)
		lines = []

		for file_path, file_messages in messages_by_file.items():
			display_path = self._get_repo_relative_path(file_path).lstrip('/')

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

	def _get_repo_relative_path(self, file_path: str) -> str:
		if not self.pr or not self.pr.files_dir:
			return Path(file_path).name
		try:
			return Path(file_path).relative_to(self.pr.files_dir).as_posix()
		except ValueError:
			return Path(file_path).name

	def _detect_hosting(self, repo_url: str) -> str:
		return 'github' if 'github.com' in repo_url else 'forgejo'

	def _make_link(self, msg: Message) -> str:
		if not self.pr:
			return f'{file_path}:{line}:{column}'

		file_path, line, column = msg.abspath, msg.line, msg.column
		commit_sha = getattr(msg, 'specified_commit', None)

		base = self.pr.repo_url.rstrip('/')

		if commit_sha:
			return f'{base}/commit/{commit_sha}'

		clean_path = self._get_repo_relative_path(file_path).lstrip('/')

		if clean_path:
			hosting = self._detect_hosting(base)
			ref = self.pr.merge_commit_sha
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


class ReportGenerator:
	def __init__(self, show_code_snippet: bool = True, snippet_context_lines: int = 2):
		self.show_code_snippet = show_code_snippet
		self.snippet_context_lines = snippet_context_lines

	def generate(self, results: list[tuple]) -> None:
		groups: dict = {}
		for pr, messages in results:
			groups.setdefault(pr.repo_url, []).append((pr, messages))

		def repo_sort_key(url: str) -> str:
			parts = url.rstrip('/').split('/')
			return '/'.join(parts[-2:]).lower()

		first = True
		for repo_url in sorted(groups.keys(), key=repo_sort_key):
			for pr, messages in sorted(groups[repo_url], key=lambda x: x[0].number):
				if not first:
					print('\n====================================\n')
				first = False

				author_display = pr.author_username
				if pr.author_name:
					author_display = f'{pr.author_username} ({pr.author_name})'
				date_str = pr.created_at.strftime('%Y.%m.%d') if pr.created_at else 'N/A'
				print('\nRepository: ', pr.repo_url)
				print('PR: ', pr.pr_url)
				print('Author: ', author_display)
				print('Date: ', date_str)

				if not pr.files:
					warning(f'Warning: No suitable files found in PR {pr.pr_url}')
					continue

				pr_generator = PullRequestReportGenerator(
					pr,
					show_code_snippet=self.show_code_snippet,
					snippet_context_lines=self.snippet_context_lines,
				)
				print(pr_generator.generate(messages))
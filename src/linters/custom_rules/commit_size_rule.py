import json
import urllib.error
import urllib.request
from typing import Any, List
from urllib.parse import urlparse

from pylint.message import Message
from pylint.typing import MessageLocationTuple
from pylint.interfaces import UNDEFINED

from .base import PRRule

class CommitSizeRule(PRRule):
	def __init__(self, threshold: int):
		self.threshold = threshold

	def check(self, context: dict[str, Any]) -> List[Message]:
		pr = context.get('pr')
		if not pr:
			return []

		messages: List[Message] = []

		try:
			parsed = urlparse(pr.repo_url.rstrip('/'))
			path_parts = [p for p in parsed.path.split('/') if p]
			if len(path_parts) < 2:
				return []
			owner, repo_name = path_parts[-2], path_parts[-1]
		except Exception:
			return []

		if pr.hosting == 'github':
			g = context.get('github_client')
			if not g:
				return []

			try:
				repo = g.get_repo(f'{owner}/{repo_name}')
			except Exception as e:
				print(f'[CustomRules] GitHub repo error: {e}')
				return []

			if not pr.commits:
				return []

			for sha in pr.commits:
				try:
					commit = repo.get_commit(sha)
					stats = commit.stats
					total_lines = (
						(stats.total if stats else 0) or
						((stats.additions or 0) + (stats.deletions or 0))
						if stats else 0
					)

					if total_lines > self.threshold:
						message = self._make_message(
							symbol='large_commit_size',
							msg=f'Коммит {sha[:8]}: {total_lines} строк (лимит: {self.threshold})',
							priority=2,
							location=MessageLocationTuple(
								abspath='.', path='.', module=f'COMMIT {sha[:8]}',
								obj='', line=1, column=1, end_line=None, end_column=None,
							)
						)
						message.specified_commit = sha
						messages.append(message)
				except Exception as e:
					print(f'[CustomRules] GitHub commit {sha} error: {e}')

		elif pr.hosting == 'forgejo':
			pr_index = getattr(pr, 'index', None) or getattr(pr, 'number', None)
			if pr_index is None:
				return []

			api_base = f'{parsed.scheme}://{parsed.netloc}/api/v1'
			token = context.get('forgejo_token')

			url = f'{api_base}/repos/{owner}/{repo_name}/pulls/{pr_index}/commits'
			req = urllib.request.Request(url)
			req.add_header('Accept', 'application/json')
			if token:
				req.add_header('Authorization', f'token {token}')

			try:
				with urllib.request.urlopen(req, timeout=10) as resp:
					commits = json.loads(resp.read().decode('utf-8'))
			except urllib.error.HTTPError as e:
				print(f'[CustomRules] Forgejo PR commits error: {e}')
				return []
			except Exception as e:
				print(f'[CustomRules] Forgejo PR commits parse error: {e}')
				return []

			for commit_info in commits:
				sha = commit_info.get('sha') or commit_info.get('id')
				if not sha:
					continue

				try:
					stats = commit_info.get('stats', {})
					total_lines = stats.get('total') or (
						stats.get('additions', 0) + stats.get('deletions', 0)
					)

					if total_lines > self.threshold:
						message = self._make_message(
							symbol='large_commit_size',
							msg=f'Коммит {sha[:8]}: {total_lines} строк (лимит: {self.threshold})',
							priority=2,
							location=MessageLocationTuple(
								abspath='.', path='.', module=f'COMMIT {sha[:8]}',
								obj='', line=1, column=1, end_line=None, end_column=None,
							)
						)
						message.specified_commit = sha
						messages.append(message)
				except Exception as e:
					print(f'[CustomRules] Forgejo commit {sha} error: {e}')

		return messages

	def _make_message(self, symbol: str, msg: str,
		location: MessageLocationTuple | None = None,
		priority: int = 3) -> Message:
		if location is None:
			location = MessageLocationTuple(
				abspath='.', path='.', module='CUSTOM_RULES',
				obj='', line=1, column=1, end_line=None, end_column=None,
			)

		msg_id = self._msg_id_for_priority(priority)

		message = Message(
			msg_id=msg_id,
			symbol=symbol,
			location=location,
			msg=msg,
			confidence=UNDEFINED,
		)
		message.linter = 'CustomRules'
		return message

	def _msg_id_for_priority(self, priority: int) -> str:
		if priority == 1:
			return 'ERROR'
		if priority == 2:
			return 'WARNING'
		return 'REFACTOR'
import os
import tempfile
import atexit
import shutil
from github import Github, GithubException

from ...config import SUPPORTED_EXTENSIONS
from ...logger import info, warning
from ..pull_request import PullRequest
from ..utils import safe_str


def _cleanup_dir(path: str) -> None:
	if path and os.path.exists(path):
		shutil.rmtree(path, ignore_errors=True)


def get_pull_request(client: Github, pr_url: str) -> PullRequest:
	tmpdir = tempfile.mkdtemp(prefix=f'pr_{hash(pr_url)}_')
	atexit.register(_cleanup_dir, tmpdir)
	path = pr_url.replace('https://github.com', '').strip('/')
	parts = path.split('/')
	try:
		owner, repo_name = parts[0], parts[1]
		pr_number = int(parts[parts.index('pull') + 1])
	except (IndexError, ValueError):
		_cleanup_dir(tmpdir)
		raise ValueError(f'Невалидная GitHub PR ссылка: {pr_url}')
	repo = client.get_repo(f'{owner}/{repo_name}')
	pr = repo.get_pull(pr_number)
	labels = [label.name for label in pr.get_labels()]
	commits = [commit.sha for commit in pr.get_commits()]
	user_id = safe_str(
		getattr(pr.user, 'name', None) or getattr(pr.user, 'login', None)
	)
	info(f'PR #{pr_number} найден: "{pr.title}" от {user_id} ({pr.created_at})')
	pr_obj = PullRequest(
		body=safe_str(pr.body),
		changed_files=pr.changed_files or 0,
		closed_at=pr.closed_at,
		created_at=pr.created_at,
		draft=getattr(pr, 'draft', False),
		repo_url=repo.html_url,
		pr_url=pr.html_url,
		labels=labels,
		merge_commit_sha=pr.merge_commit_sha,
		merged=pr.merged,
		merged_at=pr.merged_at,
		number=pr.number,
		state=pr.state,
		title=pr.title,
		updated_at=pr.updated_at,
		commits=commits,
		hosting='github',
		org_id=owner,
		repo_id=repo_name,
		user_id=user_id,
		files_dir=tmpdir,
		files=[],
	)

	for file in pr.get_files():
		if file.status == 'removed':
			continue
		if not any(file.filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
			continue
		try:
			content_file = repo.get_contents(file.filename, ref=pr.head.sha)
			if isinstance(content_file, list):
				continue
			content = content_file.decoded_content
			local_path = os.path.join(tmpdir, file.filename)
			os.makedirs(os.path.dirname(local_path), exist_ok=True)
			with open(local_path, 'wb') as f:
				f.write(content)
			pr_obj.files.append(local_path)
		except GithubException as e:
			warning(f'Не удалось скачать {file.filename}: {e}')
			continue
	labels_str = ', '.join(labels) if labels else 'нет'
	info(f'Изменения: +{pr.additions}/-{pr.deletions} строк, {pr.changed_files} файлов, теги: [{labels_str}]')

	info(f'Загружены файлы: {", ".join(os.path.basename(f) for f in pr_obj.files)}')
	return pr_obj
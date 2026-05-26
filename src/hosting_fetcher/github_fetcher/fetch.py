import os
import subprocess
import tempfile
import atexit
import shutil
from typing import Optional
from github import Github

from ...config import SUPPORTED_EXTENSIONS
from ...logger import info
from ..pull_request import PullRequest
from ..utils import safe_str


def _cleanup_dir(path: str) -> None:
	if path and os.path.exists(path):
		shutil.rmtree(path, ignore_errors=True)


def get_pull_request(client: Github, pr_url: str, token: Optional[str] = None) -> PullRequest:
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
	user_login = safe_str(getattr(pr.user, 'login', None))
	user_name = safe_str(getattr(pr.user, 'name', None))
	info(f'Найден PR #{pr_number} в репозитории {owner}/{repo_name}')

	head_repo = pr.head.repo
	if head_repo:
		clone_url = head_repo.clone_url
	else:
		clone_url = repo.clone_url
	branch = pr.head.ref

	if token:
		clone_url = clone_url.replace('https://', f'https://oauth2:{token}@')

	if not shutil.which('git'):
		_cleanup_dir(tmpdir)
		raise RuntimeError('git не найден. Установите git.')

	info(f'Клонирование ветки {branch} ({clone_url})...')
	result = subprocess.run(
		['git', 'clone', '--single-branch', '--branch', branch, '--depth', '1', clone_url, tmpdir],
		capture_output=True, text=True, timeout=120
	)
	if result.returncode != 0:
		_cleanup_dir(tmpdir)
		raise RuntimeError(f'Не удалось клонировать репозиторий: {result.stderr.strip()}')

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
		author_username=user_login,
		author_name=user_name,
		files_dir=tmpdir,
		files=[],
	)

	for file in pr.get_files():
		if file.status == 'removed':
			continue
		if not any(file.filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
			continue
		local_path = os.path.join(tmpdir, file.filename)
		if os.path.exists(local_path):
			pr_obj.files.append(local_path)

	if pr_obj.files:
		info(f'Загружены файлы: {", ".join(os.path.basename(f) for f in pr_obj.files)}')
	return pr_obj

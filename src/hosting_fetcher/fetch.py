import subprocess
import tempfile
import atexit
import shutil
from pathlib import Path
from urllib.parse import urlparse

from ..logger import info
from .utils import detect_hosting
from .pull_request import PullRequest
from . import github_fetcher
from . import forgejo_fetcher


_repo_cache: dict[str, Path] = {}


def _repo_key(hosting: str, org_id: str, repo_id: str) -> str:
	return f'{hosting}:{org_id}/{repo_id}'


def get_repo_dir(hosting: str, org_id: str, repo_id: str) -> Path:
	key = _repo_key(hosting, org_id, repo_id)
	if key in _repo_cache:
		return _repo_cache[key]
	repo_dir = Path(tempfile.mkdtemp(prefix=f'repo_{org_id}_{repo_id}_'))
	_repo_cache[key] = repo_dir
	return repo_dir


def _cleanup_all():
	for d in _repo_cache.values():
		shutil.rmtree(d, ignore_errors=True)


atexit.register(_cleanup_all)


def git_auth_url(pr_url: str, token: str | None) -> str:
	parsed = urlparse(pr_url)
	path_parts = parsed.path.strip('/').split('/')
	owner, repo_name = path_parts[0], path_parts[1]
	if token:
		return f'{parsed.scheme}://{token}@{parsed.netloc}/{owner}/{repo_name}'
	return f'{parsed.scheme}://{parsed.netloc}/{owner}/{repo_name}'


def shallow_clone_or_fetch(repo_dir: Path, auth_url: str, branch: str):
	git_dir = repo_dir / '.git'
	if git_dir.exists():
		info(f'Фетчинг ветки {branch} в репозиторий {repo_dir.name}')
		subprocess.run(
			['git', '-C', str(repo_dir), 'fetch', '--depth', '1', 'origin', branch],
			check=True, capture_output=True
		)
	else:
		info(f'Клонирование репозитория (ветка {branch}) в {repo_dir.name}')
		subprocess.run(
			['git', 'clone', '--depth', '1', '--no-single-branch', '--branch', branch, auth_url, str(repo_dir)],
			check=True, capture_output=True
		)


def switch_branch(repo_dir: Path, branch: str):
	subprocess.run(
		['git', '-C', str(repo_dir), 'switch', branch],
		check=True, capture_output=True
	)


def get_pull_request(client, pr_url, token=None) -> PullRequest:
	hosting = detect_hosting(pr_url)
	if hosting == 'github':
		return github_fetcher.get_pull_request(client, pr_url, token)
	else:
		return forgejo_fetcher.get_pull_request(client, pr_url, token)
import os
import tempfile
import atexit
import shutil
from urllib.parse import urlparse

from ...config import SUPPORTED_EXTENSIONS
from ..pull_request import PullRequest
from ..utils import safe_str
from ..utils import parse_datetime


def _cleanup_dir(path: str) -> None:
	if path and os.path.exists(path):
		shutil.rmtree(path, ignore_errors=True)


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
	parsed = urlparse(pr_url)
	path = parsed.path.strip('/')
	parts = path.split('/')
	if len(parts) < 3:
		raise ValueError(f'URL слишком короткий: {pr_url}')
	owner = parts[0]
	repo_name = parts[1]
	pr_number = None
	for i, part in enumerate(parts):
		if part in ['pulls', 'pull'] and i + 1 < len(parts):
			try:
				pr_number = int(parts[i + 1])
				break
			except ValueError:
				continue
	if pr_number is None:
		raise ValueError(f'Не найдена секция pulls/pull в URL: {pr_url}')
	return owner, repo_name, pr_number


def get_pull_request(client, pr_url: str) -> PullRequest:
	tmpdir = tempfile.mkdtemp(prefix=f'pr_{hash(pr_url)}_')
	atexit.register(_cleanup_dir, tmpdir)
	owner, repo_name, pr_number = parse_pr_url(pr_url)
	url = f'{client.base_url}/api/v1/repos/{owner}/{repo_name}/pulls/{pr_number}'
	response = client.get(url)
	response.raise_for_status()
	pr_data = response.json()
	commits_url = f'{client.base_url}/api/v1/repos/{owner}/{repo_name}/pulls/{pr_number}/commits'
	commits_response = client.get(commits_url)
	commits_response.raise_for_status()
	commits_list = commits_response.json()
	commit_shas = [c['sha'] for c in commits_list if 'sha' in c]
	files_url = f'{client.base_url}/api/v1/repos/{owner}/{repo_name}/pulls/{pr_number}/files'
	files_response = client.get(files_url)
	files_response.raise_for_status()
	files = files_response.json()
	changed_files = len(files)
	labels = [
		label.get('name', '')
		for label in pr_data.get('labels', [])
		if label.get('name')
	]
	user = pr_data.get('user', {}) or {}
	user_id = safe_str(
		user.get('login_name') or user.get('login') or user.get('username')
	)
	pr_obj = PullRequest(
		body=safe_str(pr_data.get('body')),
		changed_files=changed_files,
		closed_at=parse_datetime(pr_data.get('closed_at')),
		created_at=parse_datetime(pr_data['created_at']),
		draft=bool(pr_data.get('draft', False)),
		repo_url=f'{client.base_url}/{owner}/{repo_name}',
		pr_url=safe_str(pr_data.get('html_url'), default=pr_url),
		labels=labels,
		merge_commit_sha=pr_data['head'].get('sha'),
		merged=bool(pr_data.get('merged', False)),
		merged_at=parse_datetime(pr_data.get('merged_at')),
		number=pr_number,
		state=safe_str(pr_data.get('state', 'open')),
		title=safe_str(pr_data.get('title'), default=f'PR #{pr_number}'),
		updated_at=parse_datetime(pr_data['updated_at']),
		commits=commit_shas,
		hosting='forgejo',
		org_id=owner,
		repo_id=repo_name,
		user_id=user_id,
		files_dir=tmpdir,
		files=[],
	)

	head_sha = pr_data['head'].get('sha')
	for file_info in files:
		filename = file_info['filename']
		if not any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
			continue
		try:
			raw_url = f'{client.base_url}/api/v1/repos/{owner}/{repo_name}/raw/{filename}'
			params = {'ref': head_sha} if head_sha else {}
			file_response = client.get(raw_url, params=params)
			if file_response.status_code == 200:
				local_path = os.path.join(tmpdir, filename)
				os.makedirs(os.path.dirname(local_path), exist_ok=True)
				with open(local_path, 'wb') as f:
					f.write(file_response.content)
				pr_obj.files.append(local_path)
		except Exception as e:
			print(f'Не удалось скачать {filename}: {e}')
			continue

	return pr_obj
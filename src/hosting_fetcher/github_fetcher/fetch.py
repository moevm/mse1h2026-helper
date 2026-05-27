from ...config import SUPPORTED_EXTENSIONS
from ...logger import info, warning
from ..pull_request import PullRequest
from ..utils import safe_str


def get_pull_request(client, pr_url: str, token: str | None = None) -> PullRequest:
	from ..fetch import get_repo_dir, git_auth_url, shallow_clone_or_fetch, switch_branch

	path = pr_url.replace('https://github.com', '').strip('/')
	parts = path.split('/')
	try:
		owner, repo_name = parts[0], parts[1]
		pr_number = int(parts[parts.index('pull') + 1])
	except (IndexError, ValueError):
		raise ValueError(f'Невалидная GitHub PR ссылка: {pr_url}')
	repo = client.get_repo(f'{owner}/{repo_name}')
	pr = repo.get_pull(pr_number)

	branch_name = pr.head.ref

	repo_dir = get_repo_dir('github', owner, repo_name)
	auth_url = git_auth_url(pr_url, token)
	shallow_clone_or_fetch(repo_dir, auth_url, branch_name)
	switch_branch(repo_dir, branch_name)

	labels = [label.name for label in pr.get_labels()]
	commits = [commit.sha for commit in pr.get_commits()]
	user_login = safe_str(getattr(pr.user, 'login', None))
	user_name = safe_str(getattr(pr.user, 'name', None))
	info(f'Найден PR #{pr_number} в репозитории {owner}/{repo_name}')
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
		repo_dir=repo_dir,
		branch_name=branch_name,
		files=[],
	)

	for file in pr.get_files():
		if file.status == 'removed':
			continue
		if not any(file.filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
			continue
		local_path = repo_dir / file.filename
		if local_path.exists():
			pr_obj.files.append(local_path)
		else:
			warning(f'Файл {file.filename} не найден в локальном репозитории')

	if pr_obj.files:
		info(f'Найдены файлы: {", ".join(str(f.relative_to(repo_dir)) for f in pr_obj.files)}')
	return pr_obj
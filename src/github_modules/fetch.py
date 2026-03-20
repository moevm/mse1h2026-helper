import os
from github import Github, PullRequest

from ..config import SUPPORTED_EXTENSIONS


def get_pull_request_metadata(g: Github, pr_url: str) -> PullRequest:
	path = pr_url.replace('https://github.com', '').strip('/')
	parts = path.split('/')
	try:
		owner, repo_name = parts[0], parts[1]
		pr_index = parts.index('pull') + 1
		pr_number = int(parts[pr_index])
	except (IndexError, ValueError):
		raise ValueError(f"Invalid GitHub PR URL: {pr_url}")
	repo = g.get_repo(f"{owner}/{repo_name}")
	return repo.get_pull(pr_number)


def download_pull_request_files(pr: PullRequest, local_dir: str):
	repo = pr.base.repo
	branch_sha = pr.head.sha
	downloaded_paths = []
	contents = repo.get_contents('', ref=branch_sha)
	while contents:
		file_content = contents.pop()
		if file_content.type == 'dir':
			contents.extend(repo.get_contents(file_content.path, ref=branch_sha))
		else:
			if any(file_content.path.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
				local_path = os.path.join(local_dir, file_content.path)
				os.makedirs(os.path.dirname(local_path), exist_ok=True)
				with open(local_path, 'wb') as f:
					f.write(file_content.decoded_content)
				downloaded_paths.append(local_path)
	return downloaded_paths
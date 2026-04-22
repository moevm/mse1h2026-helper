import os
from typing import List
from github import Github, GithubException

from ...config import SUPPORTED_EXTENSIONS
from ..pull_request import PullRequest
from ..utils import safe_str


def get_pull_request_metadata(g: Github, pr_url: str) -> PullRequest:
    path = pr_url.replace('https://github.com', '').strip('/')
    parts = path.split('/')
    try:
        owner, repo_name = parts[0], parts[1]
        pr_number = int(parts[parts.index('pull') + 1])
    except (IndexError, ValueError):
        raise ValueError(f'Invalid GitHub PR URL: {pr_url}')
    repo = g.get_repo(f'{owner}/{repo_name}')
    pr = repo.get_pull(pr_number)
    labels = [label.name for label in pr.get_labels()]
    commits = [commit.sha for commit in pr.get_commits()]
    user_id = safe_str(
        getattr(pr.user, 'name', None) or getattr(pr.user, 'login', None)
    )
    return PullRequest(
        body=safe_str(pr.body),
        changed_files=pr.changed_files or 0,
        closed_at=pr.closed_at,
        created_at=pr.created_at,
        draft=getattr(pr, 'draft', False),
        html_url=pr.html_url,
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
    )


def download_pull_request_files(
    client: Github,
    pr_metadata: PullRequest,
    local_dir: str
) -> List[str]:
    repo = client.get_repo(f"{pr_metadata.org_id}/{pr_metadata.repo_id}")
    pr = repo.get_pull(pr_metadata.number)
    downloaded_paths = []
    for file in pr.get_files():
        if file.status == "removed":
            continue
        if not any(file.filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            continue
        try:
            content_file = repo.get_contents(file.filename, ref=pr.head.sha)
            if isinstance(content_file, list):
                continue
            content = content_file.decoded_content
            local_path = os.path.join(local_dir, file.filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)
            downloaded_paths.append(local_path)
        except GithubException as e:
            print(f"Не удалось скачать {file.filename}: {e}")
            continue
    return downloaded_paths
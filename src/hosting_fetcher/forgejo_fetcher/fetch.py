import os
from typing import List
from urllib.parse import urlparse

from ...config import SUPPORTED_EXTENSIONS
from ..pull_request import PullRequest
from ..utils import safe_str
from ..utils import parse_datetime
from pyforgejo import PyforgejoApi


def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    parsed = urlparse(pr_url)
    path = parsed.path.strip('/')
    parts = path.split('/')
    if len(parts) < 3:
        raise ValueError(f"URL слишком короткий: {pr_url}")
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
        raise ValueError(f"Не найдена секция pulls/pull в URL: {pr_url}")
    return owner, repo_name, pr_number


def get_pull_request_metadata(client: PyforgejoApi, pr_url: str) -> PullRequest:
    owner, repo_name, pr_number = parse_pr_url(pr_url)
    pr_data = client.repository.repo_get_pull_request(
        owner=owner,
        repo=repo_name,
        index=pr_number,
    )
    commits = client.repository.repo_get_pull_request_commits(
        owner=owner,
        repo=repo_name,
        index=pr_number,
    )
    commit_shas = [c.sha for c in commits]
    labels = [
        label.name
        for label in (pr_data.labels or [])
        if getattr(label, "name", None)
    ]
    user = pr_data.user
    user_id = safe_str(
        getattr(user, "login_name", None)
        or getattr(user, "login", None)
    )
    return PullRequest(
        body=safe_str(pr_data.body),
        changed_files=getattr(pr_data, "changed_files", 0),
        closed_at=parse_datetime(pr_data.closed_at),
        created_at=parse_datetime(pr_data.created_at),
        draft=bool(pr_data.draft),
        html_url=safe_str(pr_data.html_url, default=pr_url),
        labels=labels,
        merge_commit_sha=pr_data.merge_commit_sha,
        merged=bool(pr_data.merged),
        merged_at=parse_datetime(pr_data.merged_at),
        number=pr_number,
        state=safe_str(pr_data.state, default="open"),
        title=safe_str(pr_data.title, default=f"PR #{pr_number}"),
        updated_at=parse_datetime(pr_data.updated_at),
        commits=commit_shas,
        hosting="forgejo",
        org_id=owner,
        repo_id=repo_name,
        user_id=user_id,
    )


def download_pull_request_files(client: PyforgejoApi, pr_metadata: PullRequest, local_dir: str) -> List[str]:
    owner = pr_metadata.org_id
    repo = pr_metadata.repo_id
    pr_number = pr_metadata.number
    pr_data = client.repository.repo_get_pull_request(
        owner=owner,
        repo=repo,
        index=pr_number,
    )
    ref = pr_data.head.ref
    commits = client.repository.repo_get_pull_request_commits(
        owner=owner,
        repo=repo,
        index=pr_number,
        files=True,
    )
    files_info = {}
    for commit in commits:
        for f in getattr(commit, "files", []) or []:
            filename = getattr(f, "filename", None)
            if not filename:
                continue

            files_info[filename] = {
                "status": getattr(f, "status", None),
                "previous": getattr(f, "previous_filename", None),
            }
    downloaded = []
    for filename, meta in files_info.items():
        if not any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            continue
        if meta["status"] == "removed":
            continue
        try:
            content = client.repository.repo_get_raw_file(
                owner=owner,
                repo=repo,
                filepath=filename,
                ref=ref,
            )
            if content is None:
                continue
            if isinstance(content, str):
                data = content.encode("utf-8")
            elif isinstance(content, bytes):
                data = content
            elif hasattr(content, "__iter__"):
                data = b"".join(
                    chunk.encode() if isinstance(chunk, str) else chunk
                    for chunk in content
                )
            else:
                raise TypeError(f"Неподдерживаемый тип: {type(content)}")
            local_path = os.path.join(local_dir, filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data)

            downloaded.append(local_path)
        except Exception:
            continue
    return downloaded
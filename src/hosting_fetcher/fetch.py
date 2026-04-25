from typing import List

from .utils import detect_hosting
from .pull_request import PullRequest
from . import github_fetcher
from . import forgejo_fetcher

def get_pull_request_metadata(client, pr_url: str) -> PullRequest:
    hosting = detect_hosting(pr_url)
    if hosting == 'github':
        return github_fetcher.get_pull_request_metadata(client, pr_url)
    else:
        return forgejo_fetcher.get_pull_request_metadata(client, pr_url)


def download_pull_request_files(client, pr_metadata, local_dir: str) -> List[str]:
    if pr_metadata.hosting == 'github':
        return github_fetcher.download_pull_request_files(client, pr_metadata, local_dir)
    else:
        return forgejo_fetcher.download_pull_request_files(client, pr_metadata, local_dir)
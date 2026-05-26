from typing import Optional
from .utils import detect_hosting
from .pull_request import PullRequest
from . import github_fetcher
from . import forgejo_fetcher

def get_pull_request(client, pr_url: str, token: Optional[str] = None) -> PullRequest:
	hosting = detect_hosting(pr_url)
	if hosting == 'github':
		return github_fetcher.get_pull_request(client, pr_url, token)
	else:
		return forgejo_fetcher.get_pull_request(client, pr_url, token)
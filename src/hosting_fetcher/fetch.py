from .utils import detect_hosting
from .pull_request import PullRequest
from . import github_fetcher
from . import forgejo_fetcher

def get_pull_request(client, pr_url) -> PullRequest:
	hosting = detect_hosting(pr_url)
	if hosting == 'github':
		return github_fetcher.get_pull_request(client, pr_url)
	else:
		return forgejo_fetcher.get_pull_request(client, pr_url)
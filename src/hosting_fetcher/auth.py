import requests
from typing import Union
from github import Github

from .utils import detect_hosting
from . import github_fetcher
from . import forgejo_fetcher


def login(token: str, pr_url: str) -> Union[Github, requests.Session]:
    hosting = detect_hosting(pr_url)
    if hosting == 'github':
        return github_fetcher.login(token)
    else:
        return forgejo_fetcher.login(pr_url, token)
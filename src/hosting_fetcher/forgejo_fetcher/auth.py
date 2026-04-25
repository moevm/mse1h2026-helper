import requests
from typing import Optional
from urllib.parse import urlparse


def login(pr_url: str, token: Optional[str] = None):
    parsed = urlparse(pr_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    session = requests.Session()
    session.headers.update({'Accept': 'application/json'})
    if token:
        session.headers.update({'Authorization': f'token {token}'})
    session.base_url = base_url
    return session
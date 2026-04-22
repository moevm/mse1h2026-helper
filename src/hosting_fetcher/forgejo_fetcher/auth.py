import requests
from typing import Optional


def login(base_url: str, token: Optional[str] = None):
    session = requests.Session()
    session.headers.update({'Accept': 'application/json'})
    if token:
        session.headers.update({'Authorization': f'token {token}'})
    session.base_url = base_url.rstrip('/')
    return session
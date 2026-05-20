import requests
from typing import Optional
from urllib.parse import urlparse

from ...logger import info


_cached_sessions = {}


def login(pr_url: str, token: Optional[str] = None) -> requests.Session:
	global _cached_sessions
	parsed = urlparse(pr_url)
	base_url = f'{parsed.scheme}://{parsed.netloc}'
	if base_url in _cached_sessions:
		return _cached_sessions[base_url]
	session = requests.Session()
	session.headers.update({'Accept': 'application/json'})
	if token:
		session.headers.update({'Authorization': f'token {token}'})
	session.base_url = base_url
	_cached_sessions[base_url] = session
	info(f'Авторизация на Forgejo ({base_url}) выполнена')
	return session
import requests
from typing import Optional
from urllib.parse import urlparse

from ...logger import info


_cached_session: requests.Session | None = None
_cached_base_url: str | None = None


def login(pr_url: str, token: Optional[str] = None) -> requests.Session:
	global _cached_session, _cached_base_url
	parsed = urlparse(pr_url)
	base_url = f'{parsed.scheme}://{parsed.netloc}'
	if _cached_session is not None and _cached_base_url == base_url:
		return _cached_session
	session = requests.Session()
	session.headers.update({'Accept': 'application/json'})
	if token:
		session.headers.update({'Authorization': f'token {token}'})
	session.base_url = base_url
	_cached_session = session
	_cached_base_url = base_url
	info(f'Авторизация на Forgejo ({base_url}) выполнена')
	return session
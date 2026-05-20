from github import Auth, Github

from ...logger import info


_cached_client: Github | None = None


def login(token: str) -> Github:
	global _cached_client
	if _cached_client is None:
		auth = None if token is None else Auth.Token(token)
		_cached_client = Github(auth=auth, retry=None)
		info('Авторизация на GitHub выполнена')
	return _cached_client
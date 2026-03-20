from github import Auth, Github


def login(token: str) -> Github:
	auth = None if token is None else Auth.Token(token)
	g = Github(auth=auth, retry=None)
	return g
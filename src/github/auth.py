from github import Github, Auth


def login(token: str) -> Github:
	auth = Auth.Token(token)
	g = Github(auth=auth)
	return g
import argparse
import os
import subprocess
import sys
import tempfile
from abc import ABC, abstractmethod
from .github import login, load_pr, fetch_pull_request


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str):
		pass


class PylintWrapper(Linter):
	def run(self, file_path: str):
		process = subprocess.run(
			['pylint', '--score=n', '--disable=bad-indentation,missing-final-newline', file_path],
			capture_output=True,
			text=True,
			check=False
		)
		if process.returncode == 1:
			print('Pylint analysis finished with Fatal error (return code 1)')
		if process.stderr:
			print(f'Pylint analysis finished with non-empty error output:\n{process.stderr}')
		return process.stdout


class LinterFactory:
	_linters = {'.py': PylintWrapper()}

	@classmethod
	def get_linter(cls, file_path: str) -> Linter:
		_, ext = os.path.splitext(file_path)
		linter = cls._linters.get(ext)
		if not linter:
			raise ValueError(f'No linter for file {ext}')
		return linter


def main():
	parser = argparse.ArgumentParser(usage="python main.py [OPTIONS] PULL_REQUEST_URL", description="Helper for linting Pull Requests")
	parser.add_argument('--token', help='Токен GitHub')
	parser.add_argument('--severity', choices=['error', 'warning', 'note'], help='Минимальная серьёзность проблемы для вывода')
	parser.add_argument('--pylint', help='Параметры для линтера Pylint')
	parser.add_argument('--oclint', help='Параметры для линтера OCLint')
	parser.add_argument('pr_url', metavar='PULL_REQUEST_URL', help='Ссылка на PR')
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(1)
	args = parser.parse_args()
	try:
		g = login(token=args.token)
		pr = fetch_pull_request(g, args.pr_url)
		with tempfile.TemporaryDirectory() as tmpdir:
			all_files = load_pr(pr, tmpdir)
			if not all_files:
				raise Exception('В PR нет подходящих для анализа файлов .')
			for file_path in all_files:
				linter = LinterFactory.get_linter(file_path)
				result = linter.run(file_path)
				print(result)
	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
	main()
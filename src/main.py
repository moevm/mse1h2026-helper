import argparse
import os
import sys
import tempfile
from abc import ABC, abstractmethod
from io import StringIO
from pylint.lint import pylinter, Run
from pylint.reporters.text import TextReporter

from .github_module import login, get_pull_request_metadata, download_pull_request_files


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str):
		pass


class PylintWrapper(Linter):
	def run(self, file_path: str):
		pylinter.MANAGER.clear_cache()
		pylint_output = StringIO()
		reporter = TextReporter(pylint_output)
		try:
			runner = Run(
				[file_path, '--score=n', '--disable=bad-indentation,missing-final-newline'],
				reporter=reporter,
				exit=False
			)
		except Exception as e:
			return f'Pylint API Error: {str(e)}'
		return pylint_output.getvalue()


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
	parser = argparse.ArgumentParser(usage='python main.py [OPTIONS] PULL_REQUEST_URL', description='Helper for linting Pull Requests')
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
		if args.severity or args.pylint or args.oclint:
			raise NotImplementedError('Функциональность ещё не реализована')
		g = login(args.token)
		pr = get_pull_request_metadata(g, args.pr_url)
		with tempfile.TemporaryDirectory() as tmpdir:
			all_files = download_pull_request_files(pr, tmpdir)
			if not all_files:
				raise Exception('В PR нет подходящих для анализа файлов')
			for file_path in all_files:
				linter = LinterFactory.get_linter(file_path)
				result = linter.run(file_path)
				print(result)
	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
	main()
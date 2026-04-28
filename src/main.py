import argparse
import sys
import shlex
import tempfile

from .hosting_fetcher import login, get_pull_request_metadata, download_pull_request_files
from .linters import LinterFactory
from .reports import ReportGenerator
from .linters import options as linter_options


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
		if args.severity or args.oclint:
			raise NotImplementedError('Функциональность ещё не реализована')
		if args.pylint:
			linter_options.pylint_options = []
			for opt in shlex.split(args.pylint):
				if opt:
					linter_options.pylint_options.append(opt)
		client = login(args.token, args.pr_url)
		pr = get_pull_request_metadata(client, args.pr_url)
		with tempfile.TemporaryDirectory() as tmpdir:
			all_files = download_pull_request_files(client, pr, tmpdir)
			if not all_files:
				raise Exception('В PR нет подходящих для анализа файлов')
			for file_path in all_files:
				linter = LinterFactory.get_linter(file_path)
				messages = linter.run(file_path)
				generator = ReportGenerator(
					show_code_snippet = True,
					snippet_context_lines = 2,
					github_ref=pr.merge_commit_sha,
					github_repo_url=pr.html_url
				)
				if file_path.endswith('.py'):
					report = generator.generate(messages)
					print(report)
				else:
					print(messages)

	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
    main()
import argparse
import re
import sys
import shlex
import tempfile

from .hosting_fetcher import login, get_pull_request_metadata, download_pull_request_files
from .linters import LinterFactory
from .reports import ReportGenerator
from .linters import options as linter_options

GITHUB_PR_URL_REGEX = re.compile(r'^https?://github\.com/[^/]+/[^/]+/pull/\d+/?$')
FORGEJO_PR_URL_REGEX = re.compile(r'^https?://[^/]+/[^/]+/[^/]+/pulls?/\d+/?$')
PR_RANGE_REGEX = re.compile(r'^(\d+)-(\d+)$')

def is_valid_pr_url(url: str) -> bool:
	return bool(GITHUB_PR_URL_REGEX.match(url) or FORGEJO_PR_URL_REGEX.match(url))

def parse_pr_range(range_str):
	match = PR_RANGE_REGEX.match(range_str)
	if not match:
		raise ValueError(f'Invalid PR range format: {range_str}')
	start, end = int(match.group(1)), int(match.group(2))
	if start > end:
		raise ValueError(f'Invalid PR range: start ({start}) > end ({end})')
	return list(range(start, end + 1))

def parse_pr_list(list_str):
	try:
		return [int(num.strip()) for num in list_str.split(',')]
	except ValueError:
		raise ValueError(f'Invalid PR list format: {list_str}')

def collect_pr_urls(args):
	pr_urls = []
	pr_urls.extend(args.pr_urls)
	if args.repo:
		repo_url = args.repo.rstrip('/')
		pr_numbers = set()
		if args.pr_range:
			pr_numbers.update(parse_pr_range(args.pr_range))
		if args.pr_include:
			pr_numbers.update(parse_pr_list(args.pr_include))
		if args.pr_exclude:
			excluded = set(parse_pr_list(args.pr_exclude))
			pr_numbers -= excluded
		for pr_num in sorted(pr_numbers):
			pr_urls.append(f'{repo_url}/pull/{pr_num}')
	return pr_urls

def process_pull_request(g, pr_url):
	pr = get_pull_request_metadata(g, pr_url)
	with tempfile.TemporaryDirectory() as tmpdir:
		print("PR: ", pr_url)
		with tempfile.TemporaryDirectory() as tmpdir:
			all_files = download_pull_request_files(g, pr, tmpdir)
			if not all_files:
				print(f'Warning: No suitable files found in PR {pr_url}')
				return
			for file_path in all_files:
				linter = LinterFactory.get_linter(file_path)
				messages = linter.run(file_path)
				generator = ReportGenerator(
					show_code_snippet=True,
					snippet_context_lines=2,
					hosting_ref=pr.merge_commit_sha,
					hosting_repo_url=pr.repo_url
			)
			report = generator.generate(messages)
			print(report)

def main():
	parser = argparse.ArgumentParser(
		usage='python main.py [OPTIONS] [PULL_REQUEST_URL ...]',
		description='Helper for linting Pull Requests'
	)
	parser.add_argument('--token', help='Токен GitHub или Forgejo')
	parser.add_argument('--severity', choices=['error', 'warning', 'note'], help='Минимальная серьёзность проблемы для вывода')
	parser.add_argument('--pylint', help='Параметры для линтера Pylint')
	parser.add_argument('--oclint', help='Параметры для линтера OCLint')
	parser.add_argument('--repo', help='URL репозитория для анализа PR по номерам')
	parser.add_argument('--pr-range', help='Диапазон номеров PR (например, 1-6)')
	parser.add_argument('--pr-include', help='Список номеров PR для включения (например, 6,42)')
	parser.add_argument('--pr-exclude', help='Список номеров PR для исключения (например, 6,42)')
	if len(sys.argv) == 1:
		parser.print_help()
		sys.exit(1)
	args, remaining = parser.parse_known_args()
	args.pr_urls = remaining
	invalid = [url for url in args.pr_urls if not is_valid_pr_url(url)]
	if invalid:
		raise ValueError(f'Invalid PR URL(s): {", ".join(invalid)}')
	del invalid
	try:
		if args.severity or args.oclint:
			raise NotImplementedError('Функциональность ещё не реализована')
		if (args.pr_range or args.pr_include or args.pr_exclude) and not args.repo:
			raise ValueError('Флаги --pr-range, --pr-include, --pr-exclude требуют указания --repo')
		pr_urls = collect_pr_urls(args)
		if not pr_urls:
			raise ValueError('Не указаны PR для анализа')
		for pr_url in pr_urls:
			g = login(args.token, pr_url)
			process_pull_request(g, pr_url)
	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
	main()
import argparse
import re
import shlex
import sys
from datetime import datetime

from .linters.custom_runner import CustomRulesWrapper
from .linters import LinterFactory
from .linters import options as linter_options
from .hosting_fetcher import login, get_pull_request
from .reports import ReportGenerator

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


def check_pr_against_filters(pr, args) -> str | None:
	if args.pr_filter_name and args.pr_filter_name not in pr.title:
		return f'заголовок не содержит подстроку "{args.pr_filter_name}"'
	if args.pr_filter_date_from:
		if pr.created_at.date() < args.pr_filter_date_from:
			return f'создан раньше {args.pr_filter_date_from}'
	if args.pr_filter_date_to:
		if pr.created_at.date() > args.pr_filter_date_to:
			return f'создан позже {args.pr_filter_date_to}'
	if args.pr_filter_labels:
		required_labels = {label.strip() for label in args.pr_filter_labels.split(',') if label.strip()}
		pr_labels = set(pr.labels or [])
		if not required_labels.issubset(pr_labels):
			return f'нет ни одной из указанных меток: {args.pr_filter_labels}'
	return None


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


def process_pull_request(g, token, pr) -> list | None:
	if not pr.files:
		return None

	all_messages = []

	context = {'pr': pr}
	if pr.hosting == 'github':
		context['github_client'] = g
	elif pr.hosting == 'forgejo':
		context['forgejo_token'] = token

	custom_linter = CustomRulesWrapper(context=context)

	for file_path in pr.files:
		linter = LinterFactory.get_linter(file_path)
		all_messages.extend(linter.run(file_path))
		all_messages.extend(custom_linter.run(file_path=file_path))

	all_messages.extend(custom_linter.run(file_path=''))
	return all_messages


def main():
	def parse_date(value):
		try:
			return datetime.strptime(value, r'%Y.%m.%d').date()
		except ValueError:
			raise argparse.ArgumentTypeError('Дата должна быть в формате YYYY.MM.DD')
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
	parser.add_argument('--pr-filter-name', help='Фильтр по имени PR (должно содержать подстроку)')
	parser.add_argument('--pr-filter-date-from', help='Фильтр по дате: от (формат: YYYY.MM.DD)', type=parse_date)
	parser.add_argument('--pr-filter-date-to', help='Фильтр по дате: до (формат: YYYY.MM.DD)', type=parse_date)
	parser.add_argument('--pr-filter-labels', help='Фильтр по меткам (PR должен иметь все указанные метки)')
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
		if args.pylint:
			linter_options.pylint_options = []
			for opt in shlex.split(args.pylint):
				if opt:
					linter_options.pylint_options.append(opt)
		pr_urls = collect_pr_urls(args)
		if not pr_urls:
			raise ValueError('Не указаны PR для анализа')
		results = []
		for pr_url in pr_urls:
			g = login(args.token, pr_url)
			pr = get_pull_request(g, pr_url)

			skip_reason = check_pr_against_filters(pr, args)
			if skip_reason:
				print(f'Пропуск PR {pr_url}: {skip_reason}')
				continue
			
			results.append((pr, process_pull_request(g, args.token, pr)))

		ReportGenerator().generate(results)

	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
	main()
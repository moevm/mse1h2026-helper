from typing import List, Optional

from pylint.lint import pylinter, Run
from pylint.reporters import CollectingReporter

from .base import Linter

DEFAULT_OPTIONS = ['--score=n', '--disable=bad-indentation,missing-final-newline']


class PylintWrapper(Linter):
	def run(self, file_path: str, options: Optional[List[str]] = None):
		pylinter.MANAGER.clear_cache()
		reporter = CollectingReporter()
		try:
			Run([file_path] + (options or DEFAULT_OPTIONS), reporter=reporter, exit=False)
		except Exception as e:
			return f'Pylint API Error: {str(e)}'
		return reporter.messages
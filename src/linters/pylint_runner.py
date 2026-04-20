from pylint.lint import pylinter, Run
from pylint.reporters import CollectingReporter

from .base import Linter

from typing import List, Optional

DEFAULT_OPTIONS = ['--score=n', '--disable=bad-indentation,missing-final-newline']


class PylintWrapper(Linter):
	def run(self, file_path: str, options: Optional[List[str]] = None):
		pylinter.MANAGER.clear_cache()
		reporter = CollectingReporter()
		if options is not None:
			pylint_options = options
		else:
			pylint_options = DEFAULT_OPTIONS
		try:
			Run([file_path] + pylint_options, reporter=reporter, exit=False)
		except Exception as e:
			return f'Pylint API Error: {str(e)}'
		return reporter.messages
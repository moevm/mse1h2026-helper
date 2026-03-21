from pylint.lint import pylinter, Run
from pylint.reporters import CollectingReporter

from .base import Linter


class PylintWrapper(Linter):
	def run(self, file_path: str):
		pylinter.MANAGER.clear_cache()
		reporter = CollectingReporter()
		try:
			Run([file_path, '--score=n', '--disable=bad-indentation,missing-final-newline'], reporter=reporter, exit=False)
		except Exception as e:
			return f'Pylint API Error: {str(e)}'
		return reporter.messages
from typing import List

from pylint.lint import pylinter, Run
from pylint.reporters import CollectingReporter

from .base import Linter
from . import options
from ..reports.message import Message, MessageLocation

DEFAULT_OPTIONS = ['--score=n', '--disable=bad-indentation,missing-final-newline']


class PylintWrapper(Linter):
	def run(self, file_path: str):
		pylinter.MANAGER.clear_cache()
		reporter = CollectingReporter()
		try:
			Run([str(file_path)] + (options.pylint_options or DEFAULT_OPTIONS), reporter=reporter, exit=False)
		except Exception:
			return []
		custom_messages: List[Message] = []
		for message in reporter.messages:
			location = MessageLocation(
				abspath=message.abspath,
				path=message.path,
				module=message.module,
				obj=message.obj,
				line=message.line,
				column=message.column,
				end_line=getattr(message, 'end_line', None),
				end_column=getattr(message, 'end_column', None),
			)
			custom_messages.append(Message(
				msg_id=message.msg_id,
				symbol=message.symbol,
				location=location,
				msg=message.msg,
				confidence=message.confidence.name if message.confidence else None,
				linter='Pylint',
			))
		return custom_messages
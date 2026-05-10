from pylint.message import Message
from typing import Any, List

from .base import Linter
from .custom_rules import RuleFactory

class CustomRulesWrapper(Linter):
	def __init__(self, context: dict[str, Any] | None = None):
		self.context = context or {}
		self._pr_rules_executed = False

	def run(self, file_path: str = '') -> List[Message]:
		messages: List[Message] = []

		if file_path:
			rule_context = self.context.copy()
			rule_context['file_path'] = file_path

			for rule in RuleFactory.get_file_rules():
				messages.extend(rule.check(rule_context))

		if not file_path and not self._pr_rules_executed:
			pr_context = self.context.copy()

			for rule in RuleFactory.get_pr_rules():
				messages.extend(rule.check(pr_context))

			self._pr_rules_executed = True

		return messages
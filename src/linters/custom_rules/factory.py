from typing import List

from .base import FileRule, PRRule
from .commit_size_rule import CommitSizeRule
from .nested_loops_rule import NestedLoopsRule
from .goto_rule import GotoRule
from .require_rule import RequireRule


class RuleFactory:
	_file_rules: List[FileRule] = [
		NestedLoopsRule(max_depth=3),
		GotoRule(),
	]

	_pr_rules: List[PRRule] = [
		CommitSizeRule(threshold=10000),
	]

	@classmethod
	def get_file_rules(cls) -> List[FileRule]:
		return cls._file_rules

	@classmethod
	def get_pr_rules(cls) -> List[PRRule]:
		return cls._pr_rules

	@classmethod
	def register_file_rule(cls, rule: FileRule) -> None:
		cls._file_rules.append(rule)

	@classmethod
	def register_pr_rule(cls, rule: PRRule) -> None:
		cls._pr_rules.append(rule)

	@classmethod
	def get_all_rules(cls) -> List:
		return cls._file_rules + cls._pr_rules

	@classmethod
	def configure_rule(cls, rule_name: str, params: str) -> None:
		if rule_name == 'require':
			functions = [f.strip() for f in params.split(',') if f.strip()]
			if functions:
				cls._pr_rules = [
					r for r in cls._pr_rules
					if not isinstance(r, RequireRule)
				]
				cls._pr_rules.append(RequireRule(required_functions=functions))
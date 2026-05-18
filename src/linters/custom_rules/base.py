from abc import ABC, abstractmethod
from typing import List, Any

from pylint.message import Message


class CustomRule(ABC):
	@abstractmethod
	def check(self, context: dict[str, Any]) -> List[Message]:
		pass


class FileRule(CustomRule):
	@abstractmethod
	def check(self, context: dict[str, Any]) -> List[Message]:
		pass


class PRRule(CustomRule):
	@abstractmethod
	def check(self, context: dict[str, Any]) -> List[Message]:
		pass
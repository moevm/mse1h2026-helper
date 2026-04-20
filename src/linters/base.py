from abc import ABC, abstractmethod
from typing import List, Optional


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str, options: Optional[List[str]] = None):
		pass
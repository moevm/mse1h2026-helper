from abc import ABC, abstractmethod


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str):
		pass
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import Tuple


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str) -> Tuple[str | None, str | None, int]:
		pass


class PylintWrapper(Linter):
	def run(self, file_path: str):
		process = subprocess.run(
			['pylint', '--score=n', '--disable=bad-indentation,missing-final-newline', file_path],
			capture_output=True,
			text=True,
			check=False
		)
		if process.returncode == 1:
			if process.stderr is not None and process.stderr != '':
				raise RuntimeError(f'Pylint analyse finished with Fatal error: {process.stderr}')
			else:
				raise RuntimeError(f'Pylint analyse finished with Fatal error')
		return process.stdout, process.stderr, process.returncode


class LinterFactory:
	_linters = {'.py': PylintWrapper()}

	@classmethod
	def get_linter(cls, file_path: str) -> Linter:
		_, ext = os.path.splitext(file_path)
		linter = cls._linters.get(ext)
		if not linter:
			raise ValueError(f'No linter for file {ext}')
		return linter


def main():
	if len(sys.argv) < 2:
		print(f'Usage: {sys.argv[0]} <file_path>')
		sys.exit(1)

	file_to_check = sys.argv[1]
	try:
		linter_instance = LinterFactory.get_linter(file_to_check)
		result, stderr, return_code = linter_instance.run(file_to_check)
		if stderr is not None and stderr != '':
			print(f'Linter anasyse finished with error message: {stderr}')
		if result is not None:
			print(result)
		print(f'Returned code: {return_code}')
	except RuntimeError as e:
		print(f'Critical error: {e}')
		sys.exit(1)
	except Exception as e:
		print(f'Error: {e}')


if __name__ == '__main__':
	main()
import os
import sys
from io import StringIO
from abc import ABC, abstractmethod
from pylint.lint import pylinter
from pylint.lint import Run
from pylint.reporters.text import TextReporter


class Linter(ABC):
	@abstractmethod
	def run(self, file_path: str):
		pass


class PylintWrapper(Linter):
	def run(self, file_path: str):
		pylinter.MANAGER.clear_cache()
        pylint_output = StringIO()
		reporter = TextReporter(pylint_output)
	
		try:
            Run(
                [file_path, '--score=n', '--disable=bad-indentation,missing-final-newline'], 
                reporter=reporter,
                exit=False 
            )
        except Exception as e:
            return f"Pylint API Error: {str(e)}"
        
        return pylint_output.getvalue()


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
		result = linter_instance.run(file_to_check)
		print(result)
	except Exception as e:
		print(f'Error: {e}')
		sys.exit(1)


if __name__ == '__main__':
	main()
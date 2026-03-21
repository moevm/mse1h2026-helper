from .base import Linter
from .pylint_runner import PylintWrapper


class LinterFactory:
	_linters = {'.py': PylintWrapper()}

	@classmethod
	def get_linter(cls, file_path: str) -> Linter:
		import os
		_, ext = os.path.splitext(file_path)
		linter = cls._linters.get(ext)
		if not linter:
			raise ValueError(f'No linter for file {ext}')
		return linter
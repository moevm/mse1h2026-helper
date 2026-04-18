from .base import Linter
from .pylint_runner import PylintWrapper
from .oclint_runner import OCLintWrapper
from ..config import SUPPORTED_EXTENSIONS


class LinterFactory:
	_linters = {
		'.py': PylintWrapper(),
		**{ext: OCLintWrapper() for ext in SUPPORTED_EXTENSIONS if ext != '.py'}
	}

	@classmethod
	def get_linter(cls, file_path: str) -> Linter:
		import os
		_, ext = os.path.splitext(file_path)
		linter = cls._linters.get(ext)
		if not linter:
			raise ValueError(f'No linter for file {ext}')
		return linter
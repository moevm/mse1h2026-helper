from .base import Linter
from .pylint_runner import PylintWrapper
from .oclint_runner import OCLintWrapper
from ..config import PYTHON_EXTENSIONS, C_CPP_EXTENSIONS


class LinterFactory:
	_linters = {
		**{ext: PylintWrapper() for ext in PYTHON_EXTENSIONS},
		**{ext: OCLintWrapper() for ext in C_CPP_EXTENSIONS}
	}

	@classmethod
	def get_linter(cls, file_path: str) -> Linter:
		import os
		_, ext = os.path.splitext(file_path)
		linter = cls._linters.get(ext)
		if not linter:
			raise ValueError(f'No linter for file {ext}')
		return linter
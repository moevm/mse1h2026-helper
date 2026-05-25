import ast
from pathlib import Path
from typing import Optional, TypeAlias

import clang.cindex

from ...config import PYTHON_EXTENSIONS, C_CPP_EXTENSIONS

AST: TypeAlias = ast.AST | clang.cindex.TranslationUnit


class ASTCache:
	_instance = None
	_cache: dict[str, AST] = {}

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def get(self, file_path: str) -> Optional[AST]:
		return self._cache.get(file_path)

	def set(self, file_path: str, tree: AST) -> None:
		self._cache[file_path] = tree

	def parse_file(self, file_path: str) -> Optional[AST]:
		cached = self.get(file_path)
		if cached is not None:
			return cached

		ext = Path(file_path).suffix.lower()

		try:
			if ext in PYTHON_EXTENSIONS:
				with open(file_path, 'r', encoding='utf-8') as f:
					content = f.read()
				tree = ast.parse(content, filename=file_path)

			elif ext in C_CPP_EXTENSIONS:
				index = clang.cindex.Index.create()
				tree = index.parse(file_path)

			else:
				print(f'[ASTCache] Unsupported file type: {file_path}')
				return None

			self.set(file_path, tree)
			return tree

		except (SyntaxError, OSError, UnicodeDecodeError) as e:
			print(f'[ASTCache] Failed to parse Python file {file_path}: {e}')
			return None

		except Exception as e:
			print(f'[ASTCache] Failed to parse C/C++ file {file_path}: {e}')
			return None

	def clear(self) -> None:
		self._cache.clear()
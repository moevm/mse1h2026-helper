import ast
from typing import Optional

class ASTCache:
	_instance = None
	_cache: dict[str, ast.AST] = {}

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def get(self, file_path: str) -> Optional[ast.AST]:
		return self._cache.get(file_path)

	def set(self, file_path: str, tree: ast.AST) -> None:
		self._cache[file_path] = tree

	def parse_file(self, file_path: str) -> Optional[ast.AST]:
		cached = self.get(file_path)
		if cached is not None:
			return cached

		try:
			with open(file_path, 'r', encoding='utf-8') as f:
				content = f.read()
			tree = ast.parse(content, filename=file_path)
			self.set(file_path, tree)
			return tree
		except (SyntaxError, OSError, UnicodeDecodeError) as e:
			print(f'[ASTCache] Failed to parse {file_path}: {e}')
			return None

	def clear(self) -> None:
		self._cache.clear()
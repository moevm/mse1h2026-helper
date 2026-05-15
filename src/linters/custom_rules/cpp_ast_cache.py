import clang.cindex
from typing import Optional, Any

class CppASTCache:
	_instance = None
	_cache: dict[str, Any] = {}

	def __new__(cls):
		if cls._instance is None:
			cls._instance = super().__new__(cls)
		return cls._instance

	def get(self, file_path: str) -> Optional[Any]:
		return self._cache.get(file_path)

	def set(self, file_path: str, tree: Any) -> None:
		self._cache[file_path] = tree

	def parse_file(self, file_path: str) -> Optional[Any]:
		cached = self.get(file_path)
		if cached is not None:
			return cached

		try:
			index = clang.cindex.Index.create()
			tree = index.parse(file_path)
			self.set(file_path, tree)
			return tree
		except Exception as e:
			print(f'[CppASTCache] Failed to parse {file_path}: {e}')
			return None

	def clear(self) -> None:
		self._cache.clear()
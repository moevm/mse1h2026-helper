import ast
from pathlib import PurePath
from pylint.message import Message
from pylint.typing import MessageLocationTuple
from pylint.interfaces import UNDEFINED
from typing import List, Any

from .base import FileRule
from .ast_cache import ASTCache
from ...config import PYTHON_EXTENSIONS

class NestedLoopsRule(FileRule):
	def __init__(self, max_depth: int):
		self.max_depth = max_depth
		self.ast_cache = ASTCache()

	def check(self, context: dict[str, Any]) -> List[Message]:
		file_path = context.get('file_path', '')
		if not file_path:
			return []

		if PurePath(file_path).suffix not in PYTHON_EXTENSIONS:
			return []

		tree = self.ast_cache.parse_file(file_path)
		if tree is None:
			return []

		messages = []
		visitor = LoopDepthVisitor(self.max_depth)
		visitor.visit(tree)

		for violation in visitor.violations:
			msg = self._make_message(
				file_path=file_path,
				line=violation['line'],
				column=violation['column'],
				depth=violation['depth']
			)
			messages.append(msg)

		return messages

	def _make_message(self, file_path: str, line: int, column: int, depth: int) -> Message:
		location = MessageLocationTuple(
			abspath=file_path,
			path=file_path,
			module='',
			obj='',
			line=line,
			column=column,
			end_line=None,
			end_column=None,
		)

		message = Message(
			msg_id='REFACTOR',
			symbol='nested_loops_too_deep',
			location=location,
			msg=f'Вложенность циклов {depth} превышает максимум {self.max_depth}',
			confidence=UNDEFINED,
		)
		message.linter = 'CustomRules'
		return message

class LoopDepthVisitor(ast.NodeVisitor):
	def __init__(self, max_depth: int):
		self.max_depth = max_depth
		self.current_depth = 0
		self.violations = []

	def visit_For(self, node: ast.For):
		self._check_loop(node)
		self.generic_visit(node)
		self.current_depth -= 1

	def visit_While(self, node: ast.While):
		self._check_loop(node)
		self.generic_visit(node)
		self.current_depth -= 1

	def _check_loop(self, node):
		self.current_depth += 1
		if self.current_depth > self.max_depth:
			self.violations.append({
				'line': node.lineno,
				'column': node.col_offset,
				'depth': self.current_depth
			})
import ast
import clang.cindex
from pathlib import PurePath
from typing import List, Any, Set

from pylint.interfaces import UNDEFINED

from .base import PRRule
from .ast_cache import ASTCache
from ...config import PYTHON_EXTENSIONS, CPP_EXTENSIONS
from ...reports.message import Message, MessageLocation


class RequireRule(PRRule):
	def __init__(self, required_functions: list[str]):
		self.required_functions = required_functions
		self.ast_cache = ASTCache()

	def check(self, context: dict[str, Any]) -> List[Message]:
		pr = context.get('pr')
		if not pr or not pr.files:
			return []

		all_found: Set[str] = set()

		for file_path in pr.files:
			ext = PurePath(file_path).suffix
			if ext in CPP_EXTENSIONS:
				tree = self.ast_cache.parse_file(file_path)
				if tree is None:
					continue

				visitor = CppFunctionCallVisitor()
				visitor.visit(tree.cursor)

			elif ext in PYTHON_EXTENSIONS:
				tree = self.ast_cache.parse_file(file_path)
				if tree is None:
					continue

				visitor = PythonFunctionCallVisitor()
				visitor.visit(tree)

			else:
				continue

			all_found.update(visitor.function_calls)

		messages = []
		pr_label = f'PR #{pr.number}'
		for func_name in self.required_functions:
			if func_name not in all_found:
				msg = self._make_message(
					pr_label=pr_label,
					func_name=func_name
				)
				messages.append(msg)

		return messages

	def _make_message(self, pr_label: str, func_name: str) -> Message:
		location = MessageLocation(
			abspath='.',
			path='.',
			module=pr_label,
			obj='',
			line=1,
			column=1,
			end_line=None,
			end_column=None,
		)

		message = Message(
			msg_id='WARNING',
			symbol='required_function_missing',
			location=location,
			msg=f'В PR не найдены вызовы требуемой функции {func_name}',
			confidence=UNDEFINED,
			linter='CustomRules'
		)
		return message


class CppFunctionCallVisitor:
	def __init__(self):
		self.function_calls: Set[str] = set()

	def visit(self, cursor):
		if cursor.kind == clang.cindex.CursorKind.CALL_EXPR:
			try:
				name = cursor.spelling
				if name:
					self.function_calls.add(name)
			except Exception:
				pass

		for child in cursor.get_children():
			self.visit(child)


class PythonFunctionCallVisitor(ast.NodeVisitor):
	def __init__(self):
		self.function_calls: Set[str] = set()

	def visit_Call(self, node: ast.Call):
		if isinstance(node.func, ast.Name):
			self.function_calls.add(node.func.id)
		elif isinstance(node.func, ast.Attribute):
			self.function_calls.add(node.func.attr)
		self.generic_visit(node)
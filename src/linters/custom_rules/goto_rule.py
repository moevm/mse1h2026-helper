import clang.cindex
from pathlib import PurePath
from pylint.message import Message
from pylint.typing import MessageLocationTuple
from pylint.interfaces import UNDEFINED
from typing import List, Any

from .base import FileRule
from .ast_cache import ASTCache
from ...config import CPP_EXTENSIONS


class GotoRule(FileRule):
	def __init__(self):
		self.ast_cache = ASTCache()

	def check(self, context: dict[str, Any]) -> List[Message]:
		file_path = context.get('file_path', '')
		if not file_path:
			return []

		if PurePath(file_path).suffix not in CPP_EXTENSIONS:
			return []

		tree = self.ast_cache.parse_file(file_path)
		if tree is None:
			return []

		messages = []
		visitor = GotoVisitor()
		visitor.visit(tree.cursor)

		for location in visitor.goto_locations:
			msg = self._make_message(
				file_path=file_path,
				line=location['line'],
				column=location['column']
			)
			messages.append(msg)

		return messages

	def _make_message(self, file_path: str, line: int, column: int) -> Message:
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
			symbol='goto_usage',
			location=location,
			msg=f'Найден оператор goto',
			confidence=UNDEFINED,
		)
		message.linter = 'CustomRules'
		return message

class GotoVisitor:
    def __init__(self):
        self.goto_locations: List[dict] = []
    
    def visit(self, cursor):
        if cursor.kind == clang.cindex.CursorKind.GOTO_STMT:
            self.goto_locations.append({
                'line': cursor.location.line,
                'column': cursor.location.column,
            })
        
        for child in cursor.get_children():
            self.visit(child)
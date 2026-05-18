from dataclasses import dataclass
from typing import Optional


@dataclass
class MessageLocation:
	abspath: str
	path: str
	module: str
	obj: str = ""
	line: int = 1
	column: int = 1
	end_line: Optional[int] = None
	end_column: Optional[int] = None

@dataclass
class Message:
	msg: str
	symbol: str
	location: MessageLocation
	msg_id: Optional[str] = None
	confidence: Optional[str] = None
	linter: Optional[str] = None
	priority: Optional[int] = None
	specified_commit: Optional[str] = None

	@property
	def abspath(self) -> str:
		return self.location.abspath if self.location else ""

	@property
	def path(self) -> str:
		return self.location.path if self.location else ""

	@property
	def module(self) -> str:
		return self.location.module if self.location else ""

	@property
	def line(self) -> int:
		return self.location.line if self.location else 1

	@property
	def column(self) -> int:
		return self.location.column if self.location else 1

	@property
	def end_line(self) -> Optional[int]:
		return self.location.end_line if self.location else None

	@property
	def end_column(self) -> Optional[int]:
		return self.location.end_column if self.location else None
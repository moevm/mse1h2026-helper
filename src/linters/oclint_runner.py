import json
import subprocess
from pathlib import PurePath

from pylint.interfaces import UNDEFINED

from .base import Linter
from ..reports.message import Message, MessageLocation


class OCLintWrapper(Linter):
	def _msg_id_for_priority(self, priority: int) -> str:
		# Pylint ожидает первую букву из своих типов: F/E/W/C/R/I
		# Для OCLint удобно транслировать так:
		if priority == 1:
			return 'ERROR'
		if priority == 2:
			return 'WARNING'
		return 'REFACTOR'

	def run(self, file_path: str):
		result = subprocess.run(
			[
				'oclint',
				'-report-type', 'json',
				file_path,
				'--',
				'-std=c++17',
				'-Wall',
				'-Wextra',
				'-pedantic',
			],
			capture_output=True,
			text=True,
		)

		if result.returncode not in (0, 1):
			raise RuntimeError(
				f'OCLint failed with code {result.returncode}:\n'
				f'stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}'
			)

		raw = result.stdout.strip()
		if not raw:
			raise RuntimeError(
				f'OCLint returned empty stdout.\n'
				f'stderr:\n{result.stderr}'
			)

		try:
			data = json.loads(raw)
		except json.JSONDecodeError as e:
			raise RuntimeError(
				f'Failed to parse OCLint JSON: {e}\n'
				f'raw stdout:\n{raw}\n\nstderr:\n{result.stderr}'
			)

		violations = data.get('violation', [])

		messages = []

		for v in violations:
			path = v.get('path', file_path)
			start_line = int(v.get('startLine', 0) or 0)
			start_col = int(v.get('startColumn', 0) or 0)
			end_line = v.get('endLine')
			end_col = v.get('endColumn')

			priority = int(v.get('priority', 3) or 3)
			msg_id = self._msg_id_for_priority(priority)
			symbol = str(v.get('rule', '')).replace(' ', '_')
			msg_text = str(v.get('message') or v.get('rule') or '')

			location = MessageLocation(
				abspath=path,
				path=path,
				module=PurePath(path).stem,
				obj='',
				line=start_line,
				column=start_col,
				end_line=end_line,
				end_column=end_col,
			)

			message = Message(
				msg_id=msg_id,
				symbol=symbol,
				location=location,
				msg=msg_text,
				confidence=UNDEFINED,
				linter='OCLint'
			)
			messages.append(message)

		return messages
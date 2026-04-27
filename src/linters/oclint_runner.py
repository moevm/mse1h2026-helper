import subprocess
import json

from .base import Linter


class OCLintWrapper(Linter):
	def run(self, file_path: str):
		try:
			result = subprocess.run(
				['oclint', '-report-type', 'text', file_path, '--', '-std=c++17', '-Wall'],
				capture_output=True,
				text=True
			)
			if result.stderr:
				return result.stderr + '\n\n' + result.stdout
			return result.stdout
		except Exception as e:
			return f'OCLint error: {str(e)}'
import subprocess
import json

from .base import Linter


class OCLintWrapper(Linter):
	def run(self, file_path: str):
		try:
			result = subprocess.run(
				['oclint','-report-type', 'json', file_path, '--', '-std=c++17', '-Wall'],
				capture_output=True,
				text=True
			)
			if result.stdout:
				try:
					violations = json.loads(result.stdout)
					return violations
				except json.JSONDecodeError as e:
					print(f"JSON decode error: {e}")
					return result.stdout
			elif result.stderr:
				return result.stderr
			return []
		except Exception as e:
			return f"OCLint error: {str(e)}"
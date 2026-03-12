import subprocess
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
main_file = project_root / 'src' / 'main.py'

def test_run_without_arguments():
	"""Тест 1: Запуск без аргументов должен завершиться с ошибкой"""
	cmd = [sys.executable, str(main_file)]
	result = subprocess.run(
		cmd,
		cwd=project_root,
		capture_output=True,
		text=True,
		timeout=10
	)
	assert result.returncode == 1
	assert 'Usage:' in result.stdout

def test_run_with_arguments():
	"""Тест 2: Проверяем, что программа принимает аргументы"""
	cmd = [sys.executable, str(main_file), str(main_file)]
	result = subprocess.run(
		cmd,
		cwd=project_root,
		capture_output=True,
		text=True,
		timeout=10
	)
	assert 'Usage:' not in result.stdout
	if result.returncode != 0:
		assert 'Error:' in (result.stdout + result.stderr)
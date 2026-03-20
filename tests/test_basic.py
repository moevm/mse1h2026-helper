import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
main_file = project_root / 'src' / 'main.py'
main_package = 'src.main'


def test_run_without_arguments():
	"""Тест 1: Запуск без аргументов должен завершиться с ошибкой и показать справку"""
	cmd = [sys.executable, '-m', main_package]
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'usage:' in result.stdout


def test_help_flag():
	"""Тест 2: Флаг --help должен показать справку"""
	cmd = [sys.executable, '-m', main_package, '--help']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 0
	assert 'usage:' in result.stdout
import subprocess
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
main_file = project_root / 'src' / 'main.py'
main_package = 'src.main'


def test_run_without_arguments():
	"""Тест 1: Запуск без аргументов должен завершиться с ошибкой"""
	cmd = [sys.executable, '-m', main_package]
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'usage:' in result.stdout


def test_run_with_arguments():
	"""Тест 2: Проверяем, что программа принимает аргументы"""
	cmd = [sys.executable, '-m', main_package, str(main_file)]
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert 'Usage:' not in result.stdout
	if result.returncode != 0:
		assert 'Error:' in (result.stdout + result.stderr)


def test_unimplemented_flag_severity():
	"""Тест 3: Флаг --severity должен вызвать ошибку о нереализованной функциональности"""
	cmd = [sys.executable, '-m', main_package, '--severity', 'error', 'https://github.com/owner/repo/pull/1']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'Функциональность еще не реализована' in result.stdout


def test_unimplemented_flag_pylint():
	"""Тест 4: Флаг --pylint должен вызвать ошибку о нереализованной функциональности"""
	cmd = [sys.executable, '-m', main_package, '--pylint', 'test', 'https://github.com/owner/repo/pull/1']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'Функциональность еще не реализована' in result.stdout


def test_unimplemented_flag_oclint():
	"""Тест 5: Флаг --oclint должен вызвать ошибку о нереализованной функциональности"""
	cmd = [sys.executable, '-m', main_package, '--oclint', 'test', 'https://github.com/owner/repo/pull/1']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'Функциональность еще не реализована' in result.stdout


def test_invalid_pr_url():
	"""Тест 6: Неверный URL пул-реквеста должен вызвать ошибку"""
	cmd = [sys.executable, '-m', main_package, 'not-a-valid-url']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 1
	assert 'Error:' in (result.stdout + result.stderr)


def test_help_flag():
	"""Тест 7: Флаг --help должен показать справку"""
	cmd = [sys.executable, '-m', main_package, '--help']
	result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True, timeout=10)
	assert result.returncode == 0
	assert 'usage:' in result.stdout.lower()
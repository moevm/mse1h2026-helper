import pytest
from github import Auth, Github
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.github_modules import login, get_pull_request_metadata, download_pull_request_files


class TestLogin:
	def test_login_with_token(self):
		"""Тест: Аутентификация с токеном возвращает объект Github"""
		result = login('test_token_123')
		assert isinstance(result, Github)

	def test_login_without_token(self):
		"""Тест: Аутентификация без токена возвращает объект Github"""
		result = login(None)
		assert isinstance(result, Github)


class TestGetPullRequestMeta:
	def test_valid_url_standard_format(self):
		"""Тест: Корректный URL в стандартном формате извлекает владельца, репозиторий и номер PR"""
		mock_github = MagicMock(spec=Github)
		mock_repo = MagicMock()
		mock_pr = MagicMock()
		mock_github.get_repo.return_value = mock_repo
		mock_repo.get_pull.return_value = mock_pr
		url = 'https://github.com/owner/repo/pull/42'
		result = get_pull_request_metadata(mock_github, url)
		mock_github.get_repo.assert_called_once_with('owner/repo')
		mock_repo.get_pull.assert_called_once_with(42)
		assert result == mock_pr

	def test_valid_url_with_trailing_slash(self):
		"""Тест: URL с завершающим "/" корректно обрабатывается (обрезаются лишние символы)"""
		mock_github = MagicMock(spec=Github)
		mock_repo = MagicMock()
		mock_pr = MagicMock()
		mock_github.get_repo.return_value = mock_repo
		mock_repo.get_pull.return_value = mock_pr
		url = 'https://github.com/owner/repo/pull/42/'
		result = get_pull_request_metadata(mock_github, url)
		assert result == mock_pr

	def test_invalid_url_no_pull_segment(self):
		"""Тест: URL без сегмента 'pull' вызывает исключение (невалидный формат)"""
		mock_github = MagicMock(spec=Github)
		url = 'https://github.com/owner/repo'
		with pytest.raises(ValueError, match='Invalid GitHub PR URL'):
			get_pull_request_metadata(mock_github, url)

	def test_invalid_url_non_numeric_pr_number(self):
		"""Тест: URL с нечисловым номером пул-реквеста вызывает исключение"""
		mock_github = MagicMock(spec=Github)
		url = 'https://github.com/owner/repo/pull/abc'
		with pytest.raises(ValueError, match='Invalid GitHub PR URL'):
			get_pull_request_metadata(mock_github, url)

	def test_invalid_url_empty(self):
		"""Тест: Пустая строка в качестве URL вызывает исключение"""
		mock_github = MagicMock(spec=Github)
		url = ''
		with pytest.raises(ValueError, match='Invalid GitHub PR URL'):
			get_pull_request_metadata(mock_github, url)


class TestDownloadPullRequestFiles:
	def test_downloads_single_supported_file(self, tmp_path):
		"""Тест: Скачивается один файл с поддерживаемым расширением (.py)"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_file = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_file.type = 'file'
		mock_file.path = 'src/main.py'
		mock_file.decoded_content = b'print("hello")'
		mock_repo.get_contents.return_value = [mock_file]
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 1
		assert result[0].endswith('src/main.py')
		assert (tmp_path / 'src/main.py').exists()
		assert (tmp_path / 'src/main.py').read_bytes() == b'print("hello")'

	def test_downloads_nested_file_structure(self, tmp_path):
		"""Тест: Рекурсивно обрабатываются вложенные директории, файлы скачиваются с сохранением структуры"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_dir = MagicMock()
		mock_file = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_dir.type = 'dir'
		mock_dir.path = 'src/utils'
		mock_file.type = 'file'
		mock_file.path = 'src/utils/helper.py'
		mock_file.decoded_content = b'def help(): pass'
		mock_repo.get_contents.side_effect = [[mock_dir], [mock_file]]
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 1
		assert (tmp_path / 'src/utils/helper.py').exists()

	def test_skips_unsupported_extensions(self, tmp_path):
		"""Тест: Файлы с неподдерживаемыми расширениями (.md) пропускаются и не скачиваются"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_file = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_file.type = 'file'
		mock_file.path = 'README.md'
		mock_file.decoded_content = b'# Readme'
		mock_repo.get_contents.return_value = [mock_file]
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 0
		assert not (tmp_path / 'README.md').exists()

	def test_downloads_multiple_supported_files(self, tmp_path):
		"""Тест: Скачиваются несколько файлов с поддерживаемыми расширениями из одного запроса"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_file1 = MagicMock()
		mock_file2 = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_file1.type = 'file'
		mock_file1.path = 'main.py'
		mock_file1.decoded_content = b'print(1)'
		mock_file2.type = 'file'
		mock_file2.path = 'utils.py'
		mock_file2.decoded_content = b'print(2)'
		mock_repo.get_contents.return_value = [mock_file1, mock_file2]
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 2
		assert any('main.py' in p for p in result)
		assert any('utils.py' in p for p in result)

	def test_handles_empty_repo(self, tmp_path):
		"""Тест: Пустой репозиторий (нет файлов) корректно обрабатывается — возвращается пустой список"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_repo.get_contents.return_value = []
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 0

	def test_creates_directory_structure(self, tmp_path):
		"""Тест: При скачивании файла из вложенной директории структура папок создаётся автоматически"""
		mock_pr = MagicMock()
		mock_repo = MagicMock()
		mock_file = MagicMock()
		mock_pr.base.repo = mock_repo
		mock_pr.head.sha = 'abc123'
		mock_file.type = 'file'
		mock_file.path = 'a/b/c/deep.py'
		mock_file.decoded_content = b'x=1'
		mock_repo.get_contents.return_value = [mock_file]
		result = download_pull_request_files(mock_pr, str(tmp_path))
		assert len(result) == 1
		expected_path = tmp_path / 'a' / 'b' / 'c' / 'deep.py'
		assert expected_path.exists()
		assert expected_path.read_bytes() == b'x=1'
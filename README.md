# mse1h2026-helper

Помощник преподавателя на лабах: генератор отчётов о пулл-реквестах студентов.

## Установка и запуск

### Использование готового Docker-образа

1. Скачайте образ из Docker Hub:
```sh
docker pull pasabanov/mse1h2026-helper:latest
```

2. Запустите контейнер, передав ссылку на Pull Request:
```sh
docker run pasabanov/mse1h2026-helper PULL_REQUEST_URL
```

---

### Сборка Docker-образа локально

1. Клонируйте репозиторий и перейдите в директорию проекта:
```sh
git clone https://github.com/moevm/mse1h2026-helper
cd mse1h2026-helper
```

2. Соберите Docker-образ из Dockerfile:
```sh
docker build -t mse1h2026-helper .
```

После сборки запустите контейнер, передав ссылку на Pull Request:
```sh
docker run mse1h2026-helper PULL_REQUEST_URL
```

---

## Проверка работоспособности

Для проверки работы приложения можно запустить контейнер с тестовой ссылкой на Pull Request:
```sh
docker run pasabanov/mse1h2026-helper https://github.com/moevm/mse1h2026-helper/pull/16
```

Или если образ был собран локально:
```sh
docker run mse1h2026-helper https://github.com/moevm/mse1h2026-helper/pull/16
```

Если приложение работает корректно, в консоли появится результат обработки указанного Pull Request.
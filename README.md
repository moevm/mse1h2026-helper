# mse1h2026-helper

Помощник преподавателя на лабах: генератор отчётов о пулл-реквестах студентов.

### Проверки

Файлы **Python** проверяются с помощью **Pylint**.

Файлы **C и C++** проверяются с помощью **OCLint**, а в случае неудачного анализа — с помощью **Clang**.

> [!NOTE]
> На Mac с процессорами Apple Silicon (M1, M2, M3 и др.) проверка OCLint не работает из-за несовместимости архитектурs ARM64/AArch64 с архитектурой AMD64.

Помимо линтеров, анализ проводится с использованием собственных правил:

- **CommitSizeRule** — проверяет, что количество изменённых строк в каждом коммите не превышает заданный порог (по умолчанию 10 000 строк).
- **RequireRule** — проверяет, что в файлах пулл-реквеста присутствуют вызовы указанных обязательных функций. 
- **GotoRule** — обнаруживает использование оператора `goto` в файлах C и C++.
- **NestedLoopsRule** — проверяет, что глубина вложенности циклов в файлах Python не превышает заданный максимум (по умолчанию 3).

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

---

## Предустановленные системные пакеты

### Стандартные C/C++ заголовки

| Заголовок | Пакет | Откуда требуется |
|-----------|-------|------------------|
| `<sys/types.h>`, `<stdint.h>` | build-essential | Стандартная библиотека C |
| `<string.h>`, `<stdlib.h>` | build-essential | Стандартная библиотека C |
| `<cstdint>`, `<string>`, `<vector>` | build-essential | Стандартная библиотека C++ |

### Сетевые заголовки (DPDK)

| Заголовок | Пакет | Назначение |
|-----------|-------|------------|
| `<rte_mbuf.h>` | libdpdk-dev | DPDK — работа с mbuf-пакетами |
| `<rte_ethdev.h>` | libdpdk-dev | DPDK — управление ethernet-портами |
| `<rte_ip.h>`, `<rte_udp.h>`, `<rte_tcp.h>` | libdpdk-dev | DPDK — протоколы L3/L4 |
| `<rte_hash.h>` | libdpdk-dev | DPDK — хеш-таблицы |
| `<rte_timer.h>` | libdpdk-dev | DPDK — таймеры |
| `<rte_eal.h>`, `<rte_ring.h>` | libdpdk-dev | DPDK — Environment Abstraction Layer |

DPDK-заголовки также зависят от:
- `<numa.h>` — libnuma-dev — NUMA-поддержка
- `<pcap.h>` — libpcap-dev — захват пакетов

### Криптография и работа с сетью

| Заголовок | Пакет | Назначение |
|-----------|-------|------------|
| `<openssl/ssl.h>` | libssl-dev | OpenSSL — транспортная защита |
| `<curl/curl.h>` | libcurl4-openssl-dev | libcurl — HTTP-запросы |
| `<bpf/libbpf.h>` | libbpf-dev | BPF — Berkeley Packet Filter |

### Protobuf

| Заголовок / Инструмент | Пакет | Назначение |
|------------------------|-------|------------|
| `<google/protobuf/...>` | libprotobuf-dev | Protobuf — сериализация данных |
| `protoc` | protobuf-compiler | Компилятор `.proto` → `.pb.h` |

### Prometheus

Заголовки Prometheus устанавливаются из исходного кода (версия v1.2.4), так как пакет `libprometheus-cpp-dev` отсутствует в репозиториях Ubuntu 22.04. Файлы `*_export.h` генерируются CMake в процессе сборки — в образе они созданы как заглушки с пустым макросом.

| Заголовок | Источник | Назначение |
|-----------|----------|------------|
| `<prometheus/gateway.h>` | Собран из исходников v1.2.4 | Prometheus Push Gateway — отправка метрик |
| `<prometheus/counter.h>`, `<prometheus/gauge.h>` | Собран из исходников v1.2.4 | Prometheus — типы метрик |
| `<prometheus/detail/core_export.h>` | Создан вручную (CMake-generated stub) | Макрос экспорта для shared library |
| `<prometheus/detail/push_export.h>` | Создан вручную (CMake-generated stub) | Макрос экспорта для push-компонента |
| `<prometheus/detail/pull_export.h>` | Создан вручную (CMake-generated stub) | Макрос экспорта для pull-компонента |

### Базы данных

| Заголовок | Пакет | Назначение |
|-----------|-------|------------|
| `<sqlite3.h>` | libsqlite3-dev | SQLite — работа с базами данных |
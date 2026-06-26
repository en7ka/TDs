# Data Discovery MCP

Небольшой сервис для поиска данных по локальным источникам. Поддерживаются два типа источников:

- SQLite база `sample_data/demo.db`
- CSV файлы из `sample_data/`

Сервис читает схемы таблиц и файлов, собирает колонки, типы и несколько примеров строк, строит простой keyword-индекс и отдает доступ к нему через CLI и MCP tools.

## Архитектура

Основные модули:

- `discovery/connectors/base.py` — общий интерфейс коннектора.
- `discovery/connectors/sqlite_connector.py` — чтение SQLite: список таблиц, `PRAGMA table_info`, sample rows.
- `discovery/connectors/csv_connector.py` — чтение CSV: заголовки, примерное определение типов, sample rows.
- `discovery/index/indexer.py` — преобразование схем в документы индекса.
- `discovery/index/store.py` — хранение индекса в локальной SQLite базе.
- `discovery/search/service.py` — поиск по ключевым словам через SQLite FTS5.
- `discovery/mcp_server.py` — MCP tools на FastMCP.
- `discovery/cli.py` — CLI для ручной проверки.
- `sources.json` — конфигурация источников.

Документ индекса имеет единый формат:

```json
{
  "source_id": "sqlite_demo",
  "object_type": "table",
  "path": "products",
  "title": "products",
  "text": "products id sku name category price",
  "metadata": {}
}
```

## Установка

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

`.[dev]` нужен для запуска тестов и устанавливает `pytest`. Если тесты не нужны, достаточно:

```bash
python -m pip install -e .
```

## Демонстрация поиска

Для демонстрации выбран CLI, как разрешено в задании.

Сначала нужно проиндексировать источники:

```bash
python -m discovery.cli index sqlite_demo
python -m discovery.cli index csv_demo
```

Потом можно искать по ключевым словам:

```bash
python -m discovery.cli search keyboard
python -m discovery.cli search email
python -m discovery.cli search order
python -m discovery.cli search product
```

Пример: поиск `keyboard` вернет таблицу `products` и колонки `products.name`, `products.sku`, потому что в sample rows есть значения `Mechanical Keyboard` и `SKU-KEYBOARD`.

Посмотреть схему объекта:

```bash
python -m discovery.cli schema sqlite_demo products
python -m discovery.cli schema csv_demo orders.csv
```

Посмотреть доступные источники:

```bash
python -m discovery.cli sources
```

## MCP tools

MCP сервер запускается так:

```bash
python -m discovery.mcp_server
```

Это stdio MCP server, а не интерактивная поисковая строка. Вводить туда `keyboard` руками не нужно: команды вызываются MCP-клиентом.

Реализованные tools:

- `listSources()` — список доступных источников.
- `indexSource(sourceId)` — индексация одного источника.
- `search(query)` — поиск по индексу.
- `getSchema(sourceId, path)` — схема таблицы или CSV-файла.

Примеры аргументов:

```json
{"sourceId": "sqlite_demo"}
{"query": "email"}
{"sourceId": "sqlite_demo", "path": "users"}
```

## Тесты

```bash
python -m pytest
```

Проверяется чтение CSV, чтение SQLite и поиск по словам `email`, `order`, `product`.

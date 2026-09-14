# План: NAME-3 Information / Review

Английская копия (по ней пишут код): [../2026-09-07-name3-review.md](../2026-09-07-name3-review.md)

**Что получим:** NAME-3 смотрит все YAML/JSON/Jinja под `environments/` плюс каталоги cluster / env / namespace. Без skip-list. Type Information, action Review. `env_definition.yml` — finding. Файлы не переименовываем.

## Пять задач

### 1. Каталог
NAME-3 в `rulemeta`: Information / Review.

### 2. Правило
Обход `environments/`, kind `File`, без skip-list, новый hint. Тесты: `env_definition`, YAML вне индекса, скрытые файлы, `appdefs` в корне не смотрим, `Inventory/` как каталог — тишина.

### 3. CLI / HTML
Консоль печатает `information`. Чипы Information / Review. Типичный `check` с `env_definition.yml` — не пустой блок NAME-3.

### 4. Algorithm-доки
`docs/algorithms/name3.md` и `ru/name3.md`.

### 5. Весь pytest

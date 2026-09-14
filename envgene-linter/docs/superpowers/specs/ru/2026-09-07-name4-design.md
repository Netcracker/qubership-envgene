# envgene-linter: NAME-4 (стем привязанного ParameterSet)

> **Историческая спецификация.** Ниже сохранены решения на 2026-09-07, включая прежний отбор файлов, примеры и тестовые ожидания. Отбор файлов и зависящие от него примеры и ожидания заменяет [общее правило подключённости](../2026-09-11-connected-only-design.md). Теперь группировка выполняется по выбранному физическому файлу, а не по совпадению имени без расширения во всём репозитории. Категории и имена кластеров/окружений берутся только из фактических использований этого файла; на файл выдаётся не более одного результата. Актуальный порядок проверки описан в [алгоритме NAME-4](../../../algorithms/ru/name4.md). Остальные решения сохраняются, если не противоречат новой области проверки.

Дата: 2026-09-07  
Статус на момент проектирования: принят в разговоре, ждёт проверки файла\
Английская копия (для реализации): [../2026-09-07-name4-design.md](../2026-09-07-name4-design.md)

Стандарт: NAME-4 SHOULD — стем привязанного ParameterSet это `<subject>-<category>`. Последний токен — категория, и он определяется массивом `envSpecific*`, где перечислен стем, по таблице ниже. Часть `<subject>` обозначает предмет параметров и выбирается оператором, например `postgresql`. В стеме не должно быть имени кластера, окружения, ticket или release. В этом цикле **выдаём результат проверки**. Файлы и `env_definition` **не** правим. Имена используются в генерации; их переименование относится к отдельному рефакторингу. TYPE **Information**, ACTION **Review**.

## Термины и чтение документа

- **ParameterSet:** YAML-файл с параметрами.
- **RepoIndex:** индекс файлов, кластеров и окружений, построенный при обнаружении содержимого репозитория (discovery).
- **Стем (stem):** имя файла без расширения данных и суффикса `.j2`, если он есть: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** отдельный результат проверки в отчёте. TYPE задаёт его тип, ACTION — рекомендуемое действие.
- **Effective Set:** итоговый набор параметров после объединения слоёв.
- **STV (Shared Template Variables):** общие переменные шаблонов.

Разделы об интеграции, порядке правил и тестах описывают цикл разработки на дату документа, а не полный состав текущего линтера. `SHOULD` обозначает рекомендацию стандарта; конкретные типы результатов указаны ниже.

## Зачем

`check` пишет NAME-4, когда стем ParameterSet есть хотя бы в одном списке `envSpecific*`, но это не `<subject>-<category>`, либо в имени зашиты имя кластера или окружения, номер задачи или обозначение релиза.

## Простыми словами

`bss.yml` в `envSpecificParamsets` → finding (нужен `bss-deploy`).  
`bss-deploy.yml` в том же массиве → нет результата проверки.\
`postgresql-pipeline.yml` в `envSpecificE2EParamsets` → нет результата проверки.\
`postgresql-deploy.yml` в e2e-массиве → finding (неверный суффикс категории).\
`qa01-bss-deploy.yml` при каталоге окружения `qa01` → finding (имя окружения включено в имя файла).\
`extra.yml` в `parameters/`, но ни один env его не перечисляет → нет результата проверки.

## Что не делаем

- Autofix / переименование / правки `env_definition`
- Ключи YAML и поле `name` (это NAME-2)
- Непривязанные ParameterSet
- Credentials, STV, resource profiles, passport, определения
- Имена каталогов (NAME-3)
- Effective Set (`compute`)
- NAME-5…NAME-9
- `--rules`, JSON-отчёт, `--strict`

## Алгоритм

Вход: только `RepoIndex`. `compute` не вызываем.

### Что считается привязкой

Стем привязан, если хотя бы одно окружение перечисляет его в любом списке `envSpecificParamsets` / `envSpecificE2EParamsets` / `envSpecificTechnicalParamsets` (`env.bindings`).

`categories(stem)` — набор `Category` (`deploy` / `e2e` / `technical`), где стем есть. Пустой набор — пропускаем.

Один раз на привязанный стем, не на каждый файл слоя.

### Суффикс категории (последняя часть имени)

| Привязка (`Category`) | Нужный последний токен |
| --- | --- |
| `deploy` (`envSpecificParamsets`) | `deploy` |
| `e2e` (`envSpecificE2EParamsets`) | `pipeline` |
| `technical` (`envSpecificTechnicalParamsets`) | `technical` |

Разбиваем стем по символу `-`. Токенов **не меньше двух**. Последний токен — ровно нужный для **каждой** категории в `categories(stem)`. Если стем указан одновременно в deploy и e2e, один суффикс не может удовлетворить обеим категориям → результат проверки.

`postgresql-deploy-ha` — последний токен `ha` → finding (после категории ничего нельзя).  
`deploy` — один токен → finding (нужна часть `<subject>`).\
Jinja: `paramset_stem` (`foo-deploy.yml.j2` → `foo-deploy`). Проверяем.

### Кластер / env / ticket / release

Finding, даже если хвост верный, если в стеме есть:

- имя каталога кластера из `index.clusters` (по границам дефиса, без учёта регистра): весь стем, инфикс `-name-`, префикс `name-` или суффикс `-name`
- имя каталога окружения (`env.name` по индексу) — так же
- ticket: `(?:^|-)(?:ticket|jira|issue)-\d+` (без учёта регистра)
- release: `(?:^|-)(?:r\d+(?:-\d+)?|20\d{2}[.-]\d{1,2})`

Слова `env` / `cluster` / `site` запрещены, только если так называется реальный каталог в индексе.

Если срабатывает и это, и хвост — **один** finding, сообщение про scope/ticket.

### Finding

Один результат проверки на привязанный стем, не соответствующий правилу.

`path`: первый файл ParameterSet с этим стемом в индексе, сорт `path.as_posix()` (обход как у NAME-1/NAME-2, потом сорт).  
`locations`: этот файл `1:1`.  
`related`: пусто.

| Поле | Значение |
| --- | --- |
| `rule` | `NAME-4` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `line` / `column` | `1:1` |
| `key` | стем |
| `scope` | токены хвоста привязки, через запятую, по алфавиту: `deploy`, `pipeline`, `technical` (токены **файла**, не `e2e`) |
| `message` (scope/ticket) | `ParameterSet {stem!r} bakes a cluster, environment, ticket or release into the name.` |
| `message` (хвост) | `ParameterSet {stem!r} must end with -{token} to match its env_definition binding ({scope}).` Если токенов несколько, `{token}` — список через `/` по алфавиту (`deploy/pipeline`). |
| `hint` | `Review whether this stem can be <subject>-<category>. Do not rename it if env_definition or other logic still depends on the current spelling.` |

Не вызывать `str.capitalize()` на сообщениях.

## Каталог, консоль, HTML

`rulemeta.py`:

- описание: `Bound ParameterSet stem is <subject>-<category>`
- по умолчанию TYPE `Information`, ACTION `Review`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`. Пустой блок: `NAME-4\nNo findings`.

Тестовый репозиторий с привязкой `env-params` — это **не** пустой блок NAME-4.

HTML: `NAME-4: Bound ParameterSet stem is <subject>-<category>`. Метки Information / Review.

Консоль: `information`. Сами результаты NAME-4 не приводят к ненулевому коду завершения.

## Движок проверок

`run_check` после NAME-3 вызывает `check_name4(index)`. Дополнительное вычисление Effective Set не требуется.

## Документация алгоритма

В реализации: `docs/algorithms/name4.md` и `docs/algorithms/ru/name4.md`. В доках NAME-1…NAME-3 в прозе про `RULE_ORDER` — семь правил, NAME-4 последним.

## Тесты

- Привязанный `bss.yml` в deploy → один NAME-4 Information / Review; ключ `bss`; в сообщении `-deploy`
- Привязанный `bss-deploy.yml` в deploy → нет NAME-4
- Привязанный `postgresql-pipeline.yml` в e2e → нет NAME-4
- Привязанный `postgresql-deploy.yml` в e2e → finding (нужен `-pipeline`)
- Привязанный `postgresql-technical.yml` в technical → нет NAME-4
- Привязанный `postgresql-deploy-ha.yml` в deploy → finding
- Привязанный `deploy.yml` в deploy → finding (нужна часть `<subject>`)
- Привязанный `qa01-bss-deploy.yml` при env `qa01` → finding
- Привязанный `bss-ticket-12-deploy.yml` в deploy → finding
- Непривязанный `extra.yml` → нет NAME-4
- Тот же стем на site и env → один finding
- Jinja `foo.yml.j2` привязан как deploy → finding (нужен `-deploy`)
- Консоль: `NAME-4` после `NAME-3`; печатает `information`
- HTML: заголовок и метки Information / Review
- PLACE-* / NAME-1…NAME-3 тесты, которые на живом `check` ждали пустой NAME-4 при `env-params`, должны ждать finding NAME-4 (чистые `render()` остаются пустыми)

## Какие файлы

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | каталог NAME-4 |
| `src/envgene_linter/report.py` | `RULE_ORDER` |
| `src/envgene_linter/engine.py` | вызов NAME-4 |
| `src/envgene_linter/rules/name4.py` | создать |
| `docs/algorithms/name4.md` | алгоритм |
| `docs/algorithms/ru/name4.md` | алгоритм по-русски |
| `docs/algorithms/name1.md` … `name3.md` и `ru/` | проза `RULE_ORDER` |
| `tests/test_name4.py` | создать |
| `tests/test_rulemeta.py`, `test_report.py`, `test_cli.py`, `test_lab.py` | каталог / пустые блоки / живой `check` |

Discovery, yamlio, Effective Set не меняем. Берём списки paramset и `env.bindings`.

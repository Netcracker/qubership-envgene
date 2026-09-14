# envgene-linter: NAME-2 (имя файла без расширения равно name)

> **Историческая спецификация.** Ниже сохранены решения на 2026-09-07, включая прежний отбор файлов, примеры и тестовые ожидания. Отбор файлов и зависящие от него примеры и ожидания заменяет [общее правило подключённости](../2026-09-11-connected-only-design.md). Проверяются только выбранные физические файлы ParameterSet и выбранные Artifact Definitions; наличие файла в каталоге определений не доказывает его использование. Актуальный порядок проверки описан в [алгоритме NAME-2](../../../algorithms/ru/name2.md). Остальные решения сохраняются, если не противоречат новой области проверки.

Дата: 2026-09-07  
Статус на момент проектирования: принят в разговоре, ждёт проверки файла\
Английская копия (для реализации): [../2026-09-07-name2-design.md](../2026-09-07-name2-design.md)

Стандарт: NAME-2 SHOULD — имя файла без расширения равно полю `name`. Стем — ключ ссылки (`env_definition` пишет `cloud-deploy`, не YAML `name`). Несовпадение можно определить однозначным сравнением. В этом цикле **выдаём результат проверки** и предлагаем задать полю `name` значение стема. Файлы **не** правим.

## Термины и чтение документа

- **ParameterSet:** YAML-файл с параметрами.
- **RepoIndex:** индекс файлов, кластеров и окружений, построенный при обнаружении содержимого репозитория (discovery).
- **Стем (stem):** имя файла без расширения данных и суффикса `.j2`, если он есть: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** отдельный результат проверки в отчёте. TYPE задаёт его тип, ACTION — рекомендуемое действие.
- **Effective Set:** итоговый набор параметров после объединения слоёв.
- **STV (Shared Template Variables):** общие переменные шаблонов.

Разделы об интеграции, порядке правил и тестах описывают цикл разработки на дату документа, а не полный состав текущего линтера. `SHOULD` обозначает рекомендацию стандарта; конкретные типы результатов указаны ниже.

## Зачем

`check` пишет NAME-2, когда у ParameterSet или файла определения `name` не равен стему файла, или `name` нет. Несовпадение — TYPE **Warning**, ACTION **Fix**. Нет имени / пустое — TYPE **Information**, ACTION **Review**.

## Простыми словами

`cloud-deploy.yml` с `name: deploy-params` → один finding: поставь `name: cloud-deploy`. Если `name: cloud-deploy` — нет результата проверки. Нет `name` (или `name: ""`) → мягче, Information, та же подсказка.

## Что не делаем

- Autofix / перепись YAML
- Переименовывать файл под `name`
- Полная проверка схем определений Application / Registry / Artifact
- Смотреть env_definition, Cloud Passport, credentials, resource profiles, STV, прочий YAML
- Effective Set (`compute`)
- NAME-3…NAME-9
- `--rules`, JSON, `--strict`
- `check` без `environments/` (по-прежнему exit 2)

## Алгоритм

Вход: только `RepoIndex`. `compute` не вызываем.

### Файлы

**ParameterSet.** Все `ParamsetFile` в индексе (repository, cluster, environment) без Jinja и без ошибки чтения. Непривязанные файлы (orphan) **входили в историческую область проверки**; сейчас они исключены по правилу подключённости выше.

**Определения.** YAML в этих каталогах от корня репозитория экземпляра EnvGene (как в старом линтере). Пути, которые после разрешения ссылок указывают на один физический файл, учитываем один раз:

| Каталог | Kind |
| --- | --- |
| `appdefs` | Application definition |
| `configuration/appdefs` | Application definition |
| `regdefs` | Registry definition |
| `configuration/regdefs` | Registry definition |
| `configuration/artifact_definitions` | Artifact definition |

Определение с ошибкой загрузки YAML пропускаем. Jinja (`.yml.j2` / `.yaml.j2`) — как у paramset.

Passport, `env_definition` и прочий YAML не смотрим.

### Стем и объявленное имя

- Стем = уже существующий `paramset_stem` (`cloud-deploy.yml` и `cloud-deploy.yml.j2` → `cloud-deploy`).
- Объявленное имя = `name` в корне документа. Нет ключа, `None` или `""` — **имени нет**. Иначе сравниваем `str(name)` со стемом (`name: 1` это `"1"`).

Если `str(name) == stem` → нет finding.

### Finding

Один finding на файл. Одна из двух форм.

**Несовпадение** — имя есть и не равно стему:

| Поле | Значение |
| --- | --- |
| `rule` | `NAME-2` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | ключ `name` |
| `locations` | эта одна точка |
| `key` | `name` |
| `scope` | стем |
| `related` | пусто |
| `message` | `{kind} filename stem {stem!r} does not equal the name field {declared!r}.` |
| `hint` | `Set name: {stem} to match the filename, which is the reference key.` |

`kind`: `ParameterSet`, `Application definition`, `Registry definition` или `Artifact definition`.

**Нет имени** — ключа нет, `None` или `""`:

| Поле | Значение |
| --- | --- |
| `rule` | `NAME-2` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `path` / `line` / `column` | ключ `name`, если он есть (в том числе `""`); иначе `1:1` |
| `locations` | эта одна точка |
| `key` | `name` |
| `scope` | стем |
| `related` | пусто |
| `message` | `{kind} {filename} has no name field; EnvGene requires it to equal the filename stem {stem!r}.` |
| `hint` | `Set name: {stem}` |

`{filename}` — `path.name` (например `cloud-deploy.yml`).

Побеждает имя файла. Не предлагаем переименовать файл.

## Каталог, консоль, HTML

`rulemeta.py`:

- описание: `Filename stem must equal the name field`
- по умолчанию TYPE `Warning`, ACTION `Fix`

У «нет имени» TYPE/ACTION — Information / Review. PLACE-* остаются Warning / Fix. NAME-1 — Information / Review.

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`. Пустой блок: `NAME-2\nNo findings`.

HTML: как у других правил. Заголовок `NAME-2: Filename stem must equal the name field`. FILE — `locations`. Метки по finding: Warning/Fix или Information/Review.

## Движок проверок и обнаружение файлов

`run_check` после NAME-1 вызывает `check_name2(index)`. Дополнительное вычисление Effective Set не требуется.

В discovery появляется список `NamedEntityFile` на `RepoIndex` (путь, стем, kind, loaded / error). Paramset уже в индексе; `name` читаем из `loaded.doc` в правиле.

`check` по-прежнему требует `environments/` (exit 2). Определения сканируем, когда эта проверка идёт и каталоги есть.

## Документация алгоритма

В реализации: `docs/algorithms/name2.md` и `docs/algorithms/ru/name2.md` (как у NAME-1).

## Тесты

- Paramset: стем = `name` → нет NAME-2
- Paramset: другое `name` → один Warning / Fix; в сообщении стем и объявленное; подсказка — задать полю `name` значение стема
- Paramset без `name` → Information / Review
- Paramset `name: ""` → Information / Review
- Orphan с расхождением → finding
- Jinja пропускаем
- YAML с ошибкой загрузки пропускаем
- Artifact в `configuration/artifact_definitions` с расхождением → finding (`Artifact definition`)
- Application или registry: стем = `name` → нет finding
- Консоль: `NAME-2` после `NAME-1`; несовпадение печатает `warning`
- HTML: `NAME-2: Filename stem must equal the name field`; метки Warning / Fix
- Тесты PLACE-* и NAME-1 должны проходить; точные строки «No findings» обновляем (появился блок NAME-2)

## Какие файлы

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/model.py` | `NamedEntityFile`; список на `RepoIndex` |
| `src/envgene_linter/discovery.py` | пять каталогов определений |
| `src/envgene_linter/rulemeta.py` | каталог NAME-2 |
| `src/envgene_linter/report.py` | `RULE_ORDER` |
| `src/envgene_linter/engine.py` | вызов NAME-2 |
| `src/envgene_linter/rules/name2.py` | создать |
| `docs/algorithms/name2.md` | алгоритм |
| `docs/algorithms/ru/name2.md` | алгоритм по-русски |
| `tests/test_name2.py` | создать |
| `tests/test_report.py`, `test_cli.py`, `test_rulemeta.py` | пустой блок / каталог |

yamlio и Effective Set не меняем. Берём `paramset_stem` и `LoadedYaml.position`.

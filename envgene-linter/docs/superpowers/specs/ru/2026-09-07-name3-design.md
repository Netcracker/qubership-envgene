# envgene-linter: NAME-3 (имена в kebab-case)

> **Историческая спецификация.** Ниже сохранены решения на 2026-09-07, включая прежний отбор файлов, примеры и тестовые ожидания. Отбор файлов и зависящие от него примеры и ожидания заменяет [общее правило подключённости](../2026-09-11-connected-only-design.md). Прежний рекурсивный обход файлов и проверка всех каталогов namespace заменены. Проверяются только выбранные файлы, используемые определения окружений и их каталоги кластеров/окружений, а также namespace, на которые указывают разрешённые привязки ParameterSet или Resource Profile. Актуальный порядок проверки описан в [алгоритме NAME-3](../../../algorithms/ru/name3.md). Остальные решения сохраняются, если не противоречат новой области проверки.

Дата: 2026-09-07  
Статус на момент проектирования: поправлен в разговоре (Information / Review; все YAML под `environments/`); ждёт проверки файла\
Английская копия (для реализации): [../2026-09-07-name3-design.md](../2026-09-07-name3-design.md)

Стандарт: NAME-3 SHOULD — имена файлов, каталогов и namespace — kebab-case. Имена полей YAML и значения перечислений (enum) следуют соглашениям соответствующего объекта; это правило их **не** проверяет.

В этом цикле **выдаём результат проверки**. Файлы и каталоги **не** переименовываем. Часть имён используется в логике генерации; их переименование относится к отдельному рефакторингу. Поэтому у каждого finding TYPE **Information**, ACTION **Review**.

## Термины и чтение документа

- **ParameterSet:** YAML-файл с параметрами.
- **RepoIndex:** индекс файлов, кластеров и окружений, построенный при обнаружении содержимого репозитория (discovery).
- **Стем (stem):** имя файла без расширения данных и суффикса `.j2`, если он есть: `cloud-deploy.yml.j2` → `cloud-deploy`.
- **Finding:** отдельный результат проверки в отчёте. TYPE задаёт его тип, ACTION — рекомендуемое действие.
- **Effective Set:** итоговый набор параметров после объединения слоёв.
- **STV (Shared Template Variables):** общие переменные шаблонов.

Разделы об интеграции, порядке правил и тестах описывают цикл разработки на дату документа, а не полный состав текущего линтера. `SHOULD` обозначает рекомендацию стандарта; конкретные типы результатов указаны ниже.

## Зачем

`check` пишет NAME-3, когда (1) имя каталога кластера, окружения или namespace не kebab-case, или (2) у YAML / JSON / Jinja-файла под `environments/` стем не kebab-case. TYPE **Information**, ACTION **Review**.

## Простыми словами

`environments/Cluster_01/` → один finding (каталог кластера). `cloud-deploy.yml` — нет результата проверки. `Cloud_Deploy.yml` — finding. `env_definition.yml` — finding (`env_definition` не kebab-case). Каталог `Inventory/` — не finding (это не cluster / env / namespace). Файлы внутри `Inventory/` проверяем.

## Что не делаем

- Autofix / переименование файлов и каталогов
- Ключи YAML и значения перечислений (enum)
- Файлы вне `environments/` (включая `appdefs/` / `regdefs/` / `artifact_definitions` в корне репо)
- Файлы с неподдерживаемыми расширениями под `environments/` (`.md`, `.png`, `.txt`, …)
- Имена каталогов кроме cluster, environment и namespace (`Inventory/`, `parameters/`, `cloud-passport/`, …)
- Effective Set (`compute`)
- NAME-4…NAME-9
- `--rules`, JSON-отчёт, `--strict`

## Алгоритм

Вход: `RepoIndex` (корень, кластеры, окружения). `compute` не вызываем. Файлы — обход `environments/` на диске. Discovery не меняем.

### Kebab-case

Имя — kebab-case, если целиком подходит под `^[a-z0-9]+(?:-[a-z0-9]+)*$`. Допустимы: `env`, `cluster-01`, `cloud-deploy`, `credentials` (одна часть из строчных букв). Недопустимы: `Cluster_01`, `Cloud_Deploy`, `env_definition`, пустая строка.

### Без списка исключений

Имена EnvGene не пропускаем. `env_definition` — finding. Каталог `Inventory` по-прежнему вне области проверки (см. выше); файл `Inventory.yml` под `environments/` был бы finding.

### Какие файлы

Под `environments/` берём путь, если это файл и имя кончается на `.yml`, `.yaml`, `.json`, `.yml.j2`, `.yaml.j2` или `.json.j2`. Скрытые файлы (имя с `.`) — тоже.

В каталог с именем `.git` не заходим.

### Стем

Тот же `paramset_stem`: сначала срезать `.j2`, потом `.yml` / `.yaml` / `.json`. С kebab сверяем этот стем, не имя с расширением.

### Что смотрим

Один результат проверки на путь с именем, не соответствующим правилу. Если `is_kebab(name)` — нет результата проверки.

| Откуда | Имя | Kind | Путь |
| --- | --- | --- | --- |
| каждый кластер в индексе | `cluster.name` | `Cluster directory` | `cluster.path` |
| каждый env в индексе | `env.name` | `Environment directory` | `env.path` |
| каждый подкаталог `env.path / "Namespaces"` (включая скрытые; без рекурсии) | имя каталога | `Namespace` | этот каталог |
| каждый подходящий файл под `environments/` (обход, не списки paramset/passport/entity) | `paramset_stem(path)` | `File` | этот файл |

Списки `ParamsetFile` / `NamedEntityFile` / `PassportFile` не итерируем — иначе дубли путей с обхода и пропуск credentials / STV / прочего YAML, которого нет в индексе.

Скрытые каталоги кластера / окружения, если discovery их проиндексировал, — включаем в отчёт. Имена с `.` не пропускаем.

### Finding

| Поле | Значение |
| --- | --- |
| `rule` | `NAME-3` |
| `severity` | `Severity.INFORMATION` (`information`) |
| `issue_type` | `Information` |
| `action` | `Review` |
| `path` / `line` / `column` | каталог или файл; `1:1` |
| `locations` | эта одна точка |
| `key` | имя, не соответствующее правилу |
| `scope` | строка kind |
| `related` | пусто |
| `message` | `{kind} {name!r} is not kebab-case.` |
| `hint` | `Review whether this name can be kebab-case. Do not rename it if generation or other logic still depends on the current spelling.` |

Не вызывать `str.capitalize()` на `kind`. Kind — как в таблице.

## Каталог, консоль, HTML

`rulemeta.py`:

- описание: `Filenames, directories, and namespaces use kebab-case` (как было)
- по умолчанию TYPE `Information`, ACTION `Review`

`RULE_ORDER` без изменений: `PLACE-1`, `PLACE-2`, `PLACE-3`, `NAME-1`, `NAME-2`, `NAME-3`. Пустой блок: `NAME-3\nNo findings`.

Обычный тестовый репозиторий с `env_definition.yml` — это **не** пустой блок NAME-3: есть finding `File` на `env_definition`.

HTML: `NAME-3: Filenames, directories, and namespaces use kebab-case`. Метки Information / Review.

Консоль выводит `information`. Сами результаты NAME-3 не приводят к ненулевому коду завершения; другие результаты или ошибки команды могут его изменить.

## Движок проверок

`run_check` по-прежнему после NAME-2 вызывает `check_name3(index)`. Дополнительное вычисление Effective Set не требуется.

## Документация алгоритма

В реализации обновить `docs/algorithms/name3.md` и `docs/algorithms/ru/name3.md`.

## Тесты

- Кластер `Cluster_01` → NAME-3 Information / Review, kind `Cluster directory`; в сообщении `Cluster_01`; hint про review (в том же репо ещё finding `File` на `env_definition`)
- Kebab cluster и env (`cluster-01`, `env-01`) → нет finding на эти каталоги; finding `File` на `env_definition` остаётся
- Env `Env_01` → finding `Environment directory`
- Каталог namespace `Foo` в `Namespaces/` → finding `Namespace`
- Paramset `Cloud_Deploy.yml` → finding `File` (не `ParameterSet`)
- `env_definition.yml` → finding `File` `'env_definition'`
- Каталог `Inventory` не NAME-3
- Kebab-стем (`cloud-deploy.yml`) → нет finding с этого файла
- Консоль: `NAME-3` после `NAME-2`; finding печатает `information`
- HTML: заголовок как был; метки Information / Review
- PLACE-* / NAME-1 / NAME-2 тесты, которые на живом `check` ждали пустой NAME-3 при наличии `env_definition.yml`, должны ждать finding на `env_definition` (чистые unit-тесты `render()` без NAME-3 finding остаются пустыми)

## Какие файлы

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | значения по умолчанию для NAME-3 → Information / Review |
| `src/envgene_linter/rules/name3.py` | обход `environments/`; без списка исключений; Information; новый hint |
| `docs/algorithms/name3.md` | алгоритм |
| `docs/algorithms/ru/name3.md` | алгоритм по-русски |
| `tests/test_name3.py` | новые ожидания |
| `tests/test_cli.py`, `tests/test_rulemeta.py` | консоль / HTML / каталог |
| `tests/test_report.py` | только если сломаются пустые блоки |

Discovery, yamlio, Effective Set не меняем. Берём `paramset_stem`.

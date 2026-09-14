# envgene-linter: PLACE-6 (пайплайн-наборы привязываются к Cloud)

Отбор проверяемых файлов определяется более поздним общим [правилом подключённости](../2026-09-11-connected-only-design.md).

Описанная ниже проверка только по привязкам — историческое решение. По общему правилу подключённости цель проверяется лишь тогда, когда хотя бы одна ссылка её списка выбирает файл для данного окружения. Пустые списки и списки только с неразрешёнными ссылками не дают замечаний. См. [актуальный алгоритм](../../../algorithms/ru/place6.md); количество правил ниже относится к этому циклу.

Дата: 2026-09-09  
Статус на момент проектирования: принят в разговоре, ждёт проверки файла\
Английская версия: [../2026-09-09-place6-design.md](../2026-09-09-place6-design.md)

Стандарт: PLACE-6 MUST — пайплайн-ParameterSet (`e2eParameters` / `envSpecificE2EParamsets`) ассоциируется только с Cloud. Файл может находиться на слое репозитория, кластера или окружения. Фиксирована только **цель привязки** — `cloud`. В этом цикле **выдаём замечание** на цель привязки, отличную от Cloud. `env_definition` **не** правим.

## Зачем

Термины: `env` — окружение; `stem` — имя файла без расширения; `discovery` — обнаружение файлов и чтение привязок. TYPE обозначает тип замечания, ACTION — рекомендуемое действие; `Fix` предлагает исправление, но не выполняет его автоматически.

`check` пишет PLACE-6, когда в `envSpecificE2EParamsets` окружения есть ключ карты, отличный от `cloud` (без учёта регистра). TYPE **Warning**, ACTION **Fix**. Одно замечание на окружение + недопустимую цель привязки.

## Простыми словами

```yaml
envSpecificE2EParamsets:
  bss:
    - env-1-pipeline
```

→ замечание: `bss` — не Cloud; список должен быть под `cloud`.

```yaml
envSpecificE2EParamsets:
  cloud:
    - env-1-pipeline
```

→ нет PLACE-6. `Cloud:` / `CLOUD:` тоже без замечаний. Нет блока e2e или он пустой → замечаний нет.

`cloud` и `bss` в одной карте → одно замечание, только `bss`. Две недопустимые цели привязки → два замечания.

YAML ParameterSet и слой файла не важны. Ключи внутри файла PLACE-6 не проверяет.

## Что не делаем

- Autofix / переписывание `env_definition`
- PLACE-5 (состав ключей e2e) и PLACE-7 (одна категория на набор)
- Проверка целей `envSpecificParamsets` / `envSpecificTechnicalParamsets`
- Сверка целей с деревом `Namespaces/`
- Непривязанные файлы ParameterSet
- `--rules`, JSON-отчёт, `--strict`
- Объединение passport в Effective Set

## Алгоритм (первоначальная проверка только по привязкам)

Вход: только `RepoIndex`. `compute` не вызываем. Discovery не меняем.

Для каждого окружения берём `env.bound_targets(Category.E2E)` (уже разобрано из `envTemplate.envSpecificE2EParamsets`). Для каждого имени target в этой карте, если `target.lower() != "cloud"`, одно замечание.

Повторы исключаются структурой карты: один ключ цели на окружение. Сортировка: `(path.as_posix(), key, line)`.

### Позиция

Путь: `{env.path}/Inventory/env_definition.yml` (то же имя, что у discovery).

Читаем файл ради позиции ключа (`envTemplate` / `envSpecificE2EParamsets` / target как в YAML). `YamlReadError` → пропустить окружение (нет замечания).

### Замечание

| Поле | Значение |
| --- | --- |
| `rule` | `PLACE-6` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | `env_definition.yml` этого env; позиция ключа target |
| `locations` | эта одна точка |
| `key` | target как в YAML (`bss`, не в нижнем регистре) |
| `scope` | `"<cluster>/<env>"` |
| `related` | пусто |
| `message` | `{target} is not the Cloud; pipeline ParameterSets must bind under envSpecificE2EParamsets.cloud.` |
| `hint` | `Move the envSpecificE2EParamsets.{target} list to cloud.` |

## Каталог, консоль, HTML

`rulemeta.py`:

- описание: `Pipeline ParameterSets bind to the Cloud`
- по умолчанию TYPE `Warning`, ACTION `Fix`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `PLACE-4`, `PLACE-6`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`.

Пустой блок: `PLACE-6\nNo findings`.

HTML: `PLACE-6: Pipeline ParameterSets bind to the Cloud`. Метки Warning / Fix.

Консоль: `warning`. Exit 0.

Фикстура только с `envSpecificParamsets.cloud` (без e2e) — пустой блок PLACE-6.

## Engine

`run_check` после PLACE-4, до NAME-1 вызывает `check_place6(index)`. Дополнительное вычисление Effective Set не требуется.

## Документ алгоритма

`docs/algorithms/place6.md` и `docs/algorithms/ru/place6.md`. В других algorithm-доках `RULE_ORDER`: девять заголовков, PLACE-6 после PLACE-4, потом NAME-*. PLACE-5 в каталоге нет.

## Тесты

В сокращённых примерах ниже `e2e` означает `envTemplate.envSpecificE2EParamsets`; отдельного ключа конфигурации `e2e` здесь нет.

- `e2e: {bss: [env-1-pipeline]}` → один PLACE-6 Warning / Fix; `key == "bss"`; точные message и hint; путь — `env_definition.yml`
- `e2e: {cloud: [env-1-pipeline]}` → нет PLACE-6
- `e2e: {Cloud: [env-1-pipeline]}` → нет PLACE-6
- нет блока e2e, только deploy → нет PLACE-6
- `e2e: {bss: [a, b]}` → всё ещё одно замечание
- `e2e: {bss: […], oss: […]}` → два замечания
- `e2e: {cloud: […], bss: […]}` → одно замечание, key `bss`
- два окружения с `bss` → два замечания
- Консоль: `PLACE-6` после `PLACE-4`; печатает `warning`
- HTML: заголовок и метки Warning / Fix
- Пустые строки `render()` получают блок PLACE-6

## Какие файлы

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | каталог PLACE-6 |
| `src/envgene_linter/report.py` | `RULE_ORDER` из девяти, PLACE-6 после PLACE-4 |
| `src/envgene_linter/engine.py` | вызов PLACE-6 |
| `src/envgene_linter/rules/place6.py` | создать |
| `docs/algorithms/place6.md` | алгоритм |
| `docs/algorithms/ru/place6.md` | алгоритм по-русски |
| описание `RULE_ORDER` в других документах алгоритмов | девять правил |
| `tests/test_place6.py` | создать |
| `tests/test_lab.py`, `test_cli.py`, `test_report.py`, `test_rulemeta.py` | порядок / пустые блоки |

Discovery, yamlio, Effective Set, PLACE-1…PLACE-4 и NAME-* не меняем. Для позиций берём `load`. Привязки уже на `EnvModel`.

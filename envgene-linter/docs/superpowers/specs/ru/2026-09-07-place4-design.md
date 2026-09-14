# envgene-linter: PLACE-4 (ключи passport не в ParameterSet)

Отбор проверяемых файлов определяется более поздним общим [правилом подключённости](../2026-09-11-connected-only-design.md).

Описанные ниже отбор по имени файла во всём репозитории и повторное чтение Jinja — исторические решения. Теперь общее правило подключённости требует, чтобы конкретный физический ParameterSet был выбран для окружения, и исключает необработанные Jinja из проверки содержимого. Остальные решения и порядок отчёта ниже относятся к этому циклу; актуальное поведение — в [алгоритме](../../../algorithms/ru/place4.md).

Дата: 2026-09-07  
Статус на момент проектирования: принят в разговоре, ждёт проверки файла\
Английская версия: [../2026-09-07-place4-design.md](../2026-09-07-place4-design.md)

Стандарт: PLACE-4 SHOULD — контрактный ключ Cloud Passport **не живёт** в ParameterSet. Переопределение значения — в cloud-passport этого env, не в paramset. В этом цикле **выдаём замечание** и говорим перенести. Файлы **не** правим.

## Зачем

Термины: `env` — окружение; `stem` — имя файла без расширения; `discovery` — обнаружение файлов и чтение привязок. TYPE обозначает тип замечания, ACTION — рекомендуемое действие; `Fix` предлагает исправление, но не выполняет его автоматически.

**Верхний ключ** здесь — непосредственный ключ карты `parameters` в ParameterSet, а не метаданные документа вроде `name`. `TABLE` — статический набор имён контракта Cloud Passport в `passport.py`.

`check` пишет PLACE-4, когда в привязанном ParameterSet есть верхний ключ из таблицы EnvGene. TYPE **Warning**, ACTION **Fix**.

PLACE-3 оставляет только **файлы passport не на кластере**. Проверки ключей в ParameterSet (`_repository_keys`, `_env_agreement`) переезжают сюда — в том числе ключ на слое **cluster**.

## Простыми словами

`CLOUD_API_HOST` в `Inventory/parameters/cloud-deploy.yml` → замечание: положи в `cloud-passport/passport.yml` кластера или в passport этого env, если это переопределение.\
Тот же ключ только в `environments/cluster-01/cloud-passport/passport.yml` → нет PLACE-4.  
`MY_CUSTOM_HOST` из YAML passport, не из таблицы → нет PLACE-4.  
`extra.yml` ни в одном `envSpecific*` → нет PLACE-4.

## Что не делаем

- Autofix / переписывание YAML
- Объединение passport в Effective Set
- Свои ключи только из файла passport (не из `TABLE`)
- Непривязанные ParameterSet
- Credentials / STV / resource profiles как файлы
- `--rules`, JSON-отчёт, `--strict`

## Алгоритм

Вход: только `RepoIndex`. `compute` не вызываем. Берём `TABLE` из `passport.py` (ключи из файлов passport не добавляем).

### Какие файлы (первоначальный, позднее заменённый отбор)

ParameterSet входит в область проверки, если его `stem` (имя файла без расширения) есть хотя бы в одном списке `envSpecific*` (`env.bindings`). Слои site / cluster / env. Повторные записи одного пути исключаются.

### Jinja (первоначальное, позднее отменённое повторное чтение)

Если `file.is_jinja` или нет `loaded` — пробуем `load(file.path)`. Если YAML прочитан, проверяем содержимое. При `YamlReadError` пропускаем файл без замечания. Discovery не меняем.

### Что смотрим

`leaves` карты `parameters`. **Верхний ключ** — `path[0]`. Если он в `TABLE` — одно замечание на файл + ключ. Вложенные ключи под тем же верхним ключом не создают дополнительных замечаний.

Некорректный или нечитаемый файл без Jinja — пропускаем.

### Замечание

| Поле | Значение |
| --- | --- |
| `rule` | `PLACE-4` |
| `severity` | `Severity.WARNING` (`warning`) |
| `issue_type` | `Warning` |
| `action` | `Fix` |
| `path` / `line` / `column` | файл ParameterSet; позиция верхнего ключа |
| `locations` | эта одна точка |
| `key` | ключ из таблицы |
| `scope` | `"repository"` / `"<cluster>"` / `"<cluster>/<env>"` по слою файла |
| `related` | пусто |
| `message` | `{key} is a Cloud Passport contract key; do not store it in a ParameterSet.` |
| `hint` | `Move {key} to the cluster cloud-passport, or to this environment's cloud-passport if the value is an override.` |

Сортировка: `(path.as_posix(), key, line)`.

## PLACE-3 в этом цикле

В `place3.py` остаётся только `_misplaced_files`. `_repository_keys` и `_env_agreement` удаляем. Тесты PLACE-3 на ключ становятся тестами PLACE-4. Пример `place3/not-ok`, где был только DBAAS в paramset — это PLACE-4, не PLACE-3.

PLACE-1 по-прежнему не поднимает ключи каталога через существующие `Catalogs`. Это исключение сохраняется: каталог содержит таблицу и ключи passport.

## Каталог, консоль, HTML

`rulemeta.py`:

- описание: `Cloud Passport keys do not belong in ParameterSets`
- по умолчанию TYPE `Warning`, ACTION `Fix`

`RULE_ORDER`: `PLACE-1`, `PLACE-2`, `PLACE-3`, `PLACE-4`, `NAME-1`, `NAME-2`, `NAME-3`, `NAME-4`.

Пустой блок: `PLACE-4\nNo findings`.

HTML: `PLACE-4: Cloud Passport keys do not belong in ParameterSets`. Метки Warning / Fix.

Консоль: `warning`. Exit 0.

Фикстура с `env-params` без ключей таблицы — пустой блок PLACE-4.

## Engine

`run_check` после PLACE-3, до NAME-1 вызывает `check_place4(index)`. Дополнительное вычисление Effective Set не требуется.

## Документ алгоритма

`docs/algorithms/place4.md` и `ru/place4.md`. В PLACE-1…PLACE-3 и NAME-* в прозе `RULE_ORDER`: PLACE-4 после PLACE-3, потом NAME-*. В `place3.md` проверки ключей в paramset — это PLACE-4.

## Тесты

- Привязанный `cloud-deploy.yml` с `CLOUD_API_HOST` → один PLACE-4 Warning / Fix; точные message и hint
- Тот же ключ только в cluster `passport.yml` → нет PLACE-4
- Привязанный файл только с `MY_CUSTOM_HOST` → нет PLACE-4
- Непривязанный `extra.yml` с `CLOUD_API_HOST` → нет PLACE-4
- Cluster paramset с `DBAAS_AGGREGATOR_ADDRESS` → PLACE-4 (не PLACE-3)
- Site paramset с ключом таблицы → PLACE-4 (старый кейс PLACE-3)
- Два ключа таблицы в одном файле → два замечания
- Jinja, который валидный YAML и содержит ключ таблицы → PLACE-4
- Jinja, который не парсится → нет PLACE-4
- Консоль: `PLACE-4` после `PLACE-3`; печатает `warning`
- HTML: заголовок и метки Warning / Fix
- Тесты PLACE-3 на неправильное расположение passport сохраняются; проверки ключей перенесены в PLACE-4
- Пустые строки `render()` получают блок PLACE-4

## Какие файлы

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/rulemeta.py` | каталог PLACE-4 |
| `src/envgene_linter/report.py` | `RULE_ORDER` |
| `src/envgene_linter/engine.py` | вызов PLACE-4 |
| `src/envgene_linter/rules/place3.py` | убрать проверки ключей |
| `src/envgene_linter/rules/place4.py` | создать |
| `docs/algorithms/place4.md` | алгоритм |
| `docs/algorithms/ru/place4.md` | алгоритм по-русски |
| `docs/algorithms/place3.md` и `ru/` | ключи → PLACE-4 |
| описание `RULE_ORDER` в других документах алгоритмов | восемь правил |
| `tests/test_place4.py` | создать |
| `tests/test_place3.py` | кейсы ключей → PLACE-4 |
| `tests/test_lab.py`, `test_cli.py`, `test_report.py`, `test_rulemeta.py` | порядок / пустые блоки |

Discovery, yamlio, Effective Set и `TABLE` не меняем. Берём `leaves` и `load`.

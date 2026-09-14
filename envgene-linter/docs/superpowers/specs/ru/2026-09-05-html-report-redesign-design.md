# envgene-linter: переделка HTML-отчёта (группы по правилу + поля для ИИ)

Дата: 2026-09-05  
Статус на момент проектирования: принят в разговоре, ждёт проверки файла\
Английская копия (для реализации): [../2026-09-05-html-report-redesign-design.md](../2026-09-05-html-report-redesign-design.md)

## Порядок чтения и последующие изменения

Три спецификации HTML описывают последовательные этапы одной даты: [первый отчёт](2026-09-05-html-report-design.md) → [переделка](2026-09-05-html-report-redesign-design.md) → [удобство отчёта](2026-09-05-html-report-usability-design.md). Следующий этап заменяет явно изменённые требования предыдущего; остальные сохраняются. Строки статуса отражают первоначальное состояние согласования.

Это промежуточный этап, сохранённый как история решений. Этап удобства позже объединяет заголовок и описание правила в свёрнутую секцию, выводит все позиции в FILE, добавляет столбцы и несколько позиций в консоль и уменьшает метки.

Заменяет **вёрстку, поля карточки и правила изменения `.gitignore`** в [первом дизайне](2026-09-05-html-report-design.md). Флаг `--html`, путь файла, «сначала консоль», ошибка записи → exit 2, без JS и `html.escape` — как в том spec.

## Зачем

`envgene-linter check <repo> --html` печатает консоль и пишет `<repo>/envgene-linter-report.html`. Страница группируется **по правилу**, не по файлу. В карточке поля для будущего ИИ: **FILE**, **ISSUE**, **TYPE**, **ACTION**, **FIX SUGGESTION**.

Отчёт только локальный. После каждой успешной записи `--html` в `.gitignore` instance-репо должна быть строка `envgene-linter-report.html`.

## Простыми словами

Человек (или будущий ИИ-помощник) открывает один HTML. Сверху **Envgene Linter Report**, дальше секция на каждое сработавшее правило. Под **PLACE-1** — короткое английское описание, потом карточки со строками «метка — значение». Чип — небольшая скруглённая метка, например `Warning` или `Fix`. **ACTION** — одно слово (сейчас `Fix`). **FIX SUGGESTION** — что сделать. ИИ сначала смотрит ACTION, потом FIX SUGGESTION. В этом цикле никто ничего не чинит.

## Что не делаем в этом цикле

- JSON, autofix, агент, который применяет правки
- Менять **форму** консоли (блоки по правилу, path:line, severity, message, hint)
- `--strict`, `--rules`, baseline, `[EXCEPTION …]`
- Новые TYPE/ACTION у текущих PLACE-* (поля будут; сейчас Warning + Fix)
- Включать паспорт в Effective Set
- Менять логику PLACE-* (только тексты замечаний плюс `column` / type / action в модели)

## CLI и файл (как было, плюс gitignore)

```text
envgene-linter check <repo> --html
```

Всегда:

```text
<корень-instance-репо>/envgene-linter-report.html
```

Перезапись каждый запуск. Сначала stdout (консоль), потом HTML. Успех в stderr: `Wrote HTML report to envgene-linter-report.html`. Не записался HTML: stderr + exit **2**.

Без `--html`: HTML не писать, `.gitignore` не трогать.

## `.gitignore` инстанса

После успешной записи HTML убедиться, что в корне проверяемого репозитория `.gitignore` содержит имя отчёта. Допустимая строка `envgene-linter-report.html` также игнорирует файлы с этим именем в подкаталогах; строка `/envgene-linter-report.html` относится только к корню.

- Нет `.gitignore` — создать с одной строкой `envgene-linter-report.html`
- Есть, и обрезанная строка уже `envgene-linter-report.html` или `/envgene-linter-report.html` — не менять
- Иначе дописать `envgene-linter-report.html` (остальное не трогать, перевод строки в конце сохранить)

HTML записался, а `.gitignore` нет: предупреждение в stderr, код выхода check не менять (из-за gitignore не падаем).

Чужие строки gitignore не переписывать и не переставлять. В `.gitignore` **этого** репозитория линтера имя отчёта не добавляем — файл живёт в сканируемом инстансе.

## Каталог правил

Три правила и значения по умолчанию ниже относятся к этому этапу. Спецификации последующих правил расширяют каталог и `RULE_ORDER`; новую вёрстку HTML для этого вводить не нужно.

Новый маленький модуль (предложение: `src/envgene_linter/rulemeta.py`). Не внутри `html_report.py`.

У известного правила:

| Поле | Смысл |
| --- | --- |
| `id` | `PLACE-1`, `PLACE-2`, `PLACE-3` |
| `description` | Одна английская фраза — подзаголовок секции |
| `default_issue_type` | `Warning` / `Error` / `Information` |
| `default_action` | Сейчас `Fix`; `Review` в enum можно завести сразу, для будущих правил |

HTML не привязывает TYPE/ACTION к имени PLACE-*. Печатает значения полей замечания. Каталог даёт значения по умолчанию и подзаголовок.

Подзаголовки (фиксированный текст):

| Правило | Описание |
| --- | --- |
| PLACE-1 | Same value belongs on a higher layer |
| PLACE-2 | Higher layer restates a lower-layer value |
| PLACE-3 | Cloud Passport keys and files are misplaced |

Сейчас все три: TYPE `Warning`, ACTION `Fix`.

Правило не из каталога: заголовок секции — сырой id, без подзаголовка. TYPE и ACTION всё равно из полей замечания.

## Модель Finding

Оставляем: `rule`, `severity`, `path`, `line`, `key`, `scope`, `message`, `hint`, `related`.

Добавляем:

| Поле | Тип | Откуда |
| --- | --- | --- |
| `column` | `int` | Второе число уже существующего `LoadedYaml.position` / `Provenance.position` (с 1, начало ключа). В `yamlio` уже есть; правила пишут только `position[0]`. |
| `issue_type` | enum | Значение по умолчанию из каталога, правило может переопределить |
| `action` | enum | Значение по умолчанию из каталога, правило может переопределить |

Текст на чипе (точно так):

- TYPE: `Error`, `Warning`, `Information`
- ACTION: `Fix`, `Review`

`severity` не удаляем. Текущие правила оставляют `Severity.WARNING`. Консоль по-прежнему печатает `warning`.

Замечание по файлу паспорта без позиции ключа: `line=1`, `column=1`.

## ISSUE и FIX SUGGESTION (они же message / hint в консоли)

Проверки ключей PLACE-3 и их тексты ниже сохранены как история. Позже [PLACE-4](2026-09-07-place4-design.md) выносит проверки контрактных ключей Cloud Passport из PLACE-3 и задаёт новые сообщения и подсказки. PLACE-3 сохраняет проверку размещения файлов паспорта.

HTML использует `Finding.message` и `Finding.hint` — те же поля, что и консоль. На этом этапе заменяем их содержимое короткими английскими строками ниже. Консоль меняет **только текст**, не раскладку.

`related` на страницу не выносим. В модели оставляем. В новом FIX SUGGESTION списков файлов/env нет.

### PLACE-1 (env → cluster)

- ISSUE: `Key {key} has the same value in {n} environments of cluster {cluster}.`
- FIX SUGGESTION: `Move {key} to environments/{cluster}/parameters/ and remove the environment copies.`

### PLACE-1 (cluster → repository)

- ISSUE: `Key {key} has the same value in {n} clusters.`
- FIX SUGGESTION: `Move {key} to a repository paramset and remove the cluster copies.`

### PLACE-2

- ISSUE: `Key {key} at the {layer} layer repeats the lower-layer value.`
- FIX SUGGESTION: `Remove {key} from this file, or change the value if the override is intentional.`

`{layer}` — как сейчас (`environment`, `cluster`, …).

### PLACE-3 (паспорт не на кластере)

- ISSUE: `Passport {stem} is not at the cluster layer.`
- FIX SUGGESTION: текущий hint про место файла (`_file_hint`).

### PLACE-3 (ключ контракта на repository)

- ISSUE: `{key} is a Cloud Passport key authored at the repository layer.`
- FIX SUGGESTION: `Move {key} to a cluster-layer paramset.`

### PLACE-3 (ключ контракта в нескольких env)

- ISSUE: `{key} is a Cloud Passport key repeated in environments of cluster {cluster}.`
- FIX SUGGESTION: `Move {key} to the cluster layer unless an environment needs a different value.`

## Страница

Один HTML. CSS внутри. Без JavaScript. Без `<script>`. `lang="en"`. Все поля и пути через `html.escape`.

### Шапка

- Заголовок и `<title>`: `Envgene Linter Report`
- Шрифт заголовка: `Georgia, "Times New Roman", serif` (и id правила)
- Текст: системный шрифт интерфейса, светлая тема, без внешних ресурсов
- Счётчиков в шапке нет
- Заметки «не коммить» нет (это делает gitignore)

### Секции

Только правила, у которых есть замечания. Порядок: `PLACE-1`, `PLACE-2`, `PLACE-3`, потом прочие id по имени.

```
PLACE-1
Same value belongs on a higher layer

  [карточка]
  [карточка]
```

Ноль замечаний: файл всё равно пишем. Заголовок + `No findings`. Секций нет.

### Карточка (таблица + чипы)

Две колонки (метка | значение). Колонка меток около `9rem`. Метки точно:

`FILE` · `ISSUE` · `TYPE` · `ACTION` · `FIX SUGGESTION`

| Метка | Значение |
| --- | --- |
| FILE | `{относительный/путь}:{строка}:{столбец}` (POSIX `/`, от корня проверяемого репозитория; для пути вне корня показываем переданный путь с разделителями `/`) |
| ISSUE | `Finding.message` |
| TYPE | чип с именем `issue_type` |
| ACTION | чип с именем `action` |
| FIX SUGGESTION | `Finding.hint` |

`scope` и `related` не показываем.

Цвета чипов:

| Значение | Фон | Рамка |
| --- | --- | --- |
| Warning | `#fff3cd` | `#e0c36a` |
| Error | `#fde8e8` | `#e39a9a` |
| Information | `#e8eef5` | `#b0bec5` |
| Fix | `#e8f0fe` | `#9db7e8` |
| Review | `#eeeeee` | `#bbbbbb` |

Неизвестное значение: текст как есть, серый чип как у Review.

Пилюля (`border-radius: 999px`). Карточка: светлый фон, рамка `#e2e2e2`, лёгкое скругление.

## Консоль

Группировка и форма блоков в `report.py` те же, включая пустые блоки (`PLACE-2` и `No findings`). Путь остаётся `{path}:{line}` (без столбца). Строка severity та же. Новые короткие message/hint — да.

## Какие файлы трогаем

| Файл | Роль |
| --- | --- |
| `src/envgene_linter/model.py` | `column`, `issue_type`, `action` (+ enum’ы) |
| `src/envgene_linter/rulemeta.py` | Каталог: id, описание, значения по умолчанию |
| `src/envgene_linter/rules/place1.py` (и 2, 3) | `column`; значения по умолчанию из каталога; новые тексты |
| `src/envgene_linter/html_report.py` | Группы по правилу; таблица+чипы; новый title |
| `src/envgene_linter/cli.py` | После HTML — поправить `.gitignore` инстанса |
| `tests/test_html_report.py` | Новый контракт страницы |
| `tests/test_cli.py` | gitignore создать/дописать; без `--html` не трогать |
| Конструкторы Finding в тестах | Новые поля; новые message/hint |

`yamlio.position` не меняем. Engine и Effective Set не меняем.

## Тесты

Рендерер / CLI:

- Два PLACE-1 в разных файлах → один заголовок PLACE-1, две карточки, без `h2` на файл
- Правило без замечаний не появляется
- Неизвестный id правила → секция с этим id
- FILE содержит `:строка:столбец`
- Есть метки `FILE`, `ISSUE`, `TYPE`, `ACTION`, `FIX SUGGESTION`
- TYPE/ACTION — чипы (класс или эти цвета)
- Title: `Envgene Linter Report`
- `<` в message → `&lt;`
- Нет `<script`
- Ноль замечаний → `No findings`
- `--html` пишет отчёт и дописывает `.gitignore`
- Старый `.gitignore` сохраняет строки и получает имя отчёта, если его не было
- Имя уже есть → байты `.gitignore` не меняются
- Без `--html` HTML не создаётся и не перезаписывается, `.gitignore` не меняется
- gitignore нельзя записать после успешного HTML → предупреждение в stderr, не exit 2
- HTML нельзя записать → exit 2 (как было)

Тексты правил: тесты PLACE-*, которые фиксируют `message` / `hint`, обновить. Столбец: хотя бы один тест, что `column` равен `position()[1]` (фикстура yamlio с `(2, 3)` достаточна, если правило прокидывает число).

## Алгоритмы

Нового документа алгоритма нет. Английская спецификация — контракт этого этапа с учётом последующих изменений по ссылкам выше; русский текст — её перевод для читателя.

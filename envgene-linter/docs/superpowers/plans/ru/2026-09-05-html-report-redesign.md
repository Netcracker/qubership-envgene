# План: переделка HTML-отчёта

Английская копия (по ней пишут код): [../2026-09-05-html-report-redesign.md](../2026-09-05-html-report-redesign.md)

**Что получим:** страница по правилам, карточка FILE / ISSUE / TYPE / ACTION / FIX SUGGESTION, столбец в FILE, короткие английские тексты, отчёт в `.gitignore` инстанса.

**Идея:** каталог правил (`rulemeta.py`) знает описание и дефолты TYPE/ACTION. Finding получает `column`, `issue_type`, `action`. HTML только рисует. Консоль по форме не меняется.

## Пять задач

### 1. Модель и каталог

`IssueType` / `Action`, поля Finding с дефолтами (`column=1`, Warning, Fix), модуль `rulemeta.py` с тремя PLACE-* и фразами секций.

### 2. Страница

`render_html`: заголовок **Envgene Linter Report**, секции только у правил с finding’ами, таблица + чипы. Без счётчиков и без «не коммить».

### 3. gitignore

`ensure_report_ignored`: создать или дописать `envgene-linter-report.html`. CLI вызывает после успешной записи HTML. Не смогли обновить gitignore — предупреждение в stderr, exit 0.

### 4. Тексты правил и столбец

В PLACE-1/2/3: `column` из `position()[1]`, TYPE/ACTION из каталога, короткие ISSUE/FIX как в spec. `related` в модели остаётся, в hint больше не пишем списки файлов.

### 5. Весь pytest

Прогнать весь набор. Если что-то осталось — поправить и закоммитить.

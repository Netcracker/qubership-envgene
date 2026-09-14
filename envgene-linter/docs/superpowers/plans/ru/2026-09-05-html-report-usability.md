# План: удобство HTML-отчёта

Английская копия (по ней пишут код): [../2026-09-05-html-report-usability.md](../2026-09-05-html-report-usability.md)

**Что получим:** все пути копий в FILE и в консоли; секция правила — закрытая раскрывашка `PLACE-1: …`; метки мельче.

## Пять задач

### 1. Модель
`Location`, `Finding.locations`, `Finding.file_locations()`.

### 2. Правила
PLACE-1 (оба случая) и PLACE-3 env-agreement заполняют `locations`. PLACE-2 не трогаем.

### 3. Консоль
Вместо `path:line` — все строки `path:line:column`.

### 4. HTML
`<details class="rule-section">` без `open`, summary одной строкой, FILE — все пути, метки тише.

### 5. Весь pytest

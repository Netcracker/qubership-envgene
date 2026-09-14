# PLACE-6

- [PLACE-6](#place-6)
  - [Описание](#описание)
  - [Входные параметры](#входные-параметры)
  - [Ход обработки](#ход-обработки)
  - [Результат](#результат)
  - [Обработка ошибок](#обработка-ошибок)
  - [Пример](#пример)
  - [Связанные документы](#связанные-документы)

## Описание

PLACE-6 (MUST) сообщает о подключённых pipeline ParameterSet, привязанных к цели,
отличной от `cloud` без учёта регистра. Файлы могут располагаться на уровне
репозитория, кластера или окружения. Проверяется цель привязки; содержимое
ParameterSet не читается, `env_definition.yml` не изменяется.

## Входные параметры

| Параметр | Источник | Обязательный | По умолчанию | Значения / формат | Влияние |
| --- | --- | --- | --- | --- | --- |
| `index` | Discovery → `check` | Да | Нет | `RepoIndex` | Окружения, привязки и обнаруженные файлы |
| `connections` | Вызывающий код → `check` | Нет | `None`: `compute_connections(index)` | `Connections` | Выбранные физические файлы и их использования |

## Ход обработки

1. **Выбрать подключённые pipeline-цели**

   1. Использовать переданные `connections` или вычислить их из `index`.
   2. Из `connections.parameter_uses` собрать уникальные пары `(environment, target)`
      с категорией `Category.E2E`.

2. **Найти привязки вне Cloud**

   1. Для каждого обнаруженного окружения перебрать `env.bound_targets(Category.E2E)`
      из `envTemplate.envSpecificE2EParamsets`.
   2. Пропустить цели, для которых `target.lower() == "cloud"`.
   3. Пропустить цели, отсутствующие в выбранных парах. Хотя бы одна ссылка под целью
      должна разрешаться в физический файл для этого окружения.

3. **Определить позиции целей**

   1. При первой подходящей цели загрузить `<env>/Inventory/env_definition.yml`.
      Повторно использовать документ для остальных целей окружения.
   2. Получить позицию `("envTemplate", "envSpecificE2EParamsets", target)`.

4. **Сформировать замечания**

   1. Выдать одно Warning / Fix на окружение и цель, даже если под целью разрешается
      несколько имён файлов.
   2. Отсортировать по `(path.as_posix(), key, line)`.

## Результат

Возвращается список замечаний `PLACE-6` с severity `warning`, типом `Warning`,
действием `Fix`, исходным именем цели в `key` и `<cluster>/<env>` в `scope`.
Единственная позиция указывает на ключ цели в `env_definition.yml`; `related` пуст.

Сообщение: `{target} is not the Cloud; pipeline ParameterSets must bind under envSpecificE2EParamsets.cloud.`

Подсказка: `Move the envSpecificE2EParamsets.{target} list to cloud.`

Описание в каталоге: `Pipeline ParameterSets bind to the Cloud`. Консоль и HTML
показывают правило после PLACE-4 и перед PLACE-7, включая пустой блок. Сами эти
предупреждения сохраняют код завершения 0. Привязки deploy и technical не входят
в проверку; конфликты категорий ParameterSet проверяет PLACE-7.

## Обработка ошибок

**2a.** Отсутствующие или пустые привязки, пустые списки целей и только
неразрешившиеся ссылки не дают замечаний. Цели `Cloud` и `CLOUD` допустимы.

**3a.** `YamlReadError` прекращает обработку данного окружения; остальные продолжают проверяться.

**3b.** При отсутствии точной позиции используется последняя доступная позиция
предка; начальная позиция — строка 1, столбец 1.

## Пример

Пусть `pipeline-a` и `pipeline-b` разрешаются в подключённые ParameterSet:

```yaml
envTemplate:
  envSpecificE2EParamsets:
    bss: [pipeline-a, pipeline-b]
    Cloud: [pipeline-a]
```

PLACE-6 возвращает одно Warning / Fix на позиции `bss`, с ключом `bss`.
Цель `Cloud` допустима. Перенос списка `bss` под `cloud` устраняет замечание.

## Связанные документы

- [Подключённые сущности](connections.md)
- [Английская версия](../place6.md)
- [PLACE-6: реализация](../../../src/envgene_linter/rules/place6.py)
- [PLACE-6: тесты](../../../tests/test_place6.py)
- [`compute_connections`](../../../src/envgene_linter/connections.py)
- [YAML positions and traversal](../../../src/envgene_linter/yamlio.py)

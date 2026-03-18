# Effective Set API - Варианты объектной модели

- [Effective Set API - Варианты объектной модели](#effective-set-api---варианты-объектной-модели)
  - [Введение](#введение)
  - [Open Question](#open-question)
  - [Notes](#notes)
  - [Assumptions](#assumptions)
  - [Требования](#требования)
  - [Объектная модель и API](#объектная-модель-и-api)
    - [Объектная модель](#объектная-модель)
    - [POST /api/v1/environments/{environmentId}/ui-parameters/effective-set](#post-apiv1environmentsenvironmentidui-parameterseffective-set)
      - [Параметры](#параметры)
      - [Примеры запросов](#примеры-запросов)
      - [Ответы](#ответы)
      - [Примеры ответов](#примеры-ответов)
      - [Логика обработки](#логика-обработки)
  - [Детализация базовых операций](#детализация-базовых-операций)
    - [1. Кэширование Effective Set](#1-кэширование-effective-set)
    - [2. Чтение UI override ParamSet'ов из кэша и их мерж](#2-чтение-ui-override-paramsetов-из-кэша-и-их-мерж)
    - [3. Определение `state` параметра](#3-определение-state-параметра)
    - [4. Определение `value` параметра](#4-определение-value-параметра)
    - [5. Определение `originalValue` параметра](#5-определение-originalvalue-параметра)

## Введение

Этот документ описывает Effective Set API для Colly. Для понимания структуры ParamSet, правил именования файлов UI override ParamSet и работы с ParamSet API см. [colly-paramset-api.md](./colly-paramset-api.md).

## Open Question

1. Ответ должен содержать один или три контекста?
   1. Один.
2. Для чего отображается эффектив сет (переформулировать)
   1. Для энв + нс + апп
3. Требование 1: нужно ли для пользователя разделять состояние параметра 3 и 4
   1. Не нужно

## Notes

1. не закоммиченные значение с UI должны реплейсить парамсет значения
2. не закоммиченные значение и парамсет значения должны мержиться в ES

## Assumptions

1. Генерация эффектив сета (`generate_effective_set`) всегда включает в себя шаг генерации энв инстанса (`env_build`)
2. Значения параметров в UI override ParamSet не могут содержать credential macros

## Требования

1. С точки зрения пользователя UI у параметра в Effective Set есть состояния:
   1. **Я не изменял этот параметр в UI**
      1. key/value не задан UI
      2. key/value нет в UI override ParamSet в Git
      3. key/value нет в Effective Set Git
   2. **Я измениил этот параметр в UI, но не закоммитил изменения**
      1. key/value задан в UI
      2. key/value нет в UI override ParamSet в Git
      3. key/value нет в Effective Set в Git
   3. **Я измениил этот параметр в UI, и закоммитил**
      1. key/value задан в UI
      2. key/value есть в UI override ParamSet в Git
      3. key/value если ИЛИ нет в Effective Set в Git

2. Ответ на запрос Effective Set должен однозначно определять одно из состояний параметров для UI отображения

3. Ответ на запрос Effective Set должен содержать "изначальное" значение для каждого заоверраженного через UI override параметра
   1. изначальное состояние параметра это то которое было бы если бы UI оверрада бы не было

4. Запрос и ответ на Effective Set должен поддерживать структуру контекстов Effective Set
   - Deployment/Runtime контексты: параметры заданы на Application уровне
   - Pipeline контекст: параметры заданы на Namespace уровне

5. При обработке Effective Set API не должны учитываться параметры сервисного уровня, которые присутствуют только в deployment контексте:
   1. Файл `deploy-descriptor.yaml`
   2. Файлы в директории `per-service-parameters/`

## Объектная модель и API

### Объектная модель

```yaml
## EffectiveSetParameter
_type: enum[container, leaf]
_data:
  value: any                     # Текущее значение параметра (после мержа всех источников)
  state: enum[                   # Состояние параметра с точки зрения пользователя UI
    ui_override_untouched,       # Состояние 1: параметр не изменялся через UI override (untouched)
    ui_override_uncommitted,     # Состояние 2: задан в UI, но не закоммичен
    ui_override_committed        # Состояние 3: задан в UI, закоммичен
  ]
  originalValue: any             # Изначальное значение из Effective Set (до любого UI override). Для ui_override_untouched равно текущему значению
```

> [!NOTE]
> Служебные поля `_type` и `_data` используют префикс подчеркивания для предотвращения конфликтов с пользовательскими именами параметров (например, если у пользователя есть параметр с именем `data` или `type`).

что делать когда эффектив сета нет

### POST /api/v1/environments/{environmentId}/ui-parameters/effective-set

Отдает эффективный набор параметров (Effective Set) с метаданными о состоянии каждого параметра для заданного контекста (deployment/runtime/pipeline).

#### Параметры

- `environmentId` (path, mandatory) - Environment uuid
- `context` (query, mandatory) - Контекст параметров: `deployment`, `runtime`, `pipeline`
- `namespaceName` (query, mandatory для deployment/runtime) - Имя namespace
- `applicationName` (query, mandatory для deployment/runtime) - Имя приложения

**Request Body:**

- `parameters` (object, optional) - Незакоммиченные параметры из UI. **Отправляется все содержимое UI поля, в т.ч. и то что было закоммичено**

#### Примеры запросов

**Deployment context (с незакоммиченными параметрами):**

```text
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=deployment&namespaceName=env-01-core&applicationName=my-app

{
  "parameters": {
    "CUSTOM_PARAM": "uncommitted-value",
    "backupDaemon": {
      "resources": {
        "limits": {
          "cpu": "400m"
        }
      }
    }
  }
}
```

**Pipeline context (без незакоммиченных параметров):**

```text
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=pipeline

{}
```

**Runtime context:**

```text
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=runtime&namespaceName=env-01-core&applicationName=backend-service

{
  "parameters": {
    "SERVICE_PORT": "9090"
  }
}
```

#### Ответы

- `200 OK` - Effective Set успешно сформирован
  - Body: Effective Set с параметрами и метаданными
- `400 Bad Request` - Некорректные параметры запроса (отсутствует обязательный параметр, неверный контекст)
- `404 Not Found` - Namespace или Application не найдены

#### Примеры ответов

> [!NOTE]
> Примеры ответов построены на основе следующей YAML структуры параметров из Effective Set:
>
> ```yaml
> backupDaemon:
>   data: true
>   backupSchedule: "0 0 * * *"
>   resources:
>     limits:
>       cpu: "300m"
> ```

**Пример 1: Deployment context с различными состояниями параметров:**

```json
{
  "context": "deployment",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "env-01-core",
  "applicationName": "my-app",
  "parameters": {
    "backupDaemon": {
      "_type": "container",
      "_data": {
        "data": {
          "_type": "leaf",
          "_data": {
            "value": true,
            "state": "ui_override_untouched",
            "originalValue": true // optional. if None => originalValue==value
          }
        },
        "backupSchedule": {
          "_type": "leaf",
          "_data": {
            "value": "0 0 * * *",
            "state": "ui_override_untouched",
            "originalValue": "0 0 * * *"
          }
        },
        "resources": {
            "_type": "container",
            "_data": {
            "limits": {
            "_type": "container",
            "_data": {
                "cpu": {
                  "_type": "leaf",
                  "_data": {
                    "value": "300m",
                    "state": "ui_override_untouched",
                    "originalValue": "300m"
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Пример 2: Deployment context с незакоммиченными изменениями:**

```json
{
  "context": "deployment",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "env-01-core",
  "applicationName": "my-app",
  "parameters": {
    "backupDaemon": {
      "_type": "container",
      "_data": {
        "data": {
          "_type": "leaf",
          "_data": {
            "value": false,
            "state": "ui_override_uncommitted",
            "originalValue": true
          }
        },
        "backupSchedule": {
          "_type": "leaf",
          "_data": {
            "value": "0 2 * * *",
            "state": "ui_override_uncommitted",
            "originalValue": "0 0 * * *"
          }
        },
        "resources": {
            "_type": "container",
            "_data": {
            "limits": {
            "_type": "container",
            "_data": {
                "cpu": {
                  "_type": "leaf",
                  "_data": {
                    "value": "500m",
                    "state": "ui_override_uncommitted",
                    "originalValue": "300m"
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Пример 3: Deployment context с закоммиченными параметрами:**

```json
{
  "context": "deployment",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "env-01-core",
  "applicationName": "my-app",
  "parameters": {
    "backupDaemon": {
      "_type": "container",
      "_data": {
        "data": {
          "_type": "leaf",
          "_data": {
            "value": true,
            "state": "ui_override_untouched",
            "originalValue": true
          }
        },
        "backupSchedule": {
          "_type": "leaf",
          "_data": {
            "value": "0 3 * * *",
            "state": "ui_override_committed",
            "originalValue": "0 0 * * *"
          }
        },
        "resources": {
            "_type": "container",
            "_data": {
            "limits": {
            "_type": "container",
            "_data": {
                "cpu": {
                  "_type": "leaf",
                  "_data": {
                    "value": "400m",
                    "state": "ui_override_committed",
                    "originalValue": "300m"
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

**Пример 4: Пустой Effective Set (когда файлы отсутствуют):**

```json
{
  "context": "deployment",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "env-01-core",
  "applicationName": "new-app",
  "parameters": {}
}
```

#### Логика обработки

API работает с кэшированными данными Effective Set и UI override ParamSet'ами из Git.

При получении запроса:

1. **Валидация параметров запроса:**
   - Проверить наличие обязательных параметров (`environmentId`, `context`)
   - Для `deployment`/`runtime` контекстов: проверить наличие `namespaceName` и `applicationName`
   - Если параметры некорректны → `400 Bad Request`

2. **Определение `deployPostfix` (для deployment/runtime):**
   - Найти `Namespace` объект по `namespaceName` и `environmentId`
   - Получить значение поля `deployPostfix` из `Namespace` объекта
   - Если `deployPostfix` не найден → `404 Not Found`

3. **Чтение базовых параметров из кэша Effective Set:**
    Прочитать смерженный Effective Set из кэша

4. **Чтение UI override ParamSet'ов из кэша и их мерж между собой:**
    Прочитать UI override ParamSet из кэша и Применить рекурсивный мерж от низкого к высокому приоритету [детальное описание](#2-чтение-ui-override-paramsetов-из-кэша-и-их-мерж)

5. **Определение состояний параметров:**
   - Для каждого параметра определить состояние на основе источников (parameters из запроса, UI override ParamSet, Effective Set)

6. **Формирование финального Effective Set:**
   - Применить мерж: Effective Set → UI override → parameters из запроса
   - Обернуть каждый параметр в структуру `EffectiveSetParameter` (_type + _data с value, state, originalValue)

7. **Возврат ответа:**
   - Вернуть сформированный Effective Set с контекстной информацией

**Особенности обработки:**

- Если Effective Set в Git отсутствует → возврат пустого `parameters: {}`
- Если UI override ParamSet отсутствует → используются только параметры из Effective Set
- Если `parameters` в запросе пустой или отсутствует → обрабатываются только закоммиченные параметры
- `originalValue` для новых параметров (добавленных через UI override) равен `null`

## Детализация базовых операций

Перед описанием алгоритма, определим базовые операции, используемые в алгоритме:

### 1. Кэширование Effective Set

Эта операция описывает чтение файлов Effective Set из Git, их обработку и мерж. **Результат мержа кэшируется в Colly**.

**Для Deployment context:**

1. Определить `deployPostfix` из `Namespace` объекта по `namespaceName` и `environmentId`
2. Найти файлы Effective Set в Git по пути:

   ```text
   /environments/<environmentId>/effective-set/deployment/<deployPostfix>/<applicationName>/values/
   ```

3. Прочитать файлы из Git:
   - `deployment-parameters.yaml`
   - `credentials.yaml`
   - `collision-deployment-parameters.yaml`
   - `collision-credentials.yaml`

4. Для каждого прочитанного credential файла (содержат слово `credentials` в имени):
   - Удалить SOPS метаданные (поле `sops` из корня YAML)
   - Если поле `sops` присутствовало (файл был зашифрован), заменить все значения параметров на `"*****"`

5. Замержить все обработанные файлы в следующем порядке (рекурсивный мерж для словарей):
   - `deployment-parameters.yaml`
   - `credentials.yaml` (уже обработанный)
   - `collision-deployment-parameters.yaml`
   - `collision-credentials.yaml` (уже обработанный)

6. Сохранить результат мержа в кэш Colly

**Для Runtime context:**

1. Определить `deployPostfix` из `Namespace` объекта
2. Найти файлы в Git по пути:

   ```text
   /environments/<environmentId>/effective-set/runtime/<deployPostfix>/<applicationName>/
   ```

3. Прочитать файлы из Git:
   - `parameters.yaml`
   - `credentials.yaml`

4. Для файла `credentials.yaml`:
   - Удалить SOPS метаданные (поле `sops` из корня YAML)
   - Если поле `sops` присутствовало (файл был зашифрован), заменить все значения параметров на `"*****"`

5. Замержить все обработанные файлы в следующем порядке:
   - `parameters.yaml`
   - `credentials.yaml` (уже обработанный)

6. Сохранить результат мержа в кэш Colly

**Для Pipeline context:**

1. Найти файлы в Git по пути:

   ```text
   /environments/<environmentId>/effective-set/pipeline/
   ```

2. Прочитать файлы из Git:
   - `parameters.yaml`
   - `credentials.yaml`

3. Для файла `credentials.yaml`:
   - Удалить SOPS метаданные (поле `sops` из корня YAML)
   - Если поле `sops` присутствовало (файл был зашифрован), заменить все значения параметров на `"*****"`

4. Замержить все обработанные файлы в следующем порядке:
   - `parameters.yaml`
   - `credentials.yaml` (уже обработанный)

5. Сохранить результат мержа в кэш Colly

**Правила мержа:**

- Для словарей: рекурсивное объединение (если ключ есть в обоих файлах и значение — словарь, они объединяются рекурсивно)
- Для списков: полная замена (список из последнего файла заменяет предыдущий)
- Для примитивов: значение из последнего файла перезаписывает предыдущее

### 2. Чтение UI override ParamSet'ов из кэша и их мерж

Эта операция описывает чтение файлов UI override ParamSet из Git и их мерж.

1. Определить `deployPostfix` из `Namespace` объекта (для Namespace и Application уровней)
2. Определить набор уровней для чтения:
   - Для Deployment/Runtime контекстов: Environment, Namespace, Application
   - Для Pipeline контекста: Environment, Namespace
3. Для каждого уровня в порядке приоритета (от более общего к более специфичному):
   - Environment (низкий приоритет) → Namespace (средний приоритет) → Application (высокий приоритет)
   - Прочитать UI override ParamSet из кэша
4. Применить рекурсивный мерж параметров от всех уровней в порядке приоритета (значения из уровней с более высоким приоритетом перезаписывают значения из уровней с более низким приоритетом)

**Правила мержа:**

- Для словарей: рекурсивное объединение (если ключ есть в обоих файлах и значение — словарь, они объединяются рекурсивно)
- Для списков: полная замена (список из последнего файла заменяет предыдущий)
- Для примитивов: значение из последнего файла перезаписывает предыдущее

### 3. Определение `state` параметра

1. `ui_override_untouched`:
   - key/value нет в `parameters` запроса
   - key/value нет в замерженном UI override ParamSet из кэша
   - key/value есть в замерженном Effective Set из кэша

2. `ui_override_uncommitted`:
   1. изменение значение и добавление нового параметра:
      - key/value есть в `parameters` запроса
      - key/value нет в замерженном UI override ParamSet из кэша
      - key/value нет в замерженном Effective Set из кэша
   2. удаление параметра:  
      - key/value нет в `parameters` запроса
      - key/value есть в замерженном UI override ParamSet из кэша
      - key/value есть в замерженном Effective Set из кэша
3. `ui_override_committed`:
   1. изменение значение и добавление нового параметра:
      <!-- - key/value есть или нет в `parameters` запроса -->
      - key/value есть в замерженном UI override ParamSet из кэша
      <!-- - key/value есть или нет в замерженном Effective Set из кэша -->
   2. удаление параметра:  
      <!-- - key/value есть или нет в `parameters` запроса -->
      - key/value нет в замерженном UI override ParamSet из кэша
      <!-- - key/value есть или нет в замерженном Effective Set из кэша -->

### 4. Определение `value` параметра

1. Инициализировать `finalParams` = `effectiveSetParams` (копия)

2. Для параметров в состоянии 3 (`ui_override_committed`):
   - Взять значение напрямую из `uiOverrideParams` (по `paramPath`)
   - Заменить значение в `finalParams` (рекурсивный мерж)
   - **Примечание:** Значение может быть приблизительным, так как не учитывается полный мерж с другими paramset'ами. Для получения точного значения потребовалась бы полная симуляция pipeline (env_build), что замедлило бы работу API.

3. Для параметров в состоянии 1 (`ui_override_untouched`):
   - Значение уже присутствует в `finalParams` (из Effective Set)
   - Оставить значение как есть

4. Для параметров в состоянии 2 (`ui_override_uncommitted`):
   - Значение будет применено на следующем шаге (из `parameters`)

### 5. Определение `originalValue` параметра

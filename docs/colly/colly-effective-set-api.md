# Effective Set API для Colly

- [Effective Set API для Colly](#effective-set-api-для-colly)
  - [Введение](#введение)
  - [Контекст](#контекст)
    - [Структура Effective Set](#структура-effective-set)
    - [Расположение в репозитории](#расположение-в-репозитории)
    - [`state` (cостояния параметров)](#state-cостояния-параметров)
    - [`value` (таргетное значение параметра)](#value-таргетное-значение-параметра)
    - [`originalValue` (оригинальное значениепараметра )](#originalvalue-оригинальное-значениепараметра-)
    - [Правила мержа параметров](#правила-мержа-параметров)
  - [Детальное описание API](#детальное-описание-api)
    - [POST /api/v1/environments/{environmentId}/ui-parameters/effective-set](#post-apiv1environmentsenvironmentidui-parameterseffective-set)

## Введение

Данный документ содержит описание Effective Set API для Colly. Этот API используется для получения эффективного набора параметров (Effective Set) с метаданными о состоянии каждого параметра.

Effective Set API работает в рамках Option 4 (UI Override Files) и интегрирует данные из Effective Set с UI override параметрами.

Для понимания концепции UI override и сравнения подходов см. [override-ui.md](./override-ui.md).

Для работы с UI override параметрами см. [colly-ui-parameters-api.md](./colly-ui-parameters-api.md).

## Контекст

### Структура Effective Set

Effective Set - это финальный набор параметров для Environment, сгенерированный Calculator путем мержа всех источников параметров (template, inventory, custom params, UI overrides).

Effective Set организован по контекстам:

- **Deployment context** - параметры для деплоя приложений (на уровне Application)
- **Runtime context** - параметры для runtime конфигурации приложений (на уровне Application)
- **Pipeline context** - параметры для CI/CD pipeline (на уровне Namespace)

### Расположение в репозитории

**Effective Set файлы в Git:**

```text
/environments/<cluster>/<environment>/effective-set/
  deployment/<deployPostfix>/<applicationName>/values/
    deployment-parameters.yaml
    credentials.yaml
    collision-deployment-parameters.yaml
    collision-credentials.yaml
  runtime/<deployPostfix>/<applicationName>/
    parameters.yaml
    credentials.yaml
  pipeline/
    parameters.yaml
    credentials.yaml
```

**UI Override файлы в Git:**

```text
/environments/<cluster>/<environment>/ui-overrides/
  deployment.yaml
  runtime.yaml
  pipeline.yaml
```

**Original values файлы в Git (Calculator-generated):**

```text
/environments/<cluster>/<environment>/effective-set/
  deployment/<deployPostfix>/<applicationName>/values/
    ui-override-original-values.yaml
  runtime/<deployPostfix>/<applicationName>/
    ui-override-original-values.yaml
  pipeline/
    ui-override-original-values.yaml
```

### `state` (cостояния параметров)

С точки зрения UI у параметра в Effective Set есть три состояния:

1. **`ui_override_untouched`** - Я не изменял этот параметр в UI
   - key/value не задан через UI
   - key/value нет в UI override файлах в Git
   - Параметр может быть или не быть в Effective Set

2. **`ui_override_uncommitted`** - Я изменил этот параметр в UI, но не закоммитил изменения
   - key/value задан в UI
   - key/value **нет** в UI override файлах в Git
   - Значение применяется только локально в UI

3. **`ui_override_committed`** - Я изменил этот параметр в UI и закоммитил
   - key/value задан в UI
   - key/value **есть** в UI override файлах в Git
   - Значение применено в Git и будет использовано Calculator при следующей генерации ES

### `value` (таргетное значение параметра)

Таргетное значение параметра - то значение, которое будет в Effective Set после применения UI override

`value` формируется путем мержа трех источников данных в порядке приоритета (от низкого к высокому):

1. **Effective Set**
2. **UI override из Git**
3. **Uncommitted параметры** (из запроса)

### `originalValue` (оригинальное значение параметра)

**Оригинальное** значение параметра - то значение, которое было бы в Effective Set, если бы UI override не применялись.

`originalValue` показывает пользователю "откуда мы начали" до того, как были применены изменения через UI.

**Источники originalValue:**

1. **Файл `ui-override-original-values.yaml`**
2. **Effective Set**

### Правила мержа параметров

При формировании Effective Set и определении значений параметров применяются рекурсивные правила мержа (recursive merge):

- **Для словарей**: рекурсивное объединение (если ключ есть в обоих источниках и значение — словарь, они объединяются рекурсивно)
- **Для списков**: полная замена (список из последнего файла заменяет предыдущий)
- **Для примитивов**: значение из последнего файла перезаписывает предыдущее

**Порядок приоритетов источников** (от низкого к высокому):

1. **Effective Set файлы** (базовые параметры)
2. **UI override файлы из Git** (закоммиченные изменения)
3. **Uncommitted параметры** (из запроса)

## Детальное описание API

### POST /api/v1/environments/{environmentId}/ui-parameters/effective-set

Отдает эффективный набор параметров (Effective Set) с метаданными о состоянии каждого параметра для заданного контекста (deployment/runtime/pipeline).

**Параметры запроса:**

- `environmentId` (path, mandatory) - Environment uuid
- `context` (query, mandatory) - Контекст параметров: `deployment`, `runtime`, `pipeline`
- `namespaceName` (query, mandatory для deployment/runtime) - Имя namespace
- `applicationName` (query, mandatory для deployment/runtime) - Имя приложения

**Request Body:**

```json
{
  "parameters": {}
}
```

**Поля:**

- `parameters` (object, optional) - Незакоммиченные параметры из UI. **Отправляется все содержимое UI поля, включая закоммиченные параметры**

**Объектная модель EffectiveSetParameter:**

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

**Примеры запросов:**

**Deployment context (с незакоммиченными параметрами):**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=deployment&namespaceName=env-01-core&applicationName=my-app
```

```json
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

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=pipeline
```

```json
{}
```

**Runtime context:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters/effective-set?context=runtime&namespaceName=env-01-core&applicationName=backend-service
```

```json
{
  "parameters": {
    "SERVICE_PORT": "9090"
  }
}
```

**Ответы:**

- `200 OK` - Effective Set успешно сформирован
  - Body: Effective Set с параметрами и метаданными
- `400 Bad Request` - Некорректные параметры запроса (отсутствует обязательный параметр, неверный контекст)
- `404 Not Found` - Environment, Namespace или Application не найдены

**Примеры ответов:**

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
            "originalValue": true
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

**Логика обработки:**

API работает с кэшированными данными Effective Set и UI override файлами из Git.

При получении запроса:

1. **Валидация параметров запроса:**
   - Проверить наличие обязательных параметров (`environmentId`, `context`)
   - Для `deployment`/`runtime` контекстов: проверить наличие `namespaceName` и `applicationName`
   - Если параметры некорректны → `400 Bad Request`

2. **Определение `deployPostfix` (для deployment/runtime):**
   - Найти `Namespace` объект по `namespaceName` и `environmentId`
   - Получить значение поля `deployPostfix` из `Namespace` объекта
   - Если `deployPostfix` не найден → `404 Not Found`

3. **Чтение Effective Set из кэша:**

   Прочитать Effective Set из кэша. Кэш содержит результат мержа всех Effective Set файлов:

   - **Deployment context**: `deployment-parameters.yaml`, `credentials.yaml`, `collision-deployment-parameters.yaml`, `collision-credentials.yaml` (по возрастанию приоритета)
   - **Runtime context**: `parameters.yaml`, `credentials.yaml` (по возрастанию приоритета)
   - **Pipeline context**: `parameters.yaml`, `credentials.yaml` (по возрастанию приоритета)

   **Обработка credentials:**
   - SOPS метаданные (поле `sops`) удаляются из корня YAML
   - Если файл был зашифрован (поле `sops` присутствовало), все значения заменяются на `"*****"`

4. **Чтение UI override файлов из кэша и их мерж:**

   Прочитать из кэша UI override файлы (`ui-overrides/deployment.yaml`, `ui-overrides/runtime.yaml`, `ui-overrides/pipeline.yaml`) и применить мерж между уровнями:

   - **Deployment/Runtime context**: Environment → Namespace → Application (по возрастанию приоритета)
   - **Pipeline context**: Environment → Namespace (по возрастанию приоритета)

   Если файл отсутствует → использовать пустой объект `{}`

5. **Чтение original values из кэша:**

   Прочитать из кэша файл `ui-override-original-values.yaml`, сгенерированный Calculator. Этот файл содержит оригинальные значения параметров до применения UI override.

   Расположение файла:
   - **Deployment context**: `/effective-set/deployment/<deployPostfix>/<applicationName>/values/ui-override-original-values.yaml`
   - **Runtime context**: `/effective-set/runtime/<deployPostfix>/<applicationName>/ui-override-original-values.yaml`
   - **Pipeline context**: `/effective-set/pipeline/ui-override-original-values.yaml`

   Если файл отсутствует → использовать пустой объект `{}`

6. **Определение состояния параметра (state):**

   Для каждого key/value определить состояние на основе его наличия в разных источниках:

   | Параметр в `parameters` (из запроса) | Параметр в UI override (Git) | State                     |
   |--------------------------------------|------------------------------|---------------------------|
   | ❌ Нет                               | ❌ Нет                       | `ui_override_untouched`   |
   | ❌ Нет                               | ✅ Есть                      | `ui_override_committed`   |
   | ✅ Есть                              | ❌ Нет                       | `ui_override_uncommitted` |
   | ✅ Есть                              | ✅ Есть                      | `ui_override_committed`   |

   **Примечания:**
   - Uncommitted параметры из запроса (`parameters` в request body) имеют приоритет над committed
   - Если параметр есть и в uncommitted, и в Git → считается committed (значение из uncommitted будет в `value`, но state = `ui_override_committed`)

7. **Определение таргетного значения параметра (`value`):**

   Определить таргетное значение параметра - то значение, которое будет в Effective Set после применения UI override

   Применить приоритеты источников данных (от низкого к высокому):

   1. **Effective Set** (базовые параметры из кэша)
   2. **UI override из Git** (закоммиченные изменения)
   3. **Uncommitted параметры** (из request body)

8. **Определение оригинального значения параметра (`originalValue`):**

   Для каждого параметра определить `originalValue` - то значение, которое было бы в Effective Set, если бы UI override не существовали:

   - **Если параметр в `ui-override-original-values.yaml`** → использовать значение из этого файла
   - **Если параметра нет в `ui-override-original-values.yaml`**:
     - Если параметр в Effective Set → `originalValue` = значение из ES (из шага 3)
     - Если параметра нет в ES → `originalValue` = `null` (параметр добавлен через UI override)

   **Примечания:**
   - `originalValue` **всегда присутствует** в ответе для каждого параметра
   - Для параметров со state `ui_override_untouched`: `originalValue` = `value` (равны, но оба указываются)
   - Для параметров со state `ui_override_uncommitted` или `ui_override_committed`: `originalValue` показывает значение до UI override

9. **Формирование структуры ответа с метаданными:**

   Преобразовать каждый параметр в структуру `EffectiveSetParameter`:

   ```json
   {
     "_type": "leaf" | "container",
     "_data": {
       "value": <текущее значение>,
       "state": "ui_override_untouched" | "ui_override_uncommitted" | "ui_override_committed",
       "originalValue": <оригинальное значение>
     }
   }
   ```

   **Определение `_type`:**
   - `leaf` - если значение является примитивом (string, number, boolean, null) или списком
   - `container` - если значение является словарем (объектом)

   **Для container:**
   - Рекурсивно обработать все вложенные параметры
   - Каждый вложенный параметр также имеет `_type` и `_data`

10. **Возврат ответа:**
    - Вернуть сформированный Effective Set с контекстной информацией

**Особенности обработки:**

- Если Effective Set в Git отсутствует → возврат пустого `parameters: {}`
- Если UI override файлы отсутствуют → используются только параметры из Effective Set
- Если `parameters` в запросе пустой или отсутствует → обрабатываются только закоммиченные параметры
- `originalValue` **всегда присутствует** для каждого параметра в ответе:
  - Для новых параметров (добавленных через UI override) `originalValue` = `null`
  - Для untouched параметров `originalValue` = `value` (равны, но оба указываются)
  - Для uncommitted/committed параметров `originalValue` показывает значение до UI override
- При обработке **не учитываются** параметры сервисного уровня, которые присутствуют только в deployment контексте:
  - Файл `deploy-descriptor.yaml`
  - Файлы в директории `per-service-parameters/`

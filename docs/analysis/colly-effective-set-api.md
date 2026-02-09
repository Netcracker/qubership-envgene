# Effective Set API - Варианты объектной модели

- [Effective Set API - Варианты объектной модели](#effective-set-api---варианты-объектной-модели)
  - [Введение](#введение)
  - [Open Question](#open-question)
  - [Notes](#notes)
  - [Assumptions](#assumptions)
  - [Требования](#требования)
  - [Объектная модель и API](#объектная-модель-и-api)
    - [Вариант 1: Parameter Wrapper](#вариант-1-parameter-wrapper)
      - [\[Вариант 1\] Объектная модель](#вариант-1-объектная-модель)
      - [\[Вариант 1\] API запрос](#вариант-1-api-запрос)
      - [\[Вариант 1\] API ответ](#вариант-1-api-ответ)
    - [Вариант 2: Key-level Metadata](#вариант-2-key-level-metadata)
      - [\[Вариант 2\] Объектная модель](#вариант-2-объектная-модель)
      - [\[Вариант 2\] API запрос](#вариант-2-api-запрос)
      - [\[Вариант 2\] API ответ](#вариант-2-api-ответ)
  - [Формирование `parameters` и `parameterMetadata` в ответе API](#формирование-parameters-и-parametermetadata-в-ответе-api)
    - [Источники параметров](#источники-параметров)
    - [Обзор алгоритма формирования `parameters` и `parameterMetadata`](#обзор-алгоритма-формирования-parameters-и-parametermetadata)
    - [Детализация базовых операций](#детализация-базовых-операций)
      - [1. Чтение "Базовых параметров из Effective Set в Git"](#1-чтение-базовых-параметров-из-effective-set-в-git)
      - [2. Чтение UI override ParamSet'ов](#2-чтение-ui-override-paramsetов)
      - [3. Валидация пересекающихся ключей (требование 5)](#3-валидация-пересекающихся-ключей-требование-5)
    - [Определение состояний параметров](#определение-состояний-параметров)
      - [Алгоритм определения состояния параметра](#алгоритм-определения-состояния-параметра)
        - [Входные данные](#входные-данные)
        - [Шаг 0: Определение deployPostfix (для deployment/runtime контекстов)](#шаг-0-определение-deploypostfix-для-deploymentruntime-контекстов)
        - [Шаг 1: Проверка наличия в uncommittedParams запроса](#шаг-1-проверка-наличия-в-uncommittedparams-запроса)
        - [Шаг 2: Проверка наличия в UI override ParamSet в Git](#шаг-2-проверка-наличия-в-ui-override-paramset-в-git)
        - [Шаг 3: Проверка наличия в Effective Set в Git](#шаг-3-проверка-наличия-в-effective-set-в-git)
        - [Шаг 4: Определение состояния на основе проверок](#шаг-4-определение-состояния-на-основе-проверок)
        - [Шаг 5: Определение изначального значения (`originalValue`)](#шаг-5-определение-изначального-значения-originalvalue)
    - [Алгоритм формирования `parameters` и `parameterMetadata`](#алгоритм-формирования-parameters-и-parametermetadata)
      - [Шаг 1: Чтение базовых параметров из Effective Set в Git](#шаг-1-чтение-базовых-параметров-из-effective-set-в-git)
      - [Шаг 2: Чтение параметров из UI override ParamSet'ов](#шаг-2-чтение-параметров-из-ui-override-paramsetов)
      - [Шаг 3: Валидация пересекающихся ключей](#шаг-3-валидация-пересекающихся-ключей)
      - [Шаг 4: Определение состояний параметров](#шаг-4-определение-состояний-параметров)
      - [Шаг 5: Формирование значений параметров на основе состояний](#шаг-5-формирование-значений-параметров-на-основе-состояний)
      - [Шаг 6: Определение `originalValue` для каждого параметра](#шаг-6-определение-originalvalue-для-каждого-параметра)
      - [Шаг 7: Применение `uncommittedParams` (highest priority)](#шаг-7-применение-uncommittedparams-highest-priority)
      - [Шаг 8: Формирование `parameterMetadata`](#шаг-8-формирование-parametermetadata)
      - [Итоговый результат](#итоговый-результат)

## Введение

Этот документ описывает Effective Set API для Colly. Для понимания структуры ParamSet, правил именования файлов UI override ParamSet и работы с ParamSet API см. [colly-paramset-api.md](./colly-paramset-api.md).

## Open Question

1. Ответ должен содержать один или три контекста?
   1. лучше один, но спросим у Егора
2. Для чего отображается эффектив сет (переформулировать)
   1. энв, нс, апп
3. Требование 1: нужно ли для пользователя разделять состояние параметра 3 и 4

## Notes

1. Валидация на не пересечение ключей эффектив сета должна быть в калькуляторе, не колли
2. context, namespaceName, applicationName в POST /api/{environmentId}/effective-set должны быть квери параметрами, не в бодн
3. environmentId в POST /api/{environmentId}/effective-set должен быть в path
4. не закоммиченные значение с UI должны реплейсить парамсет значения
5. не закоммиченные значение и парамсет значения должны мержиться в ЭС

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
      3. key/value нет в Effective Set в Git
   4. **Я измениил этот параметр в UI, закоммитил, перегенерил эффектив сет**
      1. key/value задан в UI
      2. key/value есть в UI override ParamSet в Git
      3. key/value есть в Effective Set в Git

2. Ответ на запрос Effective Set должен однозначно определять одно из состояний параметров для UI отображения

3. Ответ на запрос Effective Set должен содержать "изначальное" значение для каждого заоверраженного через UI override параметра
   1. изначальное состояние параметра это то которое было бы если бы UI оверрада бы не было

4. Запрос и ответ на Effective Set должен поддерживать структуру контекстов Effective Set
   - Deployment/Runtime контексты: параметры заданы на Application уровне
   - Pipeline контекст: параметры заданы на Namespace уровне

5. Файлы одного контекста (для deployment контекста — с учетом деплой постфикса и приложения) не должны содержать пересекающиеся ключи на уровне конечных значений (leaf values)
   1. Пересечение ключей определяется на уровне конечных значений структуры параметров, где конечное значение — это значение, которое является примитивом (string, number, boolean) или списком примитивов
   2. Для вложенных структур - словарей - валидация проверяет только листья дерева параметров, а не промежуточные узлы

6. При обработке Effective Set API не должны учитываться параметры сервисного уровня, которые присутствуют только в deployment контексте:
   1. Файл `deploy-descriptor.yaml`
   2. Файлы в директории `per-service-parameters/`

## Объектная модель и API

### Вариант 1: Parameter Wrapper

#### [Вариант 1] Объектная модель

```yaml
## EffectiveSetParameter
type: enum[container, leaf]
data:
  value: any                     # Текущее значение параметра (после мержа всех источников)
  state: enum[                   # Состояние параметра с точки зрения пользователя UI
    ui_override_untouched,       # Состояние 1: параметр не изменялся через UI override (untouched)
    ui_override_uncommitted,     # Состояние 2: задан в UI, но не закоммичен
    # ui_override_committed,       # Состояние 3: задан в UI, закоммичен, но Effective Set еще не перегенерирован
    # ui_override_regenerated      # Состояние 4: задан в UI, закоммичен, Effective Set перегенерирован
  ]
  originalValue: any             # Изначальное значение из Effective Set (до любого UI override). Для ui_override_untouched равно текущему значению
```

#### [Вариант 1] API запрос

```text
POST /api/v1/environments/{environmentId}/ui-parameters/effective-set
```

- `environmentId` (path) - `cluster/env`
- `context` (query, mandatory) - Контекст параметров (`deployment`, `runtime`, `pipeline`)
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)
- `parameters` - в боди

```json
{
  "parameters": {
    "ANOTHER_PARAM": "pending-value",
    "PARAM": {
      "PARAM_VALUE": "value"
    }
  }
}
```

#### [Вариант 1] API ответ

```json
{
  "context": "pipeline",
  "environmentId": "cluster/env",
  "parameters": {
    "backupDaemon": {
      "type": "container",
      "data": {
        "enabled": {
          "type": "leaf",
          "data": {
            "value": true,
            "state": "ui_override_untouched",
            "originalValue": true
          }
        },
        "backupSchedule": {
          "type": "leaf",
          "data": {
            "value": "0 0 * * *",
            "state": "ui_override_untouched",
            "originalValue": "0 0 * * *"
          }
        },
        "resources": {
          "type": "container",
          "data": {
            "limits": {
              "type": "container",
              "data": {
                "cpu": {
                  "type": "leaf",
                  "data": {
                    "value": "300m",
                    "state": "ui_override_committed",
                    "originalValue": "200m"
                  }
                },
                "memory": {
                  "type": "leaf",
                  "data": {
                    "value": "256Mi",
                    "state": "ui_override_untouched",
                    "originalValue": "256Mi"
                  }
                }
              }
            },
            "requests": {
              "type": "container",
              "data": {
                "cpu": {
                  "type": "leaf",
                  "data": {
                    "value": "25m",
                    "state": "ui_override_untouched",
                    "originalValue": "25m"
                  }
                },
                "memory": {
                  "type": "leaf",
                  "data": {
                    "value": "64Mi",
                    "state": "ui_override_untouched",
                    "originalValue": "64Mi"
                  }
                }
              }
            }
          }
        },
        "storage": {
          "type": "leaf",
          "data": {
            "value": "10Gi",
            "state": "ui_override_untouched",
            "originalValue": "10Gi"
          }
        }
      }
    }
  }
}
```

> [!NOTE]
> Если `uncommittedParams` отсутствует или пустое, API возвращает только закоммиченные параметры из Effective Set и UI override.

### Вариант 2: Key-level Metadata

#### [Вариант 2] Объектная модель

```yaml
## EffectiveSetResponse
parameters: map                    # Все параметры (мерж Effective Set + UI overrides)
parameterMetadata: map             # Метаданные для каждого параметра
  <paramPath>: ParameterMetadata
    state: enum[                   # Состояние параметра
      ui_override_untouched,       # Состояние 1: параметр не изменялся через UI override (untouched)
      ui_uncommitted,              # Состояние 2: задан в UI, но не закоммичен
      ui_committed_not_built,      # Состояние 3: задан в UI, закоммичен, но Effective Set еще не перегенерирован
      ui_committed_regenerated     # Состояние 4: задан в UI, закоммичен, Effective Set перегенерирован
    ]
    originalValue: any             # Изначальное значение из Effective Set (до любого UI override). Для ui_override_untouched равно текущему значению
```

#### [Вариант 2] API запрос

Аналогично Варианту 1.

#### [Вариант 2] API ответ

**Deployment context:**

```json
{
  "context": "deployment",
  "environmentId": "cluster/env",
  "namespaceName": "env-1-core",
  "applicationName": "my-app",
  "parameters": {
    "DEPLOYMENT_SESSION_ID": "550e8400-e29b-41d4-a716-446655440000",
    "CUSTOM_PARAM": "new-value",
    "ANOTHER_PARAM": "pending-value",
    "REGENERATED_PARAM": "regenerated-value",
    "global": {
      "SOME_KEY": "global-value"
    },
    "service-name": {
      "SERVICE_PARAM": "service-value"
    }
  },
  "parameterMetadata": {
    "DEPLOYMENT_SESSION_ID": {
      "state": "ui_override_untouched",
      "originalValue": "550e8400-e29b-41d4-a716-446655440000",
    },
    "CUSTOM_PARAM": {
      "state": "ui_committed_not_regenerated",
      "originalValue": "old-value",
    },
    "ANOTHER_PARAM": {
      "state": "ui_uncommitted",
      "originalValue": "original-value",
    },
    "REGENERATED_PARAM": {
      "state": "ui_committed_regenerated",
      "originalValue": "old-value",
    },
    "global.SOME_KEY": {
      "state": "ui_override_untouched",
      "originalValue": "global-value",
    },
    "service-name.SERVICE_PARAM": {
      "state": "ui_uncommitted",
      "originalValue": "original-service-value",
    }
  }
}
```

**Pipeline context:**

```json
{
  "context": "pipeline",
  "environmentId": "cluster/env",
  "parameters": {
    "PIPELINE_PARAM": "value",
    "OVERRIDDEN_PARAM": "new-pipeline-value",
    "REGENERATED_PIPELINE_PARAM": "regenerated-pipeline-value"
  },
  "parameterMetadata": {
    "PIPELINE_PARAM": {
      "state": "ui_override_untouched",
      "originalValue": "value",
    },
    "OVERRIDDEN_PARAM": {
      "state": "ui_committed_not_regenerated",
      "originalValue": "old-pipeline-value",
    },
    "REGENERATED_PIPELINE_PARAM": {
      "state": "ui_committed_regenerated",
      "originalValue": "old-pipeline-value",
    }
  }
}
```

---

## Формирование `parameters` и `parameterMetadata` в ответе API

Секция `parameters` в ответе API содержит финальный мерж всех источников параметров с учетом их состояний. Секция `parameterMetadata` содержит метаданные для каждого параметра (состояние и изначальное значение)

### Источники параметров

1. **`uncommittedParams` из запроса** - незакоммиченные параметры, переданные в запросе
2. **Параметры из UI override ParamSet'ов** - параметры из UI override ParamSet'ов (закоммиченные в Git)
3. **Параметры из Effective Set** - параметры из Effective Set в Git

### Обзор алгоритма формирования `parameters` и `parameterMetadata`

Алгоритм состоит из следующих этапов:

1. Чтение базовых параметров из Effective Set в Git
2. Чтение параметров из UI override ParamSet'ов
3. Валидация пересекающихся ключей
4. Определение состояний параметров
5. Формирование значений параметров
6. Определение `originalValue`
7. Применение `uncommittedParams`
8. Формирование `parameterMetadata`

### Детализация базовых операций

Перед описанием алгоритма, определим базовые операции, используемые в алгоритме:

#### 1. Чтение "Базовых параметров из Effective Set в Git"

**Для Deployment context:**

1. Определить `deployPostfix` из `Namespace` объекта по `namespaceName` и `environmentId`
2. Найти файлы Effective Set по пути:

   ```text
   /environments/<environmentId>/effective-set/deployment/<deployPostfix>/<applicationName>/values/
   ```

3. Прочитать и замержить файлы в следующем порядке (рекурсивный мерж для словарей):
   - `deployment-parameters.yaml`
   - `credentials.yaml`
   - `collision-deployment-parameters.yaml`
   - `collision-credentials.yaml`

**Для Runtime context:**

1. Определить `deployPostfix` из `Namespace` объекта
2. Найти файлы по пути:

   ```text
   /environments/<environmentId>/effective-set/runtime/<deployPostfix>/<applicationName>/
   ```

3. Прочитать и замержить файлы:
   - `parameters.yaml`
   - `credentials.yaml`

**Для Pipeline context:**

1. Найти файлы по пути:

   ```text
   /environments/<environmentId>/effective-set/pipeline/
   ```

2. Прочитать и замержить файлы:
   - `parameters.yaml`
   - `credentials.yaml`

**Правила мержа файлов Effective Set:**

- Для словарей: рекурсивное объединение (если ключ есть в обоих файлах и значение — словарь, они объединяются рекурсивно)
- Для списков: полная замена (список из последнего файла заменяет предыдущий)
- Для примитивов: значение из последнего файла перезаписывает предыдущее

#### 2. Чтение UI override ParamSet'ов

Детальное описание структуры ParamSet, правил именования файлов и уровней см. в [colly-paramset-api.md](./colly-paramset-api.md#структура-paramset-yaml).

Детальное описание базовой операции чтения UI override ParamSet см. в [colly-paramset-api.md](./colly-paramset-api.md#чтение-ui-override-paramset-с-кешированием).

1. Определить `deployPostfix` из `Namespace` объекта (для Namespace и Application уровней)
2. Определить набор уровней для чтения:
   - Для Deployment/Runtime контекстов: Environment, Namespace, Application
   - Для Pipeline контекста: Environment, Namespace
3. Для каждого уровня в порядке приоритета (от более общего к более специфичному):
   - Environment (низкий приоритет) → Namespace (средний приоритет) → Application (высокий приоритет)
   - Выполнить операцию "Чтение UI override ParamSet с учетом ассоциаций окружения" для данного уровня (см. `colly-paramset-api.md`)
4. Применить рекурсивный мерж параметров от всех уровней в порядке приоритета (значения из уровней с более высоким приоритетом перезаписывают значения из уровней с более низким приоритетом)

**Для незакоммиченных override:**

1. Использовать `uncommittedParams` из запроса (если передан)

#### 3. Валидация пересекающихся ключей (требование 5)

Перед формированием финального мержа параметров необходимо выполнить валидацию на пересекающиеся ключи в файлах Effective Set одного контекста:

1. Для каждого контекста (deployment/runtime/pipeline) собрать все файлы Effective Set в Git:
   - Для deployment контекста: файлы из `/environments/<environmentId>/effective-set/deployment/<deployPostfix>/<applicationName>/values/`
   - Для runtime контекста: файлы из `/environments/<environmentId>/effective-set/runtime/<deployPostfix>/<applicationName>/`
   - Для pipeline контекста: файлы из `/environments/<environmentId>/effective-set/pipeline/`

2. Развернуть все параметры из файлов Effective Set до листьев дерева (где лист — это примитив или список примитивов)

3. Проверить наличие пересекающихся ключей на уровне листьев:
   - Если один и тот же путь к листу (`paramPath`) присутствует в нескольких файлах Effective Set с разными значениями → ошибка валидации
   - Пересечение определяется только на уровне конечных значений (листьев), не на промежуточных узлах (словарях)

4. Если обнаружены пересекающиеся ключи → вернуть ошибку валидации с указанием конфликтующих путей и файлов

**Примечание:** Эта валидация выполняется только для файлов Effective Set одного контекста, одного окружения, одного namespace (deployPostfix) и одного application.

---

### Определение состояний параметров

Для всех вариантов определение состояния параметра основано на проверке наличия key/value в источниках:

1. Аттрибут `uncommittedParams` запроса на Effective Set
      2. UI override ParamSet в Git
3. Effective Set в Git

**Правила определения состояния:**

1. `ui_override_untouched`:
   1. key/value нет в `uncommittedParams` запроса
   2. key/value нет в UI override ParamSet в Git
   3. key/value нет в Effective Set Git

2. `ui_override_uncommitted`:
   1. key/value есть в `uncommittedParams` запроса
   2. key/value нет в UI override ParamSet в Git
   3. key/value нет в Effective Set в Git

3. `ui_override_committed`:
   1. key/value если или нет в `uncommittedParams` запроса (не проверяется)
   2. key/value есть в UI override ParamSet в Git
   3. key/value нет в Effective Set в Git

4. `ui_override_regenerated`:
   1. key/value если или нет в `uncommittedParams` запроса (не проверяется)
   2. key/value есть в UI override ParamSet в Git
   3. key/value есть в Effective Set в Git

#### Алгоритм определения состояния параметра

Для каждого параметра (по пути `paramPath`) выполняется следующая последовательность проверок:

##### Входные данные

- `paramPath`: путь к параметру (например, `"CUSTOM_PARAM"` или `"service-name.SERVICE_PARAM"`)
- `context`: контекст запроса (`deployment`, `runtime`, `pipeline`)
- `environmentId`: идентификатор окружения
- `namespaceName`: имя namespace (для deployment/runtime контекстов)
- `applicationName`: имя приложения (для deployment/runtime контекстов)
- `uncommittedParams`: незакоммиченные параметры из запроса (опционально)

##### Шаг 0: Определение deployPostfix (для deployment/runtime контекстов)

1. Если `context == "pipeline"`:
   - `deployPostfix` не требуется, перейти к Шагу 1

2. Если `context == "deployment"` или `context == "runtime"`:
   - Получить объект `Namespace` из Git репозитория по `namespaceName` и `environmentId`
   - Извлечь значение поля `deployPostfix` из объекта `Namespace`
   - Результат: `deployPostfix` (например, `"env-1-core"`)

##### Шаг 1: Проверка наличия в uncommittedParams запроса

1. Если `uncommittedParams` передан в запросе:
   - Проверить наличие `paramPath` в `uncommittedParams`
   - Если `paramPath` присутствует → `inUncommittedParams = true`
   - Если `paramPath` отсутствует → `inUncommittedParams = false`

2. Если `uncommittedParams` не передан в запросе или пустой:
   - `inUncommittedParams = false`

##### Шаг 2: Проверка наличия в UI override ParamSet в Git

1. Определить путь к UI override ParamSet на основе контекста и уровня (см. раздел "2. Чтение UI override ParamSet'ов"):
   - Для `deployment/runtime`: проверить на уровнях Environment, Namespace, Application
   - Для `pipeline`: проверить на уровнях Environment, Namespace

2. Для каждого уровня прочитать соответствующий UI override ParamSet файл (если существует)

3. Извлечь параметры из ParamSet:
   - Для Environment/Namespace уровней: из секции `parameters`
   - Для Application уровня: из секции `applications[?appName=<applicationName>].parameters`

4. Применить рекурсивный мерж параметров от всех уровней (от низкого к высокому приоритету)

5. Проверить наличие `paramPath` в замерженных UI override параметрах:
   - Если `paramPath` присутствует → `inUIOverrideParamSet = true`
   - Если `paramPath` отсутствует → `inUIOverrideParamSet = false`

##### Шаг 3: Проверка наличия в Effective Set в Git

1. Определить путь к файлам Effective Set на основе контекста:
   - Для `deployment`: `/environments/<environmentId>/effective-set/deployment/<deployPostfix>/<applicationName>/values/`
   - Для `runtime`: `/environments/<environmentId>/effective-set/runtime/<deployPostfix>/<applicationName>/`
   - Для `pipeline`: `/environments/<environmentId>/effective-set/pipeline/`

2. Прочитать и замержить файлы Effective Set (см. раздел "1. Чтение Базовых параметров из Effective Set в Git")

3. Проверить наличие `paramPath` в замерженном Effective Set:
   - Если `paramPath` присутствует → `inEffectiveSet = true`
   - Если `paramPath` отсутствует → `inEffectiveSet = false`

##### Шаг 4: Определение состояния на основе проверок

Применить правила определения состояния в следующем порядке:

1. Если `inUncommittedParams == false` AND `inUIOverrideParamSet == false` AND `inEffectiveSet == false`:
   - **Состояние = 1 (ui_override_untouched)**
   - Параметр отсутствует во всех источниках (не задан в UI, нет в UI override ParamSet, нет в Effective Set)

2. Если `inUncommittedParams == true` AND `inUIOverrideParamSet == false` AND `inEffectiveSet == false`:
   - **Состояние = 2 (ui_override_uncommitted)**
   - Параметр задан в UI (есть в uncommittedParams), но не закоммичен (нет в UI override ParamSet) и нет в Effective Set

3. Если `inUIOverrideParamSet == true` AND `inEffectiveSet == false`:
   - **Состояние = 3 (ui_override_committed)**
   - Параметр присутствует в UI override ParamSet (закоммичен), но Effective Set еще не перегенерирован
   - Примечание: наличие в `uncommittedParams` не проверяется для этого состояния

4. Если `inUIOverrideParamSet == true` AND `inEffectiveSet == true`:
   - **Состояние = 4 (ui_override_regenerated)**
   - Параметр присутствует и в UI override ParamSet, и в Effective Set (Effective Set перегенерирован с учетом override)
   - Примечание: наличие в `uncommittedParams` не проверяется для этого состояния

##### Шаг 5: Определение изначального значения (`originalValue`)

1. Для состояния 1 (`ui_override_untouched`):
   - `originalValue = null` (параметр отсутствует во всех источниках, не существует)

2. Для состояния 2 (`ui_override_uncommitted`):
   - Попытаться найти значение параметра в Effective Set в Git (до UI override)
   - Если найдено → `originalValue = значение из Effective Set`
   - Если не найдено → `originalValue = null` (параметр новый, не существовал в Effective Set)

3. Для состояния 3 (`ui_override_committed`):
   - Найти значение параметра в Effective Set в Git (до UI override)
   - Если найдено → `originalValue = значение из Effective Set`
   - Если не найдено → `originalValue = null` (параметр новый, не существовал в Effective Set до override)

4. Для состояния 4 (`ui_override_regenerated`):
   - Найти значение параметра в Effective Set в Git (до UI override)
   - Если найдено → `originalValue = значение из Effective Set`
   - Если не найдено → `originalValue = null` (параметр новый, не существовал в Effective Set до override)

**Примечания:**

- Для вложенных параметров (например, `"service-name.SERVICE_PARAM"`) проверка выполняется по полному пути `paramPath`
- Сравнение значений выполняется на уровне листьев дерева параметров (примитивы и списки примитивов)
- Для состояния 2 наличие в `uncommittedParams` определяет, был ли параметр задан в UI, но не закоммичен
- По assumption, если Effective Set перегенерирован (состояние 4), то `env_build` гарантированно выполнен

**Изначальное значение (`originalValue`):**

- Для всех параметров: значение из Effective Set (до любого UI override)
- Для параметров в состоянии 1 (`ui_override_untouched`): равно текущему значению (так как нет override, текущее значение и есть исходное)
- Для параметров в состоянии 2, 3, 4: значение, которое было бы в Effective Set без UI override (может отличаться от текущего значения)

---

### Алгоритм формирования `parameters` и `parameterMetadata`

#### Шаг 1: Чтение базовых параметров из Effective Set в Git

Выполнить операцию "1. Чтение Базовых параметров из Effective Set в Git" (см. раздел "Детализация базовых операций").

Результат: `effectiveSetParams` = параметры из Effective Set (с исключением сервисных параметров согласно требованию 6)

#### Шаг 2: Чтение параметров из UI override ParamSet'ов

Выполнить операцию "2. Чтение UI override ParamSet'ов" (см. раздел "Детализация базовых операций"). Для каждого уровня применить рекурсивный мерж параметров от всех уровней (от низкого к высокому приоритету).

Результат: `uiOverrideParams` = параметры из UI override ParamSet'ов

**Примечание:** UI override ParamSet'ы читаются напрямую без полного мержа с другими paramset'ами. Значения могут быть приблизительными для параметров, которые зависят от мержа с другими paramset'ами.

#### Шаг 3: Валидация пересекающихся ключей

Выполнить операцию "3. Валидация пересекающихся ключей (требование 5)" (см. раздел "Детализация базовых операций") для файлов Effective Set одного контекста, окружения, namespace и application.

Результат: валидация пройдена (или ошибка валидации, если обнаружены пересекающиеся ключи)

#### Шаг 4: Определение состояний параметров

Для каждого параметра (по пути `paramPath`) определить состояние по алгоритму из раздела ["Алгоритм определения состояния параметра"](#алгоритм-определения-состояния-параметра) (шаги 0-4).

Результат: `stateMap` = `map<paramPath, state>`

**Примечание:** Состояния определяются для всех параметров, включая параметры из Effective Set, UI override ParamSet'ов и `uncommittedParams` (если передан).

#### Шаг 5: Формирование значений параметров на основе состояний

1. Инициализировать `finalParams` = `effectiveSetParams` (копия)

2. Для параметров в состоянии 3 (`ui_override_committed`):
   - Взять значение напрямую из `uiOverrideParams` (по `paramPath`)
   - Заменить значение в `finalParams` (рекурсивный мерж)
   - **Примечание:** Значение может быть приблизительным, так как не учитывается полный мерж с другими paramset'ами. Для получения точного значения потребовалась бы полная симуляция pipeline (env_build), что замедлило бы работу API.

3. Для параметров в состоянии 4 (`ui_override_regenerated`):
   - Значение уже присутствует в `finalParams` (из Effective Set, уже содержит UI override)
   - Оставить значение как есть

4. Для параметров в состоянии 1 (`ui_override_untouched`):
   - Значение уже присутствует в `finalParams` (из Effective Set)
   - Оставить значение как есть

5. Для параметров в состоянии 2 (`ui_override_uncommitted`):
   - Значение будет применено на следующем шаге (из `uncommittedParams`)

#### Шаг 6: Определение `originalValue` для каждого параметра

Для каждого параметра определить `originalValue` по алгоритму из раздела ["Алгоритм определения состояния параметра"](#алгоритм-определения-состояния-параметра), [Шаг 5: Определение изначального значения (`originalValue`)](#шаг-5-определение-изначального-значения-originalvalue).

Результат: `originalValueMap` = `map<paramPath, originalValue>`

#### Шаг 7: Применение `uncommittedParams` (highest priority)

1. Если `uncommittedParams` передан в запросе:
   - Применить рекурсивный мерж: `finalParams = recursiveMerge(finalParams, uncommittedParams)`
   - Для каждого параметра из `uncommittedParams`:
     - Обновить `stateMap`: `state = 2` (`ui_override_uncommitted`)
     - Обновить `originalValueMap`: `originalValue = значение из finalParams до мержа` (если было)

2. Результат: `finalParams` содержит финальный мерж всех источников

#### Шаг 8: Формирование `parameterMetadata`

Для каждого параметра (по пути `paramPath`) из `finalParams` сформировать запись в `parameterMetadata`:

1. Для каждого `paramPath` в `finalParams`:
   - Получить `state` из `stateMap[paramPath]`
   - Получить `originalValue` из `originalValueMap[paramPath]`
   - Создать объект `ParameterMetadata` со следующей структурой:

   ```yaml
   parameterMetadata[paramPath]:
     state: <state>  # значение из stateMap
     originalValue: <originalValue>  # значение из originalValueMap
   ```

2. Результат: `parameterMetadata` = `map<paramPath, ParameterMetadata>`

**Примечание:** `parameterMetadata` формируется только для параметров, присутствующих в `finalParams`. Если параметр отсутствует в `finalParams`, но присутствует в `stateMap` или `originalValueMap`, он не включается в `parameterMetadata` (так как отсутствует в `parameters`).

#### Итоговый результат

- `finalParams` → секция `parameters` в ответе API
- `parameterMetadata` → секция `parameterMetadata` в ответе API (сформирована из `stateMap` и `originalValueMap`)

---

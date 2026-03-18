# ParamSet API Design для Colly

- [ParamSet API Design для Colly](#paramset-api-design-для-colly)
  - [Введение](#введение)
  - [Требования](#требования)
  - [Контекст](#контекст)
    - [Факты о ParamSet в EnvGene](#факты-о-paramset-в-envgene)
    - [Структура ParamSet (YAML)](#структура-paramset-yaml)
    - [Ассоциация в Inventory](#ассоциация-в-inventory)
    - [API Endpoints](#api-endpoints)
  - [Общие правила API](#общие-правила-api)
    - [Определение уровня (level)](#определение-уровня-level)
    - [Поддержка контекстов по уровням](#поддержка-контекстов-по-уровням)
  - [Детальное описание API](#детальное-описание-api)
    - [1. GET /api/v1/environments/{environmentId}/ui-parameters](#1-get-apiv1environmentsenvironmentidui-parameters)
    - [2. POST /api/v1/environments/{environmentId}/ui-parameters](#2-post-apiv1environmentsenvironmentidui-parameters)
    - [3. DELETE /api/v1/environments/{environmentId}/ui-parameters](#3-delete-apiv1environmentsenvironmentidui-parameters)
  - [Маппинг в Git репозиторий](#маппинг-в-git-репозиторий)
    - [Расположение ParamSet файлов](#расположение-paramset-файлов)
    - [Контракты именования UI override ParamSet](#контракты-именования-ui-override-paramset)
    - [Маппинг ассоциаций в Inventory](#маппинг-ассоциаций-в-inventory)
  - [Валидация](#валидация)
  - [Управление версиями и конфликтами](#управление-версиями-и-конфликтами)
    - [Версионирование через Git](#версионирование-через-git)

## Введение

Данный документ содержит предложения по объектной модели и API для работы с Parameter Set (ParamSet) в Colly. Colly предоставляет REST API для управления EnvGene объектами, которые хранятся в Git репозитории.

Этот документ является технической спецификацией Colly API. Для понимания концепции UI override, вариантов реализации в EnvGene и общего подхода см. [override-ui.md](./override-ui.md).

## Требования

1. Время ответа на `GET /api/v1/environments/{environmentId}/ui-parameters` должно быть менее 300 мс
2. Валидации `commitMessage` в `POST /api/v1/environments/{environmentId}/ui-parameters` со стороны колли быть не должно
3. `POST /api/v1/environments/{environmentId}/ui-parameters` должны быть транзакционными

## Контекст

### Факты о ParamSet в EnvGene

1. **Расположение в репозитории:**
   - `/environments/parameters` - глобальный уровень (site-wide)
   - `/environments/<cluster-name>/parameters` - уровень кластера (cluster-wide)
   - `/environments/<cluster-name>/<env-name>/Inventory/parameters` - уровень окружения (environment-wide)

2. **Ассоциация к объектам:**
   - К Cloud - по зарезервированному слову `cloud`
   - К Namespace - по атрибуту `deployPostfix` неймспейса

3. **Контексты параметров:**
   - `deployment`
   - `runtime`
   - `pipeline`

4. **Маппинг контекстов на секции в env_definition.yml:**
   - `deployment` → `envSpecificParamsets`
   - `runtime` → `envSpecificTechnicalParamsets`
   - `pipeline` → `envSpecificE2EParamsets`

5. **Множественная ассоциация:**
   - Один ParamSet может быть ассоциирован к нескольким окружениям/объектам/контекстам
   - При чтении параметры из нескольких ParamSet merge'атся в порядке перечисления в `env_definition.yml`
   - Последующие ParamSet перезаписывают значения предыдущих

6. **Идентификация окружения:**
   - `environmentId` - Environment uuid (используется в API)
   - `environmentPath` - `<cluster-name>/<env-name>` (используется в Git путях)

7. **Расширения файлов:**
   - ParamSet файлы могут иметь расширение `.yaml` или `.yml`
   - При чтении приоритет отдается `.yaml` - если существует файл с расширением `.yaml`, файл с `.yml` игнорируется

### Структура ParamSet (YAML)

```yaml
# Optional, deprecated
version: string
# Mandatory - имя парамсета, должно совпадать с именем файла без расширения
name: string
# Mandatory для Environment/Namespace level, Empty для Application level
parameters: hashmap
# Optional для Environment/Namespace level, Mandatory для Application level
applications:
  - appName: string
    parameters: hashmap
```

### Ассоциация в Inventory

ParamSet ассоциируется через файл `env_definition.yml` в секции `envTemplate`:

```yaml
envTemplate:
  envSpecificParamsets:           # deployment context
    <deployPostfix> | cloud:
      - "paramset-name-1"
      - "paramset-name-2"
  envSpecificTechnicalParamsets:  # runtime context
    <deployPostfix> | cloud:
      - "paramset-name-1"
  envSpecificE2EParamsets:        # pipeline context
    <deployPostfix> | cloud:
      - "paramset-name-1"
```

### API Endpoints

> [!NOTE]
> Endpoints для работы с ParamSet (`/api/v1/paramset/`) и ассоциациями (`/api/v1/environments/{environmentId}/paramset-associations`) в текущей версии реализовывать **не планируется**.
>
> Для работы с UI override параметрами используются convenience endpoints:

```text
GET      /api/v1/environments/{environmentId}/ui-parameters
POST     /api/v1/environments/{environmentId}/ui-parameters
DELETE   /api/v1/environments/{environmentId}/ui-parameters
```

## Общие правила API

### Определение уровня (level)

Уровень определяется на основе переданных параметров:

- Если не переданы `namespaceName` и `applicationName` → **Environment level**
- Если передан только `namespaceName` → **Namespace level**
- Если переданы оба параметра → **Application level**

### Поддержка контекстов по уровням

- **Environment Level:** `deployment`, `runtime`, `pipeline`
- **Namespace Level:** `deployment`, `runtime` (pipeline не поддерживается)
- **Application Level:** `deployment`, `runtime` (pipeline не поддерживается)

## Детальное описание API

### 1. GET /api/v1/environments/{environmentId}/ui-parameters

Получить UI override параметры для окружения.

> [!IMPORTANT]
> API работает с кэшированными данными. Colly не обращается к Git репозиторию напрямую при каждом GET запросе. Кэш создается и обновляется по расписанию.

**Параметры запроса:**

- `environmentId` (path, mandatory) - Environment uuid
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)

**Примеры запросов:**

```text
# Environment Level
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters

# Namespace Level
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core

# Application Level
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core&applicationName=my-app
```

**Ответы:**

- `200 OK` - Успешный запрос (всегда возвращается, даже если ParamSet не существует)
  - Body: `map` (структура зависит от уровня, см. ниже)
- `404 Not Found` - Environment, Namespace или Application не найден

**Пример успешного ответа для Environment Level:**

```json
{
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Пример успешного ответа для Namespace/Application Level:**

```json
{
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Логика обработки:**

API работает с кэшированными данными ParamSet. Кэш создается и обновляется по расписанию.

При получении запроса:

1. **Определить уровень (level)** (см. раздел ["Определение уровня"](#определение-уровня-level))

2. **Для Namespace/Application level - получить `deployPostfix`:**
   - Найти `Namespace` объект по `namespaceName` и `environmentId`
   - Получить значение поля `deployPostfix` из `Namespace` объекта
   - Если `deployPostfix` не найден → `404 Not Found`

3. **Получить параметры из кэша:**
   - Прочитать ассоциации
   - Для каждого контекста получить список ассоциированных ParamSet
   - Прочитать параметры из кэшированных ParamSet файлов
   - Вернуть результат
   - Если кэш отсутствует → возврат пустых параметров `{}` для всех контекстов с warning в логах

**Кэширование:**

Colly кэширует информацию из Git репозитория. API работает исключительно с кэшированными данными, не читает файлы из репозитория напрямую.

**Создание и обновление кэша:**

- **По расписанию:**
  - Кэш обновляется автоматически каждые n минут для всех окружений
  - Процесс выполняется в фоне, независимо от API запросов

- **Процесс создания кэша:**
  1. Прочитать `env_definition.yml` для окружения
  2. Найти все UI override ParamSet файлы по путям (попытка `.yaml`, затем `.yml`)
  3. Если файл не найден → warning в логах, кэш для этого ParamSet не создается
  4. Валидация структуры ParamSet:
     - Проверить соответствие `name` имени файла
     - Проверить наличие обязательных секций
  5. Если валидация успешна → создать/обновить кэш

**Инвалидация кэша:**

- **При кэшировании по расписанию:**
  - При ошибках валидации ParamSet файлов
  - При отсутствии обязательных полей
  - Действие: кэш для данного ParamSet удаляется, warning в логах
  - При следующем periodic sync ParamSet будет прочитан и провалидирован заново
  - При GET запросе невалидный ParamSet рассматривается как отсутствующий → возврат пустого объекта `{}` для соответствующего контекста

**Примечания:**

- `deployment` - обязательный в ответе, по умолчанию `{}`
- `runtime` - обязательный в ответе, по умолчанию `{}`
- `pipeline`
  - обязательный в ответе только для Environment Level, по умолчанию `{}`
  - не включается в ответ для Namespace и Application Level
- `404 Not Found` возвращается только если не найден сам Environment, Namespace или Application (не ParamSet)
- Если ParamSet файл не существует или ассоциация отсутствует, соответствующий контекст возвращается с пустой мапой `{}`

### 2. POST /api/v1/environments/{environmentId}/ui-parameters

Создать или обновить UI override параметры.

**Параметры запроса:**

- `environmentId` (path) - Environment uuid
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)
- `commitMessage` (body, mandatory) - Коммит мессадж для коммита в энвген репозиторий
- `commitUser` (body, mandatory) - Имя пользователя под которым происходит коммит
- `commitUserEmail` (body, mandatory) - email пользователя под которым происходит коммит
- `parameters` (body, mandatory)

**Пример запросов:**

**Environment Level:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters
```

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Namespace Level:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core
```

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Application Level:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core&applicationName=my-app
```

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Ответы:**

- `200 OK` - Параметры обновлены (если ParamSet существовал)
  - Body: полный запрос (см. ниже)
- `201 Created` - Параметры созданы (если ParamSet не существовал)
  - Body: полный запрос (см. ниже)
- `400 Bad Request` - Ошибка валидации (например, передан `pipeline` для Namespace/Application Level)
- `404 Not Found` - Environment, Namespace или Application не найден

**Примеры ответов:**

**Пример успешного ответа Environment Level:**

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": {
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": {
      "KEY3": "value3"
    },
    "pipeline": {
      "KEY4": "value4"
    }
  }
}
```

**Пример успешного ответа Namespace/Application Level:**

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": {
      "NAMESPACE_PARAM": "namespace-value"
    },
    "runtime": {
      "RUNTIME_PARAM": "runtime-value"
    }
  }
}
```

**Логика обработки:**

1. **Валидация запроса:**
   - Проверить наличие обязательных полей: `commitMessage`, `commitUser`, `commitUserEmail`, `parameters`
   - Проверить существование Environment по `environmentId`
   - Если указан `namespaceName` → проверить существование Namespace и получить `deployPostfix`
   - Если указан `applicationName` → проверить, что указан `namespaceName` и проверить существование Application

2. **Определить уровень (level)** (см. раздел ["Определение уровня"](#определение-уровня-level))

3. **Валидация контекстов по уровню:**
   - Для Namespace/Application level: если передан `pipeline` с непустым значением → `400 Bad Request`

4. **Обработать каждую секцию контекста (`deployment`, `runtime`, `pipeline`):**

   **Для каждого контекста:**

   1. Если секция **не передана** → пропустить этот контекст (не изменять)

   2. Если секция передана с **пустым объектом** `{}`:
      - Определить имя и путь ParamSet файла для этого контекста
      - Удалить ParamSet файл из Git репозитория
      - Удалить ассоциацию из `env_definition.yml`

   3. Если секция передана с **параметрами**:
      - Определить имя и путь ParamSet файла для этого контекста (см. раздел ["Контракты именования UI override ParamSet"](#контракты-именования-ui-override-paramset))
      - Создать/обновить ParamSet файл:
        - Для Environment/Namespace level: записать параметры в секцию `parameters` YAML
        - Для Application level: записать параметры в секцию `applications[appName].parameters` YAML
      - Добавить/обновить ассоциацию в `env_definition.yml`:
        - Определить `associatedObjectType`: `cloud` для Environment level, `<deployPostfix>` для Namespace/Application level
        - Определить секцию ассоциаций (см. раздел ["Маппинг ассоциаций в Inventory"](#маппинг-ассоциаций-в-inventory))
        - Добавить имя ParamSet в список, если его там нет

5. **Транзакционная запись в Git:**
   - Выполнить все изменения (создание/обновление/удаление ParamSet + обновление ассоциаций) в одном Git коммите
   - Использовать переданные `commitMessage`, `commitUser`, `commitUserEmail` для коммита
   - Если любая операция не удалась → откат всех изменений, возврат ошибки

6. **Вернуть результат:**
   - Status: `200 OK` (если ParamSet существовал) или `201 Created` (если ParamSet новый)
   - Body: полный запрос (`commitMessage`, `commitUser`, `commitUserEmail`, `parameters`)

### 3. DELETE /api/v1/environments/{environmentId}/ui-parameters

Удалить UI override параметры для окружения. Используется в reset кейсе.

Удаляются как ParamSet файлы, так и ассоциации в `env_definition.yml`. Удаление является транзакционной операцией.

**Параметры:**

- `environmentId` (path, mandatory) - Environment uuid
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)
- `commitMessage` (body, mandatory) - Коммит мессадж для коммита в энвген репозиторий
- `commitUser` (body, mandatory) - Имя пользователя под которым происходит коммит
- `commitUserEmail` (body, mandatory) - email пользователя под которым происходит коммит

**Примеры запросов:**

**Environment Level:**

```http
DELETE /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters
```

```json
{
  "commitMessage": "Reset UI overrides for environment",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com"
}
```

**Namespace Level:**

```http
DELETE /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core
```

```json
{
  "commitMessage": "Reset UI overrides for namespace env-01-core",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com"
}
```

**Application Level:**

```http
DELETE /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?namespaceName=env-01-core&applicationName=my-app
```

```json
{
  "commitMessage": "Reset UI overrides for application my-app",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com"
}
```

**Ответы:**

- `204 No Content` - Параметры успешно удалены (ParamSet файлы и ассоциации удалены)
- `404 Not Found` - Environment, Namespace или Application не найден
- `400 Bad Request` - Ошибка валидации параметров запроса

**Логика обработки:**

1. **Валидация запроса:**
   - Проверить наличие обязательных полей: `commitMessage`, `commitUser`, `commitUserEmail`
   - Проверить существование Environment по `environmentId`
   - Если указан `namespaceName` → проверить существование Namespace и получить `deployPostfix`
   - Если указан `applicationName` → проверить, что указан `namespaceName` и проверить существование Application

2. **Определить уровень (level)** (см. раздел ["Определение уровня"](#определение-уровня-level))

3. **Определить список контекстов для удаления** (см. раздел ["Поддержка контекстов по уровням"](#поддержка-контекстов-по-уровням))

4. **Удалить ParamSet для каждого контекста:**

   **Для каждого контекста из списка:**

   - Определить имя и путь ParamSet файла для этого контекста (см. раздел ["Контракты именования UI override ParamSet"](#контракты-именования-ui-override-paramset))

   - Проверить существование ParamSet файла:
      - Попытка найти файл с расширением `.yaml`
      - Если не найден, попытка найти файл с расширением `.yml`

   - Если ParamSet файл существует:
      - Удалить ParamSet файл из Git репозитория

   - Удалить ассоциацию из `env_definition.yml`:
      - Определить `associatedObjectType`: `cloud` для Environment level, `<deployPostfix>` для Namespace/Application level
      - Определить секцию ассоциаций (см. раздел ["Маппинг ассоциаций в Inventory"](#маппинг-ассоциаций-в-inventory))
      - Удалить имя ParamSet из списка ассоциаций, если оно там есть
      - Если список ассоциаций для `associatedObjectType` стал пустым → удалить ключ `associatedObjectType` из секции

5. **Запись в Git:**
   - Выполнить все удаления (ParamSet файлов + обновление ассоциаций в `env_definition.yml`) в одном Git коммите
   - Использовать переданные `commitMessage`, `commitUser`, `commitUserEmail` для коммита
   - Если коммит успешен → возврат `204 No Content`

6. **Обработка несуществующих ParamSet:**
   - Если ни один ParamSet файл не существовал → всё равно обновить `env_definition.yml` (удалить ассоциации)
   - Операция считается успешной → возврат `204 No Content`

## Маппинг в Git репозиторий

### Расположение ParamSet файлов

Все UI override ParamSet файлы расположены в:

```text
/environments/<cluster-name>/<env-name>/Inventory/parameters/
```

### Контракты именования UI override ParamSet

**Environment Level:**

- `deploy-ui-override.yaml` - deployment context
- `runtime-ui-override.yaml` - runtime context
- `pipeline-ui-override.yaml` - pipeline context

**Namespace Level:**

- `<deployPostfix>-deploy-ui-override.yaml` - deployment context
- `<deployPostfix>-runtime-ui-override.yaml` - runtime context
- Pipeline context не поддерживается

**Application Level:**

- `<deployPostfix>-<applicationName>-deploy-ui-override.yaml` - deployment context
- `<deployPostfix>-<applicationName>-runtime-ui-override.yaml` - runtime context
- Pipeline context не поддерживается

Где:

- `<deployPostfix>` — значение из объекта Namespace
- `<applicationName>` — имя приложения

### Маппинг ассоциаций в Inventory

Ассоциации ParamSet хранятся в файле:

```text
/environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
```

Структура:

```yaml
envTemplate:
  envSpecificParamsets:          # context: deployment
    <associatedObjectType>:
      - <paramSetName>
  envSpecificTechnicalParamsets: # context: runtime
    <associatedObjectType>:
      - <paramSetName>
  envSpecificE2EParamsets:        # context: pipeline
    <associatedObjectType>:
      - <paramSetName>
```

Где:

- `<associatedObjectType>` - `cloud` для Environment level, `<deployPostfix>` для Namespace/Application level
- `<paramSetName>` - имя ParamSet файла без расширения

## Валидация

TBD
<!-- ругаться при post когда передан app-level pipeline context -->

<!-- 
### Валидация структуры ParamSet

1. **Валидация атрибута `type`:**
   - `type` опционален, по умолчанию `"standard"`
   - Если указан, должен быть одним из: `"standard"` или `"ui-override"`
   - Если `type: "ui-override"`, имя файла должно соответствовать паттерну UI override парамсетов:
     - **Environment Level:**
       - Для deployment: `deploy-ui-override.yaml`
       - Для runtime: `runtime-ui-override.yaml`
       - Для pipeline: `pipeline-ui-override.yaml`
     - **Namespace Level:**
       - Для deployment: `<deployPostfix>-deploy-ui-override.yaml`
       - Для runtime: `<deployPostfix>-runtime-ui-override.yaml`
       - Pipeline context не поддерживается
     - **Application Level:**
       - Для deployment: `<deployPostfix>-<applicationName>-deploy-ui-override.yaml`
       - Для runtime: `<deployPostfix>-<applicationName>-runtime-ui-override.yaml`
       - Pipeline context не поддерживается
   - Имя ParamSet (поле `name` в YAML) должно совпадать с именем файла без расширения `.yaml`
   - Если `type: "standard"`, имя файла не должно соответствовать паттерну UI override парамсетов
   - Если имя файла соответствует паттерну UI override, но `type` не указан или `type: "standard"` - ошибка валидации
   - Если имя файла не соответствует паттерну UI override, но `type: "ui-override"` - ошибка валидации

2. **Для `level: environment` и `context: deployment|runtime|pipeline`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

3. **Для `level: namespace` и `context: deployment|runtime`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

4. **Для `level: application` и `context: deployment|runtime`:**
   - `parameters` должен быть пустым
   - `applications` обязателен и не пустой

### Валидация ассоциаций

1. `environmentId` должен существовать в репозитории
2. `associatedObjectType` должен быть валидным:
   - `"cloud"` - для Environment level
   - Существующий `deployPostfix` - для Namespace/Application level
3. `context` должен быть одним из: `deployment`, `runtime`, `pipeline`
4. Для Namespace/Application level context `pipeline` не поддерживается

добавить валидацию при удаление парамсета, что он проассоциирован "куда то еще" -->

## Управление версиями и конфликтами

TBD

<!-- ### Версионирование через Git

- `commitHash` ParamSet = Git commit hash последнего коммита файла
- Используется HTTP ETag для оптимистичной блокировки
- При каждом изменении создается новый коммит в Git

### Обработка конфликтов

1. **Оптимистичная блокировка:**
   - Клиент отправляет `If-Match` с ожидаемой версией
   - Сервер проверяет совпадение версий
   - При несовпадении возвращается `412 Precondition Failed`

2. **Конфликт при Git push:**
   - Если локальный коммит успешен, но push не удался (кто-то запушил раньше)
   - Откат локального коммита
   - Pull последних изменений
   - Возврат `409 Conflict` с текущей версией

3. **UI обработка конфликтов:**
   - При получении `412` или `409`:
     - Показать ошибку пользователю
     - Отобразить текущее содержимое из ответа
     - Предложить разрешить конфликт (merge или overwrite) -->
<!-- ругаться при post когда передан app-level pipeline context -->

<!-- 
### Валидация структуры ParamSet

1. **Валидация атрибута `type`:**
   - `type` опционален, по умолчанию `"standard"`
   - Если указан, должен быть одним из: `"standard"` или `"ui-override"`
   - Если `type: "ui-override"`, имя файла должно соответствовать паттерну UI override парамсетов:
     - **Environment Level:**
       - Для deployment: `deploy-ui-override.yaml`
       - Для runtime: `runtime-ui-override.yaml`
       - Для pipeline: `pipeline-ui-override.yaml`
     - **Namespace Level:**
       - Для deployment: `<deployPostfix>-deploy-ui-override.yaml`
       - Для runtime: `<deployPostfix>-runtime-ui-override.yaml`
       - Pipeline context не поддерживается
     - **Application Level:**
       - Для deployment: `<deployPostfix>-<applicationName>-deploy-ui-override.yaml`
       - Для runtime: `<deployPostfix>-<applicationName>-runtime-ui-override.yaml`
       - Pipeline context не поддерживается
   - Имя ParamSet (поле `name` в YAML) должно совпадать с именем файла без расширения `.yaml`
   - Если `type: "standard"`, имя файла не должно соответствовать паттерну UI override парамсетов
   - Если имя файла соответствует паттерну UI override, но `type` не указан или `type: "standard"` - ошибка валидации
   - Если имя файла не соответствует паттерну UI override, но `type: "ui-override"` - ошибка валидации

2. **Для `level: environment` и `context: deployment|runtime|pipeline`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

3. **Для `level: namespace` и `context: deployment|runtime`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

4. **Для `level: application` и `context: deployment|runtime`:**
   - `parameters` должен быть пустым
   - `applications` обязателен и не пустой

### Валидация ассоциаций

1. `environmentId` должен существовать в репозитории
2. `associatedObjectType` должен быть валидным:
   - `"cloud"` - для Environment level
   - Существующий `deployPostfix` - для Namespace/Application level
3. `context` должен быть одним из: `deployment`, `runtime`, `pipeline`
4. Для Namespace/Application level context `pipeline` не поддерживается

добавить валидацию при удаление парамсета, что он проассоциирован "куда то еще" -->

### Версионирование через Git

TBD

<!-- - `commitHash` ParamSet = Git commit hash последнего коммита файла
- Используется HTTP ETag для оптимистичной блокировки
- При каждом изменении создается новый коммит в Git

### Обработка конфликтов

1. **Оптимистичная блокировка:**
   - Клиент отправляет `If-Match` с ожидаемой версией
   - Сервер проверяет совпадение версий
   - При несовпадении возвращается `412 Precondition Failed`

2. **Конфликт при Git push:**
   - Если локальный коммит успешен, но push не удался (кто-то запушил раньше)
   - Откат локального коммита
   - Pull последних изменений
   - Возврат `409 Conflict` с текущей версией

3. **UI обработка конфликтов:**
   - При получении `412` или `409`:
     - Показать ошибку пользователю
     - Отобразить текущее содержимое из ответа
     - Предложить разрешить конфликт (merge или overwrite) -->

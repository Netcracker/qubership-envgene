# ParamSet API Design для Colly

- [ParamSet API Design для Colly](#paramset-api-design-для-colly)
  - [Введение](#введение)
  - [Требования](#требования)
  - [Контекст](#контекст)
    - [Факты о ParamSet в EnvGene](#факты-о-paramset-в-envgene)
    - [Структура ParamSet (YAML)](#структура-paramset-yaml)
    - [Ассоциация в Inventory](#ассоциация-в-inventory)
  - [Архитектура и объектная модель](#архитектура-и-объектная-модель)
    - [Объектная модель](#объектная-модель)
    - [API Endpoints](#api-endpoints)
      - [ParamSet](#paramset)
      - [Effective Set](#effective-set)
      - [Convenience endpoints](#convenience-endpoints)
  - [Детальное описание API](#детальное-описание-api)
    - [1. GET /api/v1/environments/{environmentId}/ui-parameters](#1-get-apiv1environmentsenvironmentidui-parameters)
    - [2. POST /api/v1/environments/{environmentId}/ui-parameters](#2-post-apiv1environmentsenvironmentidui-parameters)
    - [3. DELETE /api/v1/environments/{environmentId}/ui-parameters](#3-delete-apiv1environmentsenvironmentidui-parameters)
  - [Управление версиями и конфликтами **TBD**](#управление-версиями-и-конфликтами-tbd)
  - [Маппинг в Git репозиторий](#маппинг-в-git-репозиторий)
    - [Путь к файлу ParamSet](#путь-к-файлу-paramset)
    - [Маппинг ассоциаций в Inventory](#маппинг-ассоциаций-в-inventory)
  - [Чтение UI override ParamSet](#чтение-ui-override-paramset)
    - [Чтения UI override ParamSet с учетом ассоциаций окружения](#чтения-ui-override-paramset-с-учетом-ассоциаций-окружения)
      - [Определение `path`](#определение-path)
      - [Чтение одного UI override ParamSet файла](#чтение-одного-ui-override-paramset-файла)
  - [Валидация **TBD**](#валидация-tbd)

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
   - `/environments/parameters/<cluster-name>` - уровень кластера
   - `/environments/parameters/<cluster-name>/<env-name>` - уровень окружения

2. **Ассоциация к объектам:**
   - К Cloud - по зарезервированному слову `cloud`
   - К Namespace - по атрибуту `deployPostfix` неймспейса

3. **Контексты параметров:**
   - `deployment` - параметры для деплоя
   - `runtime` (technical) - параметры для рантайма
   - `pipeline` (e2e) - параметры для пайплайнов

4. **Множественная ассоциация:**
   - Один ParamSet может быть ассоциирован к нескольким окружениям/объектам/контекстам

5. **Идентификация окружения:**
   - `environmentId = <clusterName>/<environmentName>`

### Структура ParamSet (YAML)

```yaml
# Optional, deprecated
version: string
# Mandatory - имя парамсета, должно совпадать с именем файла
name: string
# Optional - тип парамсета (default: "standard")
# "standard" - обычный парамсет
# "ui-override" - UI override парамсет (параметры, измененные через UI)
type: enum[standard, ui-override]
# Mandatory - ключ-значение параметры
parameters: hashmap
# Optional - параметры уровня приложения
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

## Архитектура и объектная модель

Colly управляет как файлами ParamSet, так и их ассоциациями в Inventory.

- В Колли вводится объект ParamSet. Colly предоставляет CRUD операции над ParamSet.
- В Колли расширяется объект Environment - вводится атрибут `metadata.ParamSetAssociations`. Colly предоставляет CRUD операции над ParamSetAssociations в инвентори.
- Все атрибуты на верхнем уровне объекта ParamSet идентичны структуре YAML файла в Git репозитории. Метаданные, генерируемые/вычисляемые Colly (`id`, `commitHash`, `path`), вынесены в секцию `metadata`

### Объектная модель

```yaml
## ParamSet
name: string                                    # Имя парамсета (из YAML)
type: enum[ standard, ui-override]              # default: "standard" (из YAML)
parameters: map                                 # Параметры из YAML (ключ-значение)
applications:                                   # Параметры приложений
  - appName: string                             # Имя приложения
    parameters: map                             # Параметры приложения (ключ-значение)
metadata:                                       # Метаданные, генерируемые/вычисляемые Colly
  id: string                                    # UUID, генерируется Colly
  commitHash: string                            # Git commit hash последнего коммита файла (используется для ETag)
  path: string                                  # Путь к файлу в Git репозитории

## Environment
...
metadata:
  ...
  paramSetAssociations:                            # Список ассоциаций ParamSet с Environment
    - id: string                                   # UUID ассоциации, генерируется Colly
      associatedObjectType: string                 # "cloud" | deployPostfix
      context: enum[deployment, runtime, pipeline] #
      paramSetName: string                         # Имя парамсета для ассоциации
```

### API Endpoints

> [!NOTE]
> Endpoints для работы с ParamSet (`/api/v1/paramset/`) и ассоциациями (`/api/v1/environments/{environmentId}/paramset-associations`) в текущей версии реализовывать не планируется. Для работы с UI override параметрами используются convenience endpoints.

#### ParamSet

```text
GET    /api/v1/paramset/{paramsetId}
POST   /api/v1/paramset
PUT    /api/v1/paramset/{paramsetId}
DELETE /api/v1/paramset/{paramsetId}
```

#### Effective Set

```text
GET    /api/v1/environments/{environmentId}/paramset-associations
POST   /api/v1/environments/{environmentId}/paramset-associations
DELETE /api/v1/environments/{environmentId}/paramset-associations/{associationId}
```

#### Convenience endpoints

```text
GET      /api/v1/environments/{environmentId}/ui-parameters
POST     /api/v1/environments/{environmentId}/ui-parameters
DELETE   /api/v1/environments/{environmentId}/ui-parameters
```

---

## Детальное описание API

### 1. GET /api/v1/environments/{environmentId}/ui-parameters

Получить UI override параметры для окружения

> [!WARNING]
> время ответа должно быть менее 300 мс

**Параметры:**

- `environmentId` (path) - `cluster/env`
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)

**Ответы:**

- `200 OK` - Параметры найдены
  - Headers: `ETag: "<commit-hash>"`
  - Body: `map`
- `404 Not Found` - ParamSet не найден или ассоциация отсутствует

**Примеры запросов:**

```text
## Environment Level
GET /api/v1/environments/cluster-01/env-01/ui-parameters?context=deployment

## Namespace Level
GET /api/v1/environments/cluster-01/env-01/ui-parameters?context=deployment&namespaceName=env-01-core

## Application Level
GET /api/v1/environments/cluster-01/env-01/ui-parameters?context=deployment&namespaceName=env-01-core&applicationName=my-app
```

**Пример ответа:**

Общий для Environment, Namespace, Application Levels

```json
{
  
  "parameters": {
    "deployment": { // mandatory, default - {}
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": { // mandatory, default - {}
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": { // mandatory, default - {}
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

<!-- **Алгоритм:**

1. **Environment Level:**
   - Определить имя файла ParamSet: `<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<context>-ui-override`
   - Найти ParamSet по пути: `/environments/<environmentId>/Inventory/parameters/<context>-ui-override.yaml`
   - Проверить ассоциацию в `env_definition.yml` для `cloud`
   - Вернуть `parameters` из ParamSet

2. **Namespace Level:**
   - Найти `Namespace` по `environmentId` и `namespaceName`, получить `deployPostfix`
   - Определить имя файла ParamSet: `<deployPostfix>-<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<deployPostfix>-<context>-ui-override`
   - Найти ParamSet по пути: `/environments/<environmentId>/Inventory/parameters/<deployPostfix>-<context>-ui-override.yaml`
   - Проверить ассоциацию в `env_definition.yml` для `deployPostfix`
   - Вернуть `parameters` из ParamSet

3. **Application Level:**
   - Найти `Namespace` по `environmentId` и `namespaceName`, получить `deployPostfix`
   - Определить имя файла ParamSet: `<deployPostfix>-<applicationName>-<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<deployPostfix>-<applicationName>-<context>-ui-override`
   - Найти ParamSet по пути: `/environments/<environmentId>/Inventory/parameters/<deployPostfix>-<applicationName>-<context>-ui-override.yaml`
   - Проверить ассоциацию в `env_definition.yml` для `deployPostfix`
   - Найти в `applications` запись с `appName=<applicationName>`
   - Вернуть `applications[?appName=<applicationName>].parameters` из ParamSet -->

---

### 2. POST /api/v1/environments/{environmentId}/ui-parameters

Создать или обновить UI override параметры

**Параметры:**

- `environmentId` (path) - `cluster/env`
- `namespaceName` (query, optional) - Имя namespace (для Namespace/Application уровня)
- `applicationName` (query, optional) - Имя приложения (для Application уровня)
- `commitMessage` (body) - Коммит мессадж для коммита в энвген рпеозиторий
- `commitUser` (body) - Имя пользователя под которым происходит коммит
- `commitUserEmail` (body) - email пользователя под которым происходит коммит
- `parameters` (body)

> [!WARNING]
> создание парамсетов и ассоциаций должно быть транзакционной операцией

Когда в колли приходит пустой `parameters: {}` это является для Колли признаком что такой парамсет должен быть удален. В этом случае происходит как удаление соответствующего парамсета, так и удаление ассоциации

<!-- колли коммитит из под своего пользователя но "притворяясь  пользователем UI, тем которй передан в commitUser
проверить позволяет ли гит это и какой аттрибут нужно передать - только юзер нэйм или еще емэйл
добавить примеры комплексных вэлью - передавать в json ли yaml - Егор скажет как ему удобнее -->

**Пример запросов:**

**Environment Level:**

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "parameters": {
    "deployment": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Namespace Level:**

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "namespaceName": "env-01-core",
  "parameters": {
    "deployment": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

**Application Level:**

```json
{
  "commitMessage": "FAKE-0000",
  "commitUser": "Vasya A. Pupkin",
  "commitUserEmail": "Vasya@mail.com",
  "namespaceName": "env-01-core",
  "applicationName": "my-app",
  "parameters": {
    "deployment": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "runtime": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    },
    "pipeline": { // optional
      "KEY1": "value1",
      "KEY2": "value2"
    }
  }
}
```

<!-- **Логика определения уровня:**

- Если указаны `namespaceName` и `applicationName` → Application level
- Если указан только `namespaceName` → Namespace level
- Если не указаны → Environment level

**Примечания:**

- Имя ParamSet вычисляется автоматически на основе уровня и контекста
- Path вычисляется автоматически: `/environments/<environmentId>/Inventory/parameters/`
- Ассоциация добавляется автоматически в `env_definition.yml`
- Если ParamSet уже существует, параметры обновляются (merge)
- Операция транзакционная: либо создаются/обновляются ParamSet и ассоциация, либо откат -->

**Ответы:**

- `200 OK` - Параметры обновлены (если ParamSet существовал)
  - Headers: `ETag: "<commit-hash>"`
  - Body: `map` (запрос)
- `201 Created` - Параметры созданы (если ParamSet не существовал)
  - Headers: `ETag: "<commit-hash>"`
  - Body: `map` (запрос)
- `400 Bad Request` - Ошибка валидации
- `404 Not Found` - Environment, Namespace или Application не найден

<!-- **Пример ответа:**

```json
{
  "KEY1": "value1",
  "KEY2": "value2"
}
``` -->

<!-- **Алгоритм:**

1. **Environment Level:**
   - Определить имя файла ParamSet: `<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<context>-ui-override`
   - Создать/обновить ParamSet:
     - Path: `/environments/<environmentId>/Inventory/parameters/<context>-ui-override.yaml`
     - Content:

       ```yaml
       name: <context>-ui-override
       type: "ui-override"
       parameters: <parameters>
       applications: []
       ```

   - Добавить/обновить ассоциацию в `env_definition.yml` для `cloud`
   - Вернуть `parameters`

2. **Namespace Level:**
   - Найти `Namespace` по `environmentId` и `namespaceName`, получить `deployPostfix`
   - Определить имя файла ParamSet: `<deployPostfix>-<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<deployPostfix>-<context>-ui-override`
   - Создать/обновить ParamSet:
     - Path: `/environments/<environmentId>/Inventory/parameters/<deploy-postfix>-<context>-ui-override.yaml`
     - Content:

       ```yaml
       name: <deploy-postfix>-<context>-ui-override
       type: "ui-override"
       parameters: <parameters>
       applications: []
       ```

   - Добавить/обновить ассоциацию в `env_definition.yml` для `deployPostfix`
   - Вернуть `parameters`

3. **Application Level:**
   - Найти `Namespace` по `environmentId` и `namespaceName`, получить `deployPostfix`
   - Определить имя файла ParamSet: `<deployPostfix>-<applicationName>-<context>-ui-override.yaml`
   - Определить имя ParamSet (name в YAML): `<deployPostfix>-<applicationName>-<context>-ui-override`
   - Создать/обновить ParamSet:
     - Path: `/environments/<environmentId>/Inventory/parameters/<deploy-postfix>-<application-name>-<context>-ui-override.yaml`
     - Content:

       ```yaml
       name: <deploy-postfix>-<application-name>-<context>-ui-override
       type: "ui-override"
       parameters: {}
       applications:
         - appName: <applicationName>
           parameters: <parameters>
       ```

   - Добавить/обновить ассоциацию в `env_definition.yml` для `deployPostfix`
   - Вернуть `applications[?appName=<applicationName>].parameters` -->

### 3. DELETE /api/v1/environments/{environmentId}/ui-parameters

Решить будем ли использовать это в revert кэйсе

---

## Управление версиями и конфликтами **TBD**

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

---

## Маппинг в Git репозиторий

### Путь к файлу ParamSet

`path` - это атрибут в `metadata`, который содержит полный путь к файлу ParamSet в Git репозитории.

**Примеры путей:**

- **Стандартные ParamSet:**
  - Site level: `/environments/parameters/common-params.yaml`
  - Cluster level: `/environments/cluster-01/parameters/cluster-params.yaml`
  - Environment level: `/environments/cluster-01/env-01/Inventory/parameters/env-params.yaml`

- **UI Override ParamSet:**
  - Environment level: `/environments/cluster-01/env-01/Inventory/parameters/deploy-ui-override.yaml`
  - Namespace level: `/environments/cluster-01/env-01/Inventory/parameters/bss-deploy-ui-override.yaml`
  - Application level: `/environments/cluster-01/env-01/Inventory/parameters/bss-my-app-deploy-ui-override.yaml`

**Примечания:**

- Путь вычисляется Colly на основе расположения файла в Git репозитории
- Для стандартных ParamSet путь определяется по структуре `/environments/parameters/` с учетом уровня (site/cluster/environment)
- Для UI Override ParamSet путь всегда в `/environments/<environmentId>/Inventory/parameters/`
- Уникальность ParamSet определяется по полному пути, а не только по имени файла

### Маппинг ассоциаций в Inventory

Ассоциации хранятся в файле:

```text
environments/<cluster-name>/<env-name>/Inventory/env_definition.yml
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

**Порядок важен!** ParamSet применяются в порядке списка.

---

## Чтение UI override ParamSet

Эта операция используется во всех местах, где Colly читает UI override ParamSet (включая Effective Set API и UI-parameters API). Она включает как чтение ассоциаций окружения, так и чтение самих файлов ParamSet.

Идентификация UI override ParamSet выполняется по двум критериям:

1. **Имя файла** — используется для построения пути к файлу в Git репозитории. Контрактный нейминг обязателен
2. **Атрибут `type: "ui-override"`** — используется для валидации и подтверждения, что это действительно UI override парамсет

### Чтения UI override ParamSet с учетом ассоциаций окружения

Входные данные:

- `environmentId`
- `context` (`deployment`, `runtime`, `pipeline`)
- `namespaceName` (optional)
- `applicationName` (optional)

Шаги:

1. Определить `level`:
   1. Если не переданы ни `namespaceName`, ни `applicationName` -> Environment уровень
   2. Если передан `namespaceName`, но не `applicationName` -> Namespace уровень
   3. Если переданы `namespaceName` и `applicationName` -> Application уровень
2. Прочитать ассоциации ParamSet для окружения:
   - Прочитать файл `env_definition.yml` (см. раздел ["Маппинг ассоциаций в Inventory"](#маппинг-ассоциаций-в-inventory))
   - Для заданного `context` определить соответствующую секцию:
     - `envSpecificParamsets` — для `deployment`
     - `envSpecificTechnicalParamsets` — для `runtime`
     - `envSpecificE2EParamsets` — для `pipeline`
   - Для выбранного `level` определить `associatedObjectType`:
     - `cloud` — для Environment уровня
     - `<deployPostfix>` — для Namespace/Application уровней
   - Получить список ассоциированных ParamSet по этому `associatedObjectType` и `context`
3. Для каждого ассоциированного UI override ParamSet (в порядке перечисления в `env_definition.yml`):
   - Определить имя файла и [`path`](#определение-path)
   - Выполнить [Чтения одного UI override ParamSet файла](#чтение-одного-ui-override-paramset-файла)
   - Если файл найден и успешно прочитан:
     - Добавить его параметры в агрегированный результат (с учётом порядка в списке ассоциаций)

Результат:

```yaml
parameters: map
commitHashes: map
```

Этот результат содержит всю информацию, необходимую для:

- построения объектов `ParamSet` в Colly (по `path`, `parameters`, `applications`, `commitHash`)
- формирования и обновления секции `metadata.paramSetAssociations` в объекте `Environment` (по списку ассоциированных ParamSet и их `associatedObjectType`/`context` из `env_definition.yml`)

#### Определение `path`

Путь к файлу формируется по правилу `/environments/<environmentId>/Inventory/parameters/<имя-файла>`

Имя файла определяется как:

```text
контекст = deployment
  level = environment → deploy-ui-override.yaml
  level = namespace   → <deployPostfix>-deploy-ui-override.yaml
  level = application → <deployPostfix>-<applicationName>-deploy-ui-override.yaml

контекст = runtime
  level = environment → runtime-ui-override.yaml
  level = namespace   → <deployPostfix>-runtime-ui-override.yaml
  level = application → <deployPostfix>-<applicationName>-runtime-ui-override.yaml

контекст = pipeline
  level = environment → pipeline-ui-override.yaml
  level = namespace   → <deployPostfix>-pipeline-ui-override.yaml
  level = application → не поддерживается
```

Где:

- `<deployPostfix>` — значение из объекта Namespace (определяется по `namespaceName` и `environmentId`)
- `<applicationName>` — имя приложения из запроса

#### Чтение одного UI override ParamSet файла

Входные данные:

- `environmentId`
- `context` (`deployment`, `runtime`, `pipeline`)
- `level` (Environment, Namespace, Application)
- `namespaceName` (для `namespace`/`application` уровней)
- `applicationName` (для `application` уровня)
- `path`

Шаги:

1. Получить `commitHash` и содержимое файла
2. Если файл существует:
   - Проверить, что `type: "ui-override"` (если `type` не указан или `type: "standard"` — ошибка валидации)
   - Извлечь параметры:
     - Для Environment/Namespace уровней: из секции `parameters`
     - Для Application уровня: из секции `applications[?appName=<applicationName>].parameters`
   - Вернуть:

   ```yaml
   parameters: map       # Параметры UI override
   commitHash: string    # Git commit hash файла
   ```

3. Если файл не существует:
   - Вернуть «пустой» результат (параметры отсутствуют для данного уровня)

## Валидация **TBD**
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
       - Для pipeline: `<deployPostfix>-pipeline-ui-override.yaml`
     - **Application Level:**
       - Для deployment: `<deployPostfix>-<applicationName>-deploy-ui-override.yaml`
       - Для runtime: `<deployPostfix>-<applicationName>-runtime-ui-override.yaml`
       - Для pipeline: не поддерживается (pipeline параметры не могут быть на уровне application)
   - Имя ParamSet (поле `name` в YAML) должно совпадать с именем файла без расширения `.yaml`
   - Если `type: "standard"`, имя файла не должно соответствовать паттерну UI override парамсетов
   - Если имя файла соответствует паттерну UI override, но `type` не указан или `type: "standard"` - ошибка валидации
   - Если имя файла не соответствует паттерну UI override, но `type: "ui-override"` - ошибка валидации

2. **Для `level: environment` и `context: deployment|runtime`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

3. **Для `level: environment` и `context: pipeline`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

4. **Для `level: namespace` и `context: deployment|runtime`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

5. **Для `level: namespace` и `context: pipeline`:**
   - `parameters` обязателен и не пустой
   - `applications` должен быть пустым

6. **Для `level: application` и `context: deployment|runtime`:**
   - `parameters` должен быть пустым
   - `applications` обязателен и не пустой

7. **Для `level: application` и `context: pipeline`:**
   - Недопустимо (pipeline параметры не могут быть на уровне application)

### Валидация ассоциаций

1. `environmentId` должен существовать в репозитории
2. `associatedObjectType` должен быть валидным:
   - `"cloud"` - для Cloud объекта
   - Существующий `deployPostfix` - для Namespace
3. `context` должен быть одним из: `deployment`, `runtime`, `pipeline`
4. `level` должен соответствовать `context` (см. правила выше)

добавить валидацию при удаление парамсета, что он проассоциирован "куда то еще" -->

# Версионирование и обработка конфликтов

- [Версионирование и обработка конфликтов](#версионирование-и-обработка-конфликтов)
  - [Введение](#введение)
  - [Версионирование через Git](#версионирование-через-git)
    - [Commit Hash как версия](#commit-hash-как-версия)
    - [HTTP ETag](#http-etag)
  - [Сценарии конфликтов](#сценарии-конфликтов)
    - [Сценарий 1: Параллельные изменения через UI разными пользователями](#сценарий-1-параллельные-изменения-через-ui-разными-пользователями)
    - [Сценарий 2: Одновременное изменение через UI и Git](#сценарий-2-одновременное-изменение-через-ui-и-git)
    - [Сценарий 3: Конфликт при Git push](#сценарий-3-конфликт-при-git-push)
  - [Обработка конфликтов](#обработка-конфликтов)
    - [Оптимистичная блокировка (Optimistic Locking)](#оптимистичная-блокировка-optimistic-locking)
    - [Обработка конфликтов при Git push](#обработка-конфликтов-при-git-push)
  - [API детали](#api-детали)
    - [GET запросы](#get-запросы)
    - [POST запросы](#post-запросы)
    - [Коды ответов](#коды-ответов)
  - [UI обработка конфликтов](#ui-обработка-конфликтов)
    - [Сценарий: Получение 409 Conflict](#сценарий-получение-409-conflict)
    - [Сценарий: Получение 412 Precondition Failed](#сценарий-получение-412-precondition-failed)
  - [Примеры](#примеры)
    - [Пример 1: Успешное обновление с ETag](#пример-1-успешное-обновление-с-etag)
      - [Шаг 1: GET запрос](#шаг-1-get-запрос)
      - [Шаг 2: POST запрос с If-Match](#шаг-2-post-запрос-с-if-match)
    - [Пример 2: Конфликт версий (412)](#пример-2-конфликт-версий-412)
    - [Пример 3: Конфликт при Git push (409)](#пример-3-конфликт-при-git-push-409)

## Введение

Данный документ описывает механизмы версионирования и обработки конфликтов при работе с UI override параметрами через Colly API.

Для понимания UI Parameters API см. [colly-ui-parameters-api.md](./colly-ui-parameters-api.md).

## Версионирование через Git

### Commit Hash как версия

Каждое изменение UI override параметров создает новый commit в Git репозитории. Commit hash используется как версия ресурса.

- **Версия файла** = Git commit hash последнего коммита, изменившего этот файл
- Commit hash является уникальным идентификатором состояния файла
- При каждом изменении создается новый commit с новым hash

### HTTP ETag

Colly использует [HTTP ETag](https://datatracker.ietf.org/doc/html/rfc7232#section-2.3) для реализации оптимистичной блокировки:

- `ETag` header в GET ответе содержит commit hash файла
- `If-Match` header в POST запросе содержит ожидаемый commit hash
- Если версии не совпадают - операция отклоняется с кодом `412 Precondition Failed`

**Пример:**

```http
# GET запрос
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01

# Ответ
HTTP/1.1 200 OK
ETag: "a1b2c3d4e5f6"
Content-Type: application/json

{
  "parameters": {
    "param1": "value1"
  }
}
```

```http
# POST запрос с If-Match
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01
If-Match: "a1b2c3d4e5f6"

{
  "parameters": {
    "param1": "new_value"
  },
  "commitUser": "John Doe",
  "commitUserEmail": "john.doe@example.com"
}
```

## Сценарии конфликтов

### Сценарий 1: Параллельные изменения через UI разными пользователями

**Ситуация:**

1. Пользователь A и Пользователь B одновременно открывают UI и загружают параметры (GET запрос)
2. Оба получают одинаковую версию (ETag = `v1`)
3. Пользователь A изменяет параметр `param1` и сохраняет (POST с `If-Match: v1`)
4. Colly создает commit, новая версия = `v2`
5. Пользователь B изменяет параметр `param2` и пытается сохранить (POST с `If-Match: v1`)

**Результат:**

- POST запрос Пользователя B отклоняется с `412 Precondition Failed`
- Пользователь B должен обновить данные (GET запрос) и повторить изменения

### Сценарий 2: Одновременное изменение через UI и Git

**Ситуация:**

1. Пользователь A загружает параметры через UI (GET запрос, ETag = `v1`)
2. Администратор вручную редактирует файл UI override в Git и делает commit (новая версия = `v2`)
3. Пользователь A изменяет параметры в UI и пытается сохранить (POST с `If-Match: v1`)

**Результат:**

- POST запрос отклоняется с `412 Precondition Failed`
- Пользователь A должен обновить данные (GET запрос) и увидит изменения администратора

### Сценарий 3: Конфликт при Git push

**Ситуация:**

1. Colly получает POST запрос от Пользователя A
2. Colly создает локальный commit успешно (версия = `v2`)
3. Colly пытается выполнить push в remote репозиторий
4. Push отклоняется, т.к. кто-то другой уже запушил изменения в этот же файл

**Результат:**

- Colly откатывает локальный commit
- Colly выполняет pull последних изменений из remote
- Colly возвращает `409 Conflict` с текущей версией из remote
- Пользователь A должен повторить запрос с новыми данными

## Обработка конфликтов

### Оптимистичная блокировка (Optimistic Locking)

Colly использует оптимистичную блокировку для предотвращения конфликтов:

1. **Клиент читает данные:**
   - GET запрос возвращает данные + ETag (commit hash)
   - Клиент сохраняет ETag

2. **Клиент изменяет данные:**
   - POST запрос включает `If-Match` header с сохраненным ETag
   - Сервер проверяет совпадение версий

3. **Сервер валидирует версию:**
   - Если версии совпадают → операция выполняется
   - Если версии не совпадают → `412 Precondition Failed`

**Преимущества:**

- Не требует блокировок в БД или файловой системе
- Позволяет нескольким пользователям работать параллельно
- Конфликты обнаруживаются только при сохранении

### Обработка конфликтов при Git push

**Алгоритм:**

1. Colly получает POST запрос
2. Colly валидирует `If-Match` (если указан)
3. Colly создает локальный commit
4. Colly пытается выполнить push в remote:
   - **Успех:** commit hash включается в ответ, `200 OK` или `201 Created`
   - **Ошибка (кто-то запушил раньше):**
     1. Откатить локальный commit
     2. Выполнить pull из remote
     3. Получить актуальную версию файла
     4. Вернуть `409 Conflict` с текущими данными из remote

**Пример ответа 409 Conflict:**

```json
{
  "error": "Conflict",
  "message": "The resource has been modified by another user. Please reload and try again.",
  "currentVersion": {
    "commitHash": "f6e5d4c3b2a1",
    "parameters": {
      "param1": "value_from_remote",
      "param2": "value2"
    }
  }
}
```

## API детали

### GET запросы

**Response headers:**

```http
HTTP/1.1 200 OK
ETag: "<commit-hash>"
Content-Type: application/json
```

- `ETag` содержит commit hash последнего изменения UI override файла
- Клиент должен сохранить ETag для последующих POST запросов

### POST запросы

**Request headers (optional):**

```http
POST /api/v1/environments/{environmentId}/ui-parameters
If-Match: "<commit-hash>"
Content-Type: application/json
```

- `If-Match` содержит ожидаемый commit hash
- Если указан - Colly проверяет совпадение версий перед изменением
- Если не указан - изменения применяются без проверки версии (не рекомендуется)

**Response headers (успех):**

```http
HTTP/1.1 200 OK
ETag: "<new-commit-hash>"
Content-Type: application/json
```

- `ETag` содержит новый commit hash после сохранения
- Клиент должен обновить сохраненный ETag

### Коды ответов

| Код | Описание | Когда возникает |
|:----|:---------|:----------------|
| `200 OK` | Успешное обновление | POST запрос успешно обновил существующие параметры |
| `201 Created` | Успешное создание | POST запрос создал новые параметры (файл создан впервые) |
| `400 Bad Request` | Некорректный запрос | Отсутствуют обязательные параметры или некорректный формат |
| `404 Not Found` | Ресурс не найден | Namespace или Application не существуют |
| `409 Conflict` | Конфликт при Git push | Кто-то другой запушил изменения в файл раньше |
| `412 Precondition Failed` | Версия не совпадает | ETag из `If-Match` не совпадает с текущей версией файла |
| `422 Unprocessable Entity` | Ошибка валидации | Некорректные значения параметров |

## UI обработка конфликтов

### Сценарий: Получение 409 Conflict

**Шаги для UI:**

1. Показать сообщение пользователю  - Параметры были изменены другим пользователем. Ваши изменения не были сохранены.

2. Отобразить текущее содержимое из ответа (`currentVersion.parameters`)

3. Предложить пользователю варианты:
   - **Reload** - перезагрузить данные с сервера (выполнить GET запрос)
   - **Overwrite** - перезаписать изменения другого пользователя (повторить POST с новым ETag)
   - **Merge** - попытаться смержить изменения вручную

4. После выбора пользователя:
   - Если **Reload** - выполнить GET запрос, обновить UI
   - Если **Overwrite** - выполнить POST с ETag из `currentVersion.commitHash`
   - Если **Merge** - показать diff и позволить пользователю разрешить конфликты

### Сценарий: Получение 412 Precondition Failed

**Шаги для UI:**

1. Показать сообщение пользователю - Параметры были изменены. Пожалуйста, обновите данные.

2. Автоматически выполнить GET запрос для получения актуальных данных

3. Обновить UI с новыми данными

4. Предложить пользователю повторить изменения

## Примеры

### Пример 1: Успешное обновление с ETag

#### Шаг 1: GET запрос

```http
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01

HTTP/1.1 200 OK
ETag: "a1b2c3d4e5f6"
Content-Type: application/json

{
  "context": "deployment",
  "level": "application",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "ns-01",
  "applicationName": "app-01",
  "parameters": {
    "param1": "value1"
  }
}
```

#### Шаг 2: POST запрос с If-Match

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01
If-Match: "a1b2c3d4e5f6"
Content-Type: application/json

{
  "parameters": {
    "param1": "new_value",
    "param2": "value2"
  },
  "commitUser": "John Doe",
  "commitUserEmail": "john.doe@example.com"
}
```

**Ответ:**

```http
HTTP/1.1 200 OK
ETag: "f6e5d4c3b2a1"
Content-Type: application/json

{
  "status": "updated",
  "context": "deployment",
  "level": "application",
  "environmentId": "550e8400-e29b-41d4-a716-446655440000",
  "namespaceName": "ns-01",
  "applicationName": "app-01",
  "parameters": {
    "param1": "new_value",
    "param2": "value2"
  },
  "commitHash": "f6e5d4c3b2a1",
  "commitMessage": "Update UI override parameters for deployment/application",
  "commitUser": "John Doe",
  "commitUserEmail": "john.doe@example.com"
}
```

### Пример 2: Конфликт версий (412)

**Ситуация:** ETag устарел (кто-то уже изменил файл)

**POST запрос:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01
If-Match: "a1b2c3d4e5f6"
Content-Type: application/json

{
  "parameters": {
    "param1": "new_value"
  },
  "commitUser": "John Doe",
  "commitUserEmail": "john.doe@example.com"
}
```

**Ответ:**

```http
HTTP/1.1 412 Precondition Failed
ETag: "f6e5d4c3b2a1"
Content-Type: application/json

{
  "error": "Precondition Failed",
  "message": "The resource version does not match. Expected version: a1b2c3d4e5f6, actual version: f6e5d4c3b2a1",
  "expectedVersion": "a1b2c3d4e5f6",
  "actualVersion": "f6e5d4c3b2a1"
}
```

### Пример 3: Конфликт при Git push (409)

**Ситуация:** Локальный commit создан успешно, но push отклонен (кто-то запушил раньше)

**POST запрос:**

```http
POST /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/ui-parameters?context=deployment&level=application&namespaceName=ns-01&applicationName=app-01
If-Match: "a1b2c3d4e5f6"
Content-Type: application/json

{
  "parameters": {
    "param1": "new_value"
  },
  "commitUser": "John Doe",
  "commitUserEmail": "john.doe@example.com"
}
```

**Ответ:**

```http
HTTP/1.1 409 Conflict
ETag: "x9y8z7w6v5u4"
Content-Type: application/json

{
  "error": "Conflict",
  "message": "The resource has been modified by another user. Please reload and try again.",
  "currentVersion": {
    "commitHash": "x9y8z7w6v5u4",
    "parameters": {
      "param1": "value_from_another_user",
      "param2": "value2"
    }
  }
}
```

# Applications API для Colly

- [Applications API для Colly](#applications-api-для-colly)
  - [Введение](#введение)
  - [API Endpoints](#api-endpoints)
    - [GET /api/v1/environments/{environmentId}/applications](#get-apiv1environmentsenvironmentidapplications)
      - [Параметры](#параметры)
      - [Примеры запросов](#примеры-запросов)
      - [Ответы](#ответы)
      - [Логика обработки](#логика-обработки)
      - [Кэширование](#кэширование)

## Введение

Данный документ содержит описание API для получения списка приложений в окружении. Этот API используется UI для отображения выпадающего списка приложений при создании Application-level UI override параметров.

## API Endpoints

### GET /api/v1/environments/{environmentId}/applications

Отдает список имен приложений для заданного `environmentId` и `namespaceName`, полученные из SD, расположенного в:

```text
/environments/<cluster-name>/<env-name>/Inventory/solution-descriptor/sd.yaml|yml
```

#### Параметры

- `environmentId` (path, mandatory) - Environment uuid
- `namespaceName` (query, mandatory) - Имя Namespace

#### Примеры запросов

```text
GET /api/v1/environments/550e8400-e29b-41d4-a716-446655440000/applications?namespaceName=env-01-core
```

#### Ответы

- `200 OK` - Список приложений найден
  - Body: массив строк с именами приложений
- `200 OK` - Приложения не найдены
  - Body: `[]`
- `404 Not Found` - Namespace не найден или `deployPostfix` не определен

**Пример успешного ответа:**

```json
[
  "my-app-1",
  "my-app-2",
  "backend-service"
]
```

**Пример ответа при отсутствии приложений:**

```json
[]
```

#### Логика обработки

API работает с кэшированными данными Solution Descriptor. Кэш создается и обновляется по расписанию.

При получении запроса:

1. Проверить наличие валидного кэша SD для данного `environmentId`:
   - Если кэш существует и валиден → использовать данные из кэша
   - Если кэш отсутствует или невалиден → возврат пустого списка с warning в логах

2. Определение `deployPostfix` для namespace:
   - Найти `Namespace` объект по `namespaceName` и `environmentId`
   - Получить значение поля `deployPostfix` из `Namespace` объекта
   - Если `deployPostfix` не найден для `namespaceName` → `404 Not Found`

3. Получение списка приложений из кэша:
   - Отфильтровать приложения из кэшированного SD по совпадению `deployPostfix`
   - Если для данного `deployPostfix` не найдено ни одного приложения → возврат пустого списка
   - Вернуть список имен приложений

#### Кэширование

Colly кэширует информацию из Solution Descriptor. API работает исключительно с кэшированными данными, не читает SD файлы напрямую

**Создание и обновление кэша:**

- **По расписанию:**
  - Кэш обновляется автоматически каждые n минут для всех окружений
  - Процесс выполняется в фоне, независимо от API запросов

- **Процесс создания кэша:**
  1. Найти файл SD по пути (попытка `.yaml`, затем `.yml`)
  2. Если файл не найден → warning в логах, кэш не создается
  3. Валидация структуры SD:
     - Проверить наличие секции `applications`
     - Для каждого приложения проверить обязательные поля: `version`, `deployPostfix`
  4. Если валидация успешна → создать/обновить кэш

**Инвалидация кэша:**

- **При кэширование по расписанию:**
  - При ошибках валидации SD (отсутствие обязательных полей `version`, `deployPostfix`)
  - При отсутствии секции `applications` в SD
  - Действие: кэш для данного окружения полностью удаляется, warning в логах
  - При следующем periodic sync SD будет прочитан и провалидирован заново

# UI Override

## Концепция

UI Override - это механизм переопределения параметров Effective Set через UI, который:

- Применяется Calculator при генерации Effective Set
- Имеет приоритет выше ParamSet'ов и Predefined parameters, но ниже Custom Params
- Поддерживает контексты ES (deployment/runtime/pipeline)
- Хранится в трех файлах (по одному на контекст)

## Разделение ответственности

### UI Override Object

**Расположение в репозитории:**

```text
environments/
  <cluster>/
    <environment>/
      ui-overrides/
        deployment.yaml       # Deployment контекст
        runtime.yaml          # Runtime контекст
        pipeline.yaml         # Pipeline контекст
```

**Пример: `ui-overrides/deployment.yaml`**

```yaml
# Environment уровень (применяется ко всем namespace и application)
environment:
  param_env1: value1
  param_env2: value2

# Namespace уровень (применяется ко всем application в namespace)
namespaces:
  namespace-01:  # deployPostfix из Namespace объекта
    param_ns1: value1
    param_ns2: value2
  namespace-02:  # deployPostfix из Namespace объекта
    param_ns3: value3

# Application уровень (применяется к конкретному application)
applications:
  namespace-01:  # deployPostfix из Namespace объекта
    app-01:      # applicationName
      param1: value2
      param4: null        # Удаление параметра
    app-02:
      param5: value5
  namespace-02:  # deployPostfix из Namespace объекта
    app-03:
      param6: value6
```

**Пример: `ui-overrides/runtime.yaml`**

```yaml
environment:
  runtime_env_param1: value1

namespaces:
  namespace-01:  # deployPostfix из Namespace объекта
    runtime_ns_param1: value2

applications:
  namespace-01:  # deployPostfix из Namespace объекта
    app-01:      # applicationName
      runtime_param1: value1
      runtime_param2: value2
```

**Пример: `ui-overrides/pipeline.yaml`**

```yaml
environment:
  pipeline_param1: value1
  pipeline_param2: value2

namespaces:
  namespace-01:  # deployPostfix из Namespace объекта (если нужны namespace-specific параметры для pipeline)
    pipeline_ns_param1: value3
```

> [!NOTE]
> В качестве ключей в секциях `namespaces` и `applications` используется `deployPostfix` 
> из соответствующего Namespace объекта, а не `namespaceName`. Это обеспечивает 
> уникальность и консистентность с Effective Set структурой.

---

### Calculator

**Инпуты:**

1. те что сейчас
2. **UI Override Object** - Calculator ищет UI Override файлы по контрактному пути `<envs-path>/ui-overrides/` (опционально, если директория не существует - пропускается)

**Что делает:**

1. Генерирует ES (как и сейчас)
2. Если UI Override Object существует - применяет оверрайды и сохраняет файл `ui-override-original-values.yaml` для UI override параметров

**Приоритет мержа (низкий → высокий):**

```text
...
- UI Override (environment level)      ← НОВОЕ (опционально)
- UI Override (namespace level)        ← НОВОЕ (опционально)
- UI Override (application level)      ← НОВОЕ (опционально)
- Custom Params (--custom-params)     ← highest priority
```

**Аутпут в Git:**

```text
effective-set/
  ui-override-original-values.yaml                    # originalValue для всех контекстов (новое)
```

**Формат файла:**

```yaml
# ui-override-original-values.yaml
deployment:
  namespace-01:
    app-01:
      param1: value1       # Значение до UI override
      param3: null         # Новый параметр (не было в ES)
      param4: value4       # Параметр удален через UI override
    app-02:
      param5: null

runtime:
  namespace-01:
    app-01:
      runtime_param1: old_value1
      runtime_param2: old_value2

pipeline:
  pipeline_param1: old_value
```

**Пример вызова Calculator:**

```bash
calculator --env-id cluster/env \
           --envs-path /environments/cluster/env \
           --output /environments/cluster/env/effective-set
```

Calculator автоматически ищет UI Override файлы по пути `<envs-path>/ui-overrides/`. Если директория существует - применяет оверрайды, если нет - пропускает этот шаг.

---

### Colly

**Читает из Git:**

1. `ES` - Effective Set
2. `UI_OVERRIDE_ORIGINAL_VALUES` - файл original values до UI override
3. `UI_OVERRIDE` - UI Override файлы
4. `request.parameters` - незакоммиченные изменения из UI (HTTP request body)

**Вычисляет для каждого параметра:**

#### 1. `originalValue`

Значение параметра до применения UI Override:

- Если параметр есть в `ui-override-original-values.yaml` → берем значение из этого файла
- Иначе → берем значение из текущего ES (параметр не был переопределен через UI)

#### 2. `state`

Состояние параметра относительно UI Override:

- `ui_override_uncommitted` - параметр изменен в UI, но не закоммичен (есть в `request.parameters`, но отличается от `ui-overrides/*.yaml`)
- `ui_override_committed` - параметр закоммичен в Git (есть в `ui-overrides/*.yaml`, или был удален из UI после коммита)
- `ui_override_untouched` - параметр отсутствует в `request.parameters` и в `ui-overrides/*.yaml`

#### 3. `value`

Целевое значение параметра:

- Если параметр изменен в UI (есть в `request.parameters`) → берем значение из `request.parameters`
- Иначе, если параметр есть в `ui-overrides/*.yaml` → берем значение из UI Override
- Иначе → берем значение из ES

**Отдает в API response:**

- `value` - целевое значение (что будет в ES после коммита)
- `state` - состояние параметра (unchanged/staged/committed)
- `originalValue` - значение до UI override

---

## Реализация

Calculator

1. Реализовать поиск UI Override файлов по контрактному пути `<envs-path>/ui-overrides/`:
   - `deployment.yaml` для deployment контекста
   - `runtime.yaml` для runtime контекста
   - `pipeline.yaml` для pipeline контекста
2. Если директория `ui-overrides/` не существует - пропустить этот шаг (UI Override опционален)
3. Если UI Override файлы найдены:
   1. Применять UI Override с приоритетом ниже --custom-params
   2. Генерировать единый файл `effective-set/ui-override-original-values.yaml` для deploy, pipeline, runtime контекстов (запоминать originalValue перед применением UI Override)

Colly

1. Читать UI Override файлы из Git (deployment.yaml, runtime.yaml, pipeline.yaml)
   1. Парсить структуру `environment / namespaces / applications`
2. Читать `effective-set/ui-override-original-values.yaml`
3. Вычислять state на основе request.parameters, UI Override, UI_OVERRIDE_ORIGINAL_VALUES
4. Вычислять value и originalValue
5. API для коммита request.parameters → UI Override файлы в Git

Подробнее см.:

- [colly-effective-set-api.md](./colly-effective-set-api.md) - API для работы с Effective Set
- [colly-ui-parameters-api.md](./colly-ui-parameters-api.md) - API для работы с UI override файлами
- [colly-versioning-conflicts.md](./colly-versioning-conflicts.md) - Версионирование и конфликты

UI

1. Отправлять все параметры (включая закоммиченные) в request.parameters
2. Отображать state, value, originalValue для пользователя

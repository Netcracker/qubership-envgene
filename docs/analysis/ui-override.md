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
  namespace-01:
    param_ns1: value1
    param_ns2: value2
  namespace-02:
    param_ns3: value3

# Application уровень (применяется к конкретному application)
applications:
  namespace-01:
    app-01:
      param1: value2
      param4: null        # Удаление параметра
    app-02:
      param5: value5
  namespace-02:
    app-03:
      param6: value6
```

**Пример: `ui-overrides/runtime.yaml`**

```yaml
environment:
  runtime_env_param1: value1

namespaces:
  namespace-01:
    runtime_ns_param1: value2

applications:
  namespace-01:
    app-01:
      runtime_param1: value1
      runtime_param2: value2
```

**Пример: `ui-overrides/pipeline.yaml`**

```yaml
environment:
  pipeline_param1: value1
  pipeline_param2: value2
```

---

### Calculator

**Инпуты:**

1. те что сейчас
2. **UI Override Object** (новый параметр `--ui-overrides-path`)

**Что делает:**

1. Генерирует ES (как и сейчас)
2. Сохраняет метафайл для UI override параметров

**Приоритет мержа (низкий → высокий):**

```text
1. Template defaults
2. ParamSet (environment level)
3. ParamSet (namespace level)
4. ParamSet (application level)
5. SBOM parameters
6. Predefined parameters
7. UI Override (environment level)      ← НОВОЕ
8. UI Override (namespace level)        ← НОВОЕ
9. UI Override (application level)      ← НОВОЕ
10. Custom Params (--custom-params)     ← highest priority
```

**Аутпут в Git:**

```text
effective-set/
  ui-metadata.yaml                    # Метаданные для всех контекстов (новое)
```

**Формат метафайла:**

```yaml
# ui-metadata.yaml
deployment:
  namespace-01:
    app-01:
      param1:
        originalValue: value1       # Значение до UI override
      param3:
        originalValue: null         # Новый параметр (не было в ES)
      param4:
        originalValue: value4       # Параметр удален через UI override
    app-02:
      param5:
        originalValue: null

runtime:
  namespace-01:
    app-01:
      runtime_param1:
        originalValue: old_value1
      runtime_param2:
        originalValue: old_value2

pipeline:
  pipeline_param1:
    originalValue: old_value
```

**Новый параметр Calculator:**

```bash
calculator --env-id cluster/env \
           --envs-path /environments/cluster/env \
           --ui-overrides-path /environments/cluster/env/ui-overrides \
           --output /environments/cluster/env/effective-set
```

---

### Colly

**Читает из Git:**

1. `ES` - Effective Set
2. `UI_METADATA` - метафайл
3. `UI_OVERRIDE` - UI Override файлы
4. `request.parameters` - незакоммиченные изменения из UI (HTTP request body)

**Вычисляет для каждого параметра:**

#### 1. `originalValue`

Значение параметра до применения UI Override:

- Если параметр есть в `ui-metadata.yaml` → берем `originalValue` из метафайла
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

1. Добавить параметр `--ui-overrides-path`
2. Реализовать чтение UI Override файлов:
   - `deployment.yaml` для deployment контекста
   - `runtime.yaml` для runtime контекста
   - `pipeline.yaml` для pipeline контекста
3. Запоминать originalValue перед применением UI Override
4. Применять UI Override с приоритетом выше Predefined parameters
5. Генерировать единый метафайл `effective-set/ui-metadata.yaml` для всех контекстов

Colly

1. Читать UI Override файлы из Git (deployment.yaml, runtime.yaml, pipeline.yaml)
   1. Парсить структуру `environment / namespaces / applications`
2. Читать `effective-set/ui-metadata.yaml`
3. Вычислять state на основе request.parameters, UI Override, UI Metadata
4. Вычислять value и originalValue
5. API для коммита request.parameters → UI Override файлы в Git

UI

1. Отправлять все параметры (включая закоммиченные) в request.parameters
2. Отображать state, value, originalValue для пользователя

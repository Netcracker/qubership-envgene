# Override UI

- [Override UI](#override-ui)
  - [Problem Statement](#problem-statement)
  - [Scenarios](#scenarios)
  - [Use Cases](#use-cases)
  - [Open Questions](#open-questions)
  - [Proposed Approach](#proposed-approach)
    - [EnvGene](#envgene)
      - [Option 1. Env Specific Parameters Override](#option-1-env-specific-parameters-override)
        - [Option 1A. Базовый вариант](#option-1a-базовый-вариант)
        - [Option 1B. Расширенный вариант](#option-1b-расширенный-вариант)
      - [Option 2. Env Instance Override](#option-2-env-instance-override)
      - [Option 3. Effective Set Override](#option-3-effective-set-override)
      - [Option 4. UI Override Files (Simplified Approach)](#option-4-ui-override-files-simplified-approach)
      - [Сравнение Опций](#сравнение-опций)
  - [API документация](#api-документация)

## Problem Statement

1. **Нам удобнее в UI**

   Работа через Git требует определенных навыков и привычек. Для пользователей, которые привыкли работать через UI, это может вызывать неудобство и отторжение.

2. **EnvGene сложный**

   EnvGene содержит большое количество разнообразных [объектов](/docs/envgene-objects.md), которые необходимы для реализации различных сценариев использования. Пользователь должен изучить и понять эти объекты, чтобы выполнять даже простые действия, такие как изменение одного параметра, что создает высокий барьер входа для новых пользователей и требует значительного времени на изучение системы.

3. **Поменять один параметр долго**

   Изменение параметра в EnvGene занимает определенное время: checkout репозитория, изменение YAML-файла в Git, push в удаленный репозиторий. В сценариях разработки, когда разработчик работает с одним окружением, проводит dev-тест и требуются частые изменения параметров, текущий подход по работе с параметрами приносит значительные накладные расходы — изменение одного параметра занимает длительное время, что приводит к потере времени разработчика.

## Scenarios

1. **Dev/QA Test**

   Разработчик/QA или группа разработчиков/QA получили развернутое в облаке окружение для тестирования изменений.

   В процессе отладки и тестирования требуется многократный редеплой отдельных приложений с изменением их параметров в CM для достижения корректной работы функциональности.

   Полученные в результате отладки и тестирования изменения параметров требуют сохранения в шаблоне окружения для воспроизводимости в будущих окружениях и использования в других инстансах.

2. **"Озеленение" CI окружения**

   После упавших автотестов при автоматизированном деплое солюшена в CI окружение, QA инженер вносит в этот солюшен фиксы/хот-фиксы для достижения успешного прохождения тестов.

   Процесс включает многократный редеплой отдельных приложений, что требует изменения параметров этих приложений в CM.

   Полученные в результате отладки и тестирования изменения параметров требуют сохранения в шаблоне окружения для воспроизводимости в будущих окружениях и использования в других инстансах.

## Use Cases

1. Create override.
   1. Add a new parameter to:
      1. Deployment context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      2. Runtime context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      3. Pipeline context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to a specific namespace)
   2. Override a parameter value for:
      1. Deployment context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      2. Runtime context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      3. Pipeline context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to a specific namespace)
   3. ~~Remove a parameter~~
2. View override parameters for:
   1. Deployment context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to all applications in the namespace)
      3. Application level (applies to a specific application)
   2. Runtime context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to all applications in the namespace)
      3. Application level (applies to a specific application)
   3. Pipeline context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to a specific namespace)
3. Update override
   1. Add a new parameter to:
      1. Deployment context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      2. Runtime context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      3. Pipeline context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to a specific namespace)
   2. Override a parameter value for:
      1. Deployment context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      2. Runtime context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      3. Pipeline context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to a specific namespace)
   3. Remove a parameter value for:
      1. Deployment context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      2. Runtime context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to all applications in the namespace)
         3. Application level (applies to a specific application)
      3. Pipeline context:
         1. Environment level (applies to all namespaces in the environment)
         2. Namespace level (applies to a specific namespace)
4. Delete override for
   1. Deployment context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to all applications in the namespace)
      3. Application level (applies to a specific application)
   2. Runtime context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to all applications in the namespace)
      3. Application level (applies to a specific application)
   3. Pipeline context:
      1. Environment level (applies to all namespaces in the environment)
      2. Namespace level (applies to a specific namespace)
5. View Effective Set
   1. Deployment context on Application level
   2. Runtime context on Application level
   3. Pipeline context on Environment level
6. View "to-be" Effective Set
   1. Deployment context on Application level
   2. Runtime context on Application level
   3. Pipeline context on Environment level
7. View Effective Set generation date

## Open Questions

1. Необходимо ли обрабатывать часть UI оверрайд параметров как сенсетив параметры - энкриптить при сохранение в репозиторий?
   1. Нет
2. Нужен ли UI оверрайд параметров из DD?
   1. Нет
3. Как очищать инвентори от UI оверрайдов при "сдаче" энва?
   1. через удаление и создание
4. Какой процесс сохранения параметров полученных в Dev/QA Test и "Озеленение" CI окружения в энв темплейте
   1. OoS для этого анализа
5. Для ui парамсетов вводятся ограничения на структуру контента парамсета. EnvGene про эти ограничения  не знает. Что может привести к тому, что параметры на UI и в envgene разойдутся
   1. **решение: поддержать ограничения и в энвгене (?)**
   2. решение: дополнительные точки ассоциации в инвентори (?)
6. Типизация через нейминг это плохо?
   1. типизация через тип позволит описать правила валидации через JSON схему
7. ParamSet или ParamSet + ParamSetAssociation ?
   1. Парамсет + атттрибуты энва
8. Как получить sha коммита, который изменял конкретный файл
9. описать про ошибку при пересечение ключей файликов эфектив сета
10. описать принцип мержа в Колли с учетом
    1. того что ключи не должны пересекаться
    2. есть исключения типа `global`
11. Что делать когда заинкрипчено и есть `sops` секция
12. дата генерации эффектив сета

## Proposed Approach

Решение предоставляет UI для быстрого изменения параметров окружения без необходимости работы с Git напрямую. UI оверрайды сохраняются в инстансном репозитории и применяются с наивысшим приоритетом в цепочке парамсетов.

Предложено три варианта реализации, различающиеся местом хранения оверрайдов и временем их применения. Все варианты обеспечивают возможность последующего переноса изменений в шаблон окружения для воспроизводимости.

![override-ui-arch.png](/docs/images/override-ui-arch.png)

![override-ui-prototype.html](/docs/analysis/override-ui-prototype.html)

![override-ui-options.png](/docs/images/override-ui-options.png)

### EnvGene

#### Option 1. Env Specific Parameters Override

Оверрайды хранятся исключительно в отдельных ParamSet файлах в инстансном репозитории. ParamSet файлы ассоциируются с окружением через Inventory и применяются последними в цепочке параметров, обеспечивая наивысший приоритет. Применение изменений требует выполнения `env_build` и `generate_effective_set`.

##### Option 1A. Базовый вариант

**Уровни оверрайдов:**

- **Deployment и Runtime контексты:** оверрайды задаются только на уровне Application
- **Pipeline контекст:** оверрайды задаются только на уровне Environment (применяются ко всем NS окружения)

1. При создание UI оверрайда значения сохраняются в инстансном репозитории в виде Env Specific ParamSets

   1. парамсеты создается в `/environments/<cluster>/<env>/Inventory/parameters/` отдельно для каждого нс/контекста c именами:
      1. для `deployment` контекста: `<deploy-postfix>-deploy-ui-override.yaml`
      2. для `runtime` контекста: `<deploy-postfix>-runtime-ui-override.yaml`
      3. для `pipeline` контекста: `pipeline-ui-override.yaml`

   2. парамсет ассоциируется в инвентори энва:
      1. парамсет добавляется в конец списка парамсетов в текущие точки ассоциации

            ```yaml
            envTemplate:
               envSpecificParamsets:
                  <deploy-postfix>:
                     - ...
                     - <deploy-postfix>-deploy-ui-override
               envSpecificTechnicalParamsets:
                  <deploy-postfix>:
                     - ...
                     - <deploy-postfix>-runtime-ui-override
               envSpecificE2EParamsets:
                  # For all NSs of the Env
                  <deploy-postfix>:
                     - ...
                     - pipeline-ui-override
            ```

      2. Во время `env_build` происходит валидация:
         - UI override парамсеты (с именем файла соответствующим паттерну `*-ui-override.yaml`) должны быть в конце списка - если нет, падает
      3. Во время `env_inventory_generation` (или в первой джобе?) происходит валидация, что создаются или изменяются ui-override парамсеты - если да, падает

   3. парамсеты имеют следующую структуру:
      1. для `deployment` и `runtime` контекста:

            ```yaml
            name: string
            parameters: <>
            applications:
               - appName: string
                 parameters: map
            ```

      2. для `pipeline` контекста: `pipeline-ui-override.yaml`

            ```yaml
            name: string
            parameters: map
            applications: []
            ```

   4. В BGD кейсе вместо `<deploy-postfix>` используется `<deploy-postfix>-peer|origin`. Для процессинга этой конструкции используется BG Domain объект.

2. Для отображения сохраненного UI оверрайда используется парамсет

3. UI оверрайд может содержать макросы ссылки на креды созданные в гите

4. Возможность создавать креды не предоставляется. Работа с заинкрипченным репозиторием не поддерживается
   1. **Assumption**: В тех репозиториях/сайтах где используется Override UI энкрипт репозитория не требуется

##### Option 1B. Расширенный вариант

**Уровни оверрайдов:**

- **Deployment и Runtime контексты:** оверрайды могут быть заданы на уровне Environment, Namespace или Application
- **Pipeline контекст:** оверрайды могут быть заданы на уровне Environment или Namespace

1. При создание UI оверрайда значения сохраняются в инстансном репозитории в виде Env Specific ParamSets

   1. парамсеты создается в `/environments/<cluster>/<env>/Inventory/parameters/` отдельно для каждого уровня/контекста c именами:
      1. Для deployment и runtime контекстов:
         1. На уровне Environment: `deploy-ui-override.yaml` / `runtime-ui-override.yaml` (через секцию `parameters`)
         2. На уровне Namespace: `<deploy-postfix>-deploy-ui-override.yaml` / `<deploy-postfix>-runtime-ui-override.yaml` (через секцию `parameters`)
         3. На уровне Application: `<deploy-postfix>-<application-name>-deploy-ui-override.yaml` / `<deploy-postfix>-<application-name>-runtime-ui-override.yaml` (через секцию `applications`)
      2. Для pipeline контекста:
         1. На уровне Environment: `pipeline-ui-override.yaml`
         2. На уровне Namespace: `<deploy-postfix>-pipeline-ui-override.yaml`

   2. парамсет ассоциируется в инвентори энва:
      1. парамсет добавляется в конец списка парамсетов в соответствующие точки ассоциации:

            ```yaml
            envTemplate:
               envSpecificParamsets:
                  cloud:
                     - ...
                     - deploy-ui-override
                  <deploy-postfix>:
                     - ...
                     - <deploy-postfix>-deploy-ui-override
                     - <deploy-postfix>-<application-name>-deploy-ui-override
               envSpecificTechnicalParamsets:
                  cloud:
                     - ...
                     - runtime-ui-override
                  <deploy-postfix>:
                     - ...
                     - <deploy-postfix>-runtime-ui-override
                     - <deploy-postfix>-<application-name>-runtime-ui-override
               envSpecificE2EParamsets:
                  cloud:
                     - ...
                     - pipeline-ui-override
                  <deploy-postfix>:
                     - ...
                     - <deploy-postfix>-pipeline-ui-override
            ```

      2. Во время `env_build` происходит валидация:
         - UI override парамсеты (с именем файла соответствующим паттерну `*-ui-override.yaml`) должны быть в конце списка - если нет, падает
      3. Во время `env_inventory_generation` (или в первой джобе?) происходит валидация, что создаются или изменяются ui-override парамсеты - если да, падает

   3. парамсеты имеют следующую структуру в зависимости от уровня:
      1. Deployment и Runtime контексты:

         1. На уровне Environment:

               ```yaml
               name: deploy-ui-override  # или runtime-ui-override
               parameters: map  # Параметры уровня Environment
               applications: []  # Пусто, т.к. параметры на уровне Environment
               ```

         2. На уровне Namespace:

               ```yaml
               name: <deploy-postfix>-deploy-ui-override  # или <deploy-postfix>-runtime-ui-override
               parameters: map  # Параметры уровня Namespace
               applications: []  # Пусто, т.к. параметры на уровне Namespace
               ```

         3. На уровне Application:

               ```yaml
               name: <deploy-postfix>-<application-name>-deploy-ui-override  # или <deploy-postfix>-<application-name>-runtime-ui-override
               parameters: {}  # Пусто, т.к. параметры на уровне Application
               applications:
                  - appName: string
                    parameters: map  # Параметры уровня Application
               ```

      2. Pipeline контекст:

         1. На уровне Environment:

               ```yaml
               name: pipeline-ui-override
               parameters: map  # Параметры уровня Environment
               applications: []  # Пусто
               ```

         2. На уровне Namespace:

               ```yaml
               name: <deploy-postfix>-pipeline-ui-override
               parameters: map  # Параметры уровня Namespace
               applications: []  # Пусто
               ```

   4. В BGD кейсе для уровня Namespace и Application вместо `<deploy-postfix>` используется `<deploy-postfix>-peer|origin`. Для процессинга этой конструкции используется BG Domain объект. Для уровня Environment BGD не применяется (параметры на уровне Environment общие для всего окружения).

2. Для отображения сохраненного UI оверрайда используется парамсет

3. UI оверрайд может содержать макросы ссылки на креды созданные в гите

4. Возможность создавать креды не предоставляется. Работа с заинкрипченным репозиторием не поддерживается
   1. **Assumption**: В тех репозиториях/сайтах где используется Override UI энкрипт репозитория не требуется

#### Option 2. Env Instance Override

Расширяет Option 1A или Option 1B дополнительным мержем оверрайдов напрямую в Application и Namespace объекты инстансного репозитория. Оверрайды хранятся в двух местах: ParamSet файлах (как в Option 1A/1B) и в Application/Namespace объектах. Применение изменений требует только `generate_effective_set`, что ускоряет процесс по сравнению с Option 1A/1B.

1. Все то же самое что и в **Option 1A** или **Option 1B**
2. При создание UI оверрайда значения мержатся в режиме Shallow Merge в Application энвайрмента:
   1. для `deploy` в аттрибут `deployParameters` Application объекта расположенного в `environments/<cluster>/<env>/Namespaces/<ns>/Applications/<app>.yml`
   2. для `runtime` в аттрибут `technicalConfigurationParameters` Application объекта расположенного в `environments/<cluster>/<env>/Namespaces/<ns>/Applications/<app>.yml`
   3. для `pipeline` в аттрибут `e2eParameters` во все Namespace объекты энвайрмента, расположенные в `environments/<cluster>/<env>/namespace.yml`

#### Option 3. Effective Set Override

Расширяет Option 2 дополнительным мержем оверрайдов напрямую в файлы Effective Set. Оверрайды хранятся в трех местах: ParamSet файлах, Application/Namespace объектах и файлах Effective Set. Изменения могут быть применены мгновенно.

1. Все то же самое что и в **Option 2. Env Instance Override**
2. При создание UI оверрайда значения мержатся в режиме Shallow Merge в файлы ES:
   1. для `deploy` в `effective-set/deployment/<ns>/<app>/values/deployment-parameters.yaml`
   2. для `runtime` в `effective-set/runtime/<ns>/<app>/parameters.yaml`
   3. для `pipeline` в `effective-set/pipeline/parameters.yaml`

#### Option 4. UI Override Files (Simplified Approach)

Оверрайды Effective Set хранятся в отдельной директории `ui-overrides/` в трех файлах (по одному на контекст). Файлы UI override создаются и управляются исключительно Colly через API. Calculator применяет UI override напрямую при генерации ES с приоритетом ниже Custom Params. Генерируется файл `ui-override-original-values.yaml` для отслеживания оригинальных значений параметров до применения UI override.

**Структура хранения:**

```text
environments/
  <cluster>/
    <environment>/
      ui-overrides/
        deployment.yaml       # Deployment контекст
        runtime.yaml          # Runtime контекст
        pipeline.yaml         # Pipeline контекст
```

**Уровни оверрайдов:**

- **Environment Level** - параметры применяются ко всем namespace и application в окружении
- **Namespace Level** - параметры применяются ко всем application в namespace
- **Application Level** - параметры применяются к конкретному application

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

**Calculator изменения:**

1. Calculator читает UI Override файлы, расположенные в контрактном пути:
   - `deployment.yaml` для deployment контекста
   - `runtime.yaml` для runtime контекста
   - `pipeline.yaml` для pipeline контекста

2. Calculator мержит их в Effective Set при каждой генерации с приоритетом ниже чем Custom Params

3. Calculator генерирует файл `ui-override-original-values.yaml` с оригинальными значениями параметров до применения UI override:

   ```text
   effective-set/
     ui-override-original-values.yaml    # originalValue для всех контекстов
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

**Colly изменения:**

Colly предоставляет REST API для работы с UI override параметрами и Effective Set.

1. **UI Parameters API** - управление UI override файлами:
   - `GET /api/v1/environments/{environmentId}/ui-parameters` - получение UI override параметров
   - `POST /api/v1/environments/{environmentId}/ui-parameters` - создание/обновление UI override параметров (коммит в Git)
   - Детали: [colly-ui-parameters-api.md](./colly-ui-parameters-api.md)

2. **Effective Set API** - получение ES с метаданными:
   - Colly вычисляет для каждого параметра три атрибута:
     - `originalValue` - значение до применения UI Override
     - `state` - состояние параметра (uncommitted/committed/untouched)
     - `value` - целевое значение параметра
   - Детали: [colly-effective-set-api.md](./colly-effective-set-api.md)

3. **Версионирование и конфликты**:
   - Использование Git commit hash и HTTP ETag
   - Оптимистичная блокировка (412 Precondition Failed)
   - Обработка конфликтов при Git push (409 Conflict)
   - Детали: [colly-versioning-conflicts.md](./colly-versioning-conflicts.md)

**Особенности Option 4:**

- Не использует ParamSet механизм
- Не требует ассоциаций ParamSet в `env_definition.yml`
- Упрощенная структура хранения (3 файла вместо множества ParamSet)
- UI отправляет все параметры (включая закоммиченные) в `request.parameters`
- Colly отображает `state`, `value`, `originalValue` для пользователя

#### Сравнение Опций

| Критерий                                   | Option 1. Env Specific Parameters Override                | Option 2. Env Instance Override                                                      | Option 3. Effective Set Override                                                                | Option 4. UI Override Files                      |
|:-------------------------------------------|:----------------------------------------------------------|:-------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------|:-------------------------------------------------|
| **Время применения изменений**             | Дольше - требуется `env_build` + `generate_effective_set` | Среднее - требуется `generate_effective_set`                                         | Мгновенно - изменения применяются сразу                                                         | Среднее - требуется `generate_effective_set`     |
| **Сложность реализации**                   | Средняя                                                   | Высокая                                                                              | Высокая                                                                                         | Низкая                                           |
| **Риск рассинхронизации**                  | Низкий - оверрайды в одном месте (ParamSet)               | Средний - оверрайды в двух местах (ParamSet + Application/Namespace)                 | Высокий - оверрайды в трех местах (ParamSet + Application/Namespace + ES)                       | Низкий - оверрайды в одном месте (ui-overrides/) |
| **Использование ParamSet**                 | Да                                                        | Да                                                                                   | Да                                                                                              | Нет                                              |
| **Изменения в Inventory**                  | Да - ассоциация ParamSet                                  | Да - ассоциация ParamSet + мерж в Application/Namespace                              | Да - ассоциация ParamSet + мерж в Application/Namespace + мерж в ES                             | Нет                                              |
| **Изменения в EnvGene**                    | Calculator + валидация в env_build                        | Calculator + валидация в env_build + мерж в объекты                                  | Calculator + валидация в env_build + мерж в объекты + мерж в ES                                 | Только Calculator                                |
| **Tracking оригинальных значений**         | Нет                                                       | Нет                                                                                  | Нет                                                                                             | Да - через ui-override-original-values.yaml      |
| **Поддержка uncommitted изменений в UI**   | Нет                                                       | Нет                                                                                  | Нет                                                                                             | Да - через request.parameters                    |

## API документация

Детальное описание API для работы с UI override (Option 4) см. в следующих документах:

1. **[colly-ui-parameters-api.md](./colly-ui-parameters-api.md)** - UI Parameters API
   - GET/POST endpoints для управления UI override файлами
   - Структура запросов и ответов
   - Примеры использования
   - Логика обработки по уровням (Environment/Namespace/Application)

2. **[colly-effective-set-api.md](./colly-effective-set-api.md)** - Effective Set API
   - POST endpoint для получения Effective Set с метаданными
   - Объектная модель (originalValue, state, value)
   - Алгоритмы вычисления состояний параметров
   - Примеры ответов

3. **[colly-applications-api.md](./colly-applications-api.md)** - Applications API
   - GET endpoint для получения списка приложений в namespace
   - Используется UI для отображения выпадающего списка приложений

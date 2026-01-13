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
      - [Сравнение Опций](#сравнение-опций)
    - [Colly](#colly)
      - [ParamSet API](#paramset-api)
      - [ParamSetAssociation API](#paramsetassociation-api)
      - [Override UI API](#override-ui-api)
        - [GET Environment Level Parameters](#get-environment-level-parameters)
        - [GET Namespace Level Parameters](#get-namespace-level-parameters)
        - [GET Application Level Parameters](#get-application-level-parameters)
        - [POST Environment Level Paramters](#post-environment-level-paramters)
        - [POST Namespace Level Paramters](#post-namespace-level-paramters)
        - [POST Application Level Paramters](#post-application-level-paramters)
      - [GET Effective Set. Deployment context](#get-effective-set-deployment-context)
      - [GET Effective Set. Runtime context](#get-effective-set-runtime-context)
      - [GET Effective Set. Pipeline context](#get-effective-set-pipeline-context)
      - [Алгоритм мержа](#алгоритм-мержа)
    - [Обработка конфликтов при параллельных изменениях через UI разными пользователями и одновременном изменении через UI и Git](#обработка-конфликтов-при-параллельных-изменениях-через-ui-разными-пользователями-и-одновременном-изменении-через-ui-и-git)
      - [GET /api/ui-override](#get-apiui-override)
      - [POST /api/ui-override](#post-apiui-override)
      - [PUT /api/ui-override](#put-apiui-override)
      - [Конфликт при Git push](#конфликт-при-git-push)
    - [Appendix 1. факты о парамсетах](#appendix-1-факты-о-парамсетах)
    - [Appendix 2. Валидация структуры ParamSet](#appendix-2-валидация-структуры-paramset)

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
2. Нужен ли UI оверрайд параметров из DD?
3. Как очищать инвентори от UI оверрайдов при "сдаче" энва?
   1. удалять новый, создавать старый
4. Какой процесс сохранения параметров полученных в Dev/QA Test и "Озеленение" CI окружения в энв темплейте

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

      2. Во время `env_build` происходит валидация на то что ui-override парамсеты в конце списка - если нет, падает
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
                     - <deploy-postfix>-<application-name>-pipeline-ui-override
            ```

      2. Во время `env_build` происходит валидация на то что ui-override парамсеты в конце списка - если нет, падает
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
               name: <deploy-postfix>-deploy-ui-override  # или <deploy-postfix>-runtime-ui-override
               parameters: <>  # Пусто, т.к. параметры на уровне Application
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

#### Сравнение Опций

| Критерий | Option 1. Env Specific Parameters Override | Option 2. Env Instance Override | Option 3. Effective Set Override |
| :-------- | :------------------------------------------ | :------------------------------- | :-------------------------------- |
| **Время применения изменений** | Дольше - требуется `env_build` + `generate_effective_set` | Среднее - требуется `generate_effective_set` | Мгновенно - изменения применяются сразу |
| **Сложность реализации** | Ниже | Выше | Выше |
| **Риск рассинхронизации** | Низкий - оверрайды в одном месте (ParamSet) | Средний - оверрайды в двух местах (ParamSet + Application/Namespace) | Высокий - оверрайды в трех местах (ParamSet + Application/Namespace + ES) |

### Colly

#### ParamSet API

```text
GET    .../paramset/<paramsetId>
POST   .../paramset
PUT    .../paramset/<paramsetId>
DELETE .../paramset/<paramsetId>
```

```yaml
## ParamSet object
id: uuid
version: string # git commit hash
name: string
location: string # path in repo
parameters: map
applications: list
```

#### ParamSetAssociation API

```text
GET    .../paramset/<paramsetId>/associations
POST   .../paramset/<paramsetId>/associations
DELETE .../paramset/<paramsetId>/associations/<associationId>
```

```yaml
## ParamSetAssociation object
id: uuid
paramSetId: string
environmentId: string # in cluster/env
associatedObject: string # cloud or <deployPostfix>
context: enum[ deploy, pipeline, runtime ]
order: int # Порядок применения
```

#### Override UI API

##### GET Environment Level Parameters

```text
GET /api/ui-override?environmentId=<environmentId>&context=<context>
```

Параметры из аттрибута `parameters` парамсета c именем `<context>-ui-override` ассоцированный с энвайрментом `<environmentId>` c cloud, c контекстом `<context>`

1. Определи имя ParamSet: `<context>-ui-override`
2. Определи location на основе `environmentId`: `environments/parameters/<environmentId>/Inventory/parameters/`
3. Найди ParamSet по пути:
   - `filePath = location + "<context>-ui-override.yaml"`
   - Прочитай файл из Git репозитория
4. Проверь валидацию ассоциации
   - Проверь наличие имени ParamSet в `env_definition.yml` в секции соответствующей контексту (`envSpecificParamsets`, `envSpecificTechnicalParamsets`, `envSpecificE2EParamsets`) для `cloud`
5. Верни `parameters` из найденного ParamSet

##### GET Namespace Level Parameters

```text
GET /api/ui-override?environmentId=<environmentId>&context=<context>&namespaceName=<namespaceName>
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   - Найди список `Namespace` по `environmentId`
   - Найди среди них тот у которого `name=<namespaceName>`
   - Возьми у него `deployPostfix`
2. Определи имя ParamSet: `<deployPostfix>-<context>-ui-override`
3. Определи location на основе `environmentId`: `environments/parameters/<environmentId>/Inventory/parameters/`
4. Найди ParamSet по пути:
   - `filePath = location + "<deployPostfix>-<context>-ui-override.yaml"`
   - Прочитай файл из Git репозитория
5. Проверь валидацию ассоциации:
   - Проверь наличие имени ParamSet в `env_definition.yml` в секции соответствующей контексту (`envSpecificParamsets`, `envSpecificTechnicalParamsets`, `envSpecificE2EParamsets`) для `<deployPostfix>`
6. Верни `parameters` из найденного ParamSet

##### GET Application Level Parameters

```text
GET /api/ui-override?environmentId=<environmentId>&context=<context>&namespaceName=<namespaceName>&applicationName=<applicationName>
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   - Найди список `Namespace` по `environmentId`
   - Найди среди них тот у которого `name=<namespaceName>`
   - Возьми у него `deployPostfix`
2. Определи имя ParamSet: `<deployPostfix>-<context>-ui-override`
3. Определи location на основе `environmentId`: `environments/parameters/<environmentId>/Inventory/parameters/`
4. Найди ParamSet по пути:
   - `filePath = location + "<deployPostfix>-<context>-ui-override.yaml"`
   - Прочитай файл из Git репозитория
5. Проверь валидацию ассоциации:
   - Проверь наличие имени ParamSet в `env_definition.yml` в секции соответствующей контексту для `<deployPostfix>`
6. Найди в `applications` запись с `appName=<applicationName>`
7. Верни `applications[?name=<applicationName>].parameters` из найденного ParamSet

##### POST Environment Level Paramters

```text
POST /api/ui-override
```

```yaml
environmentId: string
context: enum[ deploy, pipeline, runtime ]
parameters: map
```

1. Создай Param Set в инстансном репозитории
   1. location: `environments/parameters/<environmentId>/Inventory/parameters/<context>-ui-override.yaml`
   2. content:

      ```yaml
      name: "<context>-ui-override"
      parameters: <parameters>
      applications: []
      ```

2. Добавь точку ассоциации в инвентори
   1. location: `environments/<environmentId>/Inventory/env_definition.yml`
   2. content:

      ```yaml
      envTemplate:
         envSpecificParamsets|envSpecificE2EParamsets|envSpecificTechnicalParamsets:
            cloud:
               - ...
               - "<context>-ui-override"
      ```

3. Создай `ParamSet`

      ```yaml
      id: <uuid>
      version: <git commit hash>
      name: <context>-ui-override
      location: <path>
      parameters: <parameters>
      applications: []
      ```

4. Создай `ParamSetAssociation`

      ```yaml
      id: <uuid>
      paramSetId: <ParamSet uuid>
      environmentId: <environmentId>
      associatedObject: cloud
      context: <context>
      order: int
      ```

##### POST Namespace Level Paramters

```text
POST /api/ui-override
```

```yaml
environmentId: string
namespaceName: string
context: enum[ deploy, pipeline, runtime ]
parameters: map
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   1. Найди список `Namespace` по `environmentId`
   2. Найди среди них тот у которого `name=<namespaceName>`
   3. Возьми у него `deployPostfix`

2. Создай Param Set в инстансном репозитории
   1. location: `environments/parameters/<environmentId>/Inventory/parameters/<deployPostfix>-<context>-ui-override.yaml`
   2. content:

      ```yaml
      name: "<deployPostfix>-<context>-ui-override"
      parameters: <parameters>
      applications: []
      ```

3. Добавь точку ассоциации в инвентори
   1. location: `environments/<environmentId>/Inventory/env_definition.yml`
   2. content:

      ```yaml
      envTemplate:
         envSpecificParamsets|envSpecificE2EParamsets|envSpecificTechnicalParamsets:
            <deployPostfix>:
               - ...
               - "<deployPostfix>-<context>-ui-override"
      ```

4. Создай `ParamSet`

      ```yaml
      id: <uuid>
      version: <git commit hash>
      name: "<deployPostfix>-<context>-ui-override"
      location: <path>
      parameters: <parameters>
      applications: []
      ```

5. Создай `ParamSetAssociation`

      ```yaml
      id: <uuid>
      paramSetId: <ParamSet uuid>
      environmentId: <environmentId>
      associatedObject: <deployPostfix>
      context: <context>
      order: int
      ```

##### POST Application Level Paramters

```text
POST /api/ui-override
```

```yaml
environmentId: string
namespaceName: string
applicationName: string
context: enum[ deploy, pipeline, runtime ]
parameters: map
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   1. Найди список `Namespace` по `environmentId`
   2. Найди среди них тот у которого `name=<namespaceName>`
   3. Возьми у него `deployPostfix`

2. Создай Param Set в инстансном репозитории
   1. location: `environments/parameters/<environmentId>/Inventory/parameters/<deployPostfix>-<context>-ui-override.yaml`
   2. content:

      ```yaml
      name: "<deployPostfix>-<context>-ui-override"
      parameters: {}
      applications:
        - appName: <applicationName>
          parameters: <parameters>
      ```

3. Добавь точку ассоциации в инвентори
   1. location: `environments/<environmentId>/Inventory/env_definition.yml`
   2. content:

      ```yaml
      envTemplate:
         envSpecificParamsets|envSpecificTechnicalParamsets:
            <deployPostfix>:
               - ...
               - "<deployPostfix>-<context>-ui-override"
      ```

4. Создай `ParamSet`

      ```yaml
      id: <uuid>
      version: <git commit hash>
      name: "<deployPostfix>-<context>-ui-override"
      location: <path>
      parameters: {}
      applications:
        - appName: <applicationName>
          parameters: <parameters>
      ```

5. Создай `ParamSetAssociation`

      ```yaml
      id: <uuid>
      paramSetId: <ParamSet uuid>
      environmentId: <environmentId>
      associatedObject: <deployPostfix>
      context: <context>
      order: int
      ```

> [!WARNING]
> Изменения нескольких файлов (парамсет и инвентори) должны быть транзакционными

#### GET Effective Set. Deployment context

```text
GET /api/effective-set?environmentId=<environmentId>&context=deployment&namespaceName=<namespaceName>&applicationName=<applicationName>
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   1. Найди список `Namespace` по `environmentId`
   2. Найди среди них тот у которого `name=<namespaceName>`
   3. Возьми у него `deployPostfix`
2. Найди файлы эффектив сета по пути `environments/parameters/<environmentId>/effective-set/deployment/<deployPostfix>/<applicationName>/values`
3. Замержи последовательно файлы из этого фолдера:
   1. `deployment-parameters.yaml`
   2. `credentials.yaml`
   3. `collision-deployment-parameters.yaml`
   4. `collision-credentials.yaml`
4. Отдай результат

#### GET Effective Set. Runtime context

```text
GET /api/effective-set?environmentId=<environmentId>&context=runtime&namespaceName=<namespaceName>&applicationName=<applicationName>
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   1. Найди список `Namespace` по `environmentId`
   2. Найди среди них тот у которого `name=<namespaceName>`
   3. Возьми у него `deployPostfix`
2. Найди файлы эффектив сета по пути `environments/parameters/<environmentId>/effective-set/runtime/<deployPostfix>/<applicationName>/`
3. Замержи последовательно файлы из этого фолдера:
   1. `parameters.yaml`
   2. `credentials.yaml`
4. Отдай результат

#### GET Effective Set. Pipeline context

```text
GET /api/effective-set?environmentId=<environmentId>&context=pipeline&namespaceName=<namespaceName>&applicationName=<applicationName>
```

1. Найди `Namespace` по `environmentId` и `namespaceName`:
   1. Найди список `Namespace` по `environmentId`
   2. Найди среди них тот у которого `name=<namespaceName>`
   3. Возьми у него `deployPostfix`
2. Найди файлы эффектив сета по пути `environments/parameters/<environmentId>/effective-set/pipeline/`
3. Замержи последовательно файлы из этого фолдера:
   1. `parameters.yaml`
   2. `credentials.yaml`
4. Отдай результат

#### Алгоритм мержа

Для словарей: рекурсивное объединение. Если ключ есть в обоих файлах и значение — словарь, они объединяются рекурсивно, а не перезаписываются.
Для списков: полная замена. Если ключ есть в обоих файлах и значение — список, список из последнего файла полностью заменяет предыдущий.
Для примитивов: значение из последнего файла перезаписывает предыдущее.

Если при мерже нашлись пересечения ключей отдается ошибка

### Обработка конфликтов при параллельных изменениях через UI разными пользователями и одновременном изменении через UI и Git

1. Версия ParamSet = Git commit hash последнего коммита конкретного файла
2. [HTTP ETag](https://datatracker.ietf.org/doc/html/rfc7232#section-2.3) = commit hash последнего коммита, изменившего конкретный файл
3. Colly управляет версионированием через Git

#### GET /api/ui-override

Процесс:

1. Colly определяет путь к файлу ParamSet
2. Colly проверяет, существует ли файл в Git
3. Если файл не существует:
   1. Возвращает 404 Not Found
   2. Включает информацию об ошибке в ответ
4. Если файл существует:
   1. Получает SHA-1 hash последнего коммита, изменившего файл
   2. Читает и парсит содержимое файла
   3. Возвращает ParamSet в теле ответа
   4. Устанавливает ETag в заголовке ответа (hash в кавычках)

Успешный ответ:

- Статус: 200 OK
- Заголовок ETag: commit hash в кавычках
- Заголовок Cache-Control: no-cache
- Тело: JSON с содержимым ParamSet

Ответ если ParamSet не существует:

- Статус: 404 Not Found
- Тело: описание ошибки, информация о том, что ParamSet не найден

#### POST /api/ui-override

Процесс:

1. Colly валидирует входные данные (name, location, context, parameters, applications)
2. Colly определяет путь к файлу ParamSet на основе location и name
3. Colly проверяет, что ParamSet с таким ID не существует
4. Если ParamSet уже существует:
   1. Возвращает 409 Conflict
   2. Включает информацию о существующем ParamSet в ответ
5. Если ParamSet не существует:
   1. Создает файл ParamSet в Git
   2. Коммитит изменения в Git
   3. Получает новый commit hash
   4. Возвращает успех с новым ETag

Запрос:

- Тело: JSON с данными для создания ParamSet:

Успешный ответ:

- Статус: 201 Created
- Заголовок Location: /api/ui-override
- Заголовок ETag: новый commit hash
- Тело: сообщение об успехе, ID созданного ParamSet и версия

Ответ при конфликте (ParamSet уже существует):

- Статус: 409 Conflict
- Заголовок ETag: commit hash существующего ParamSet
- Тело: описание ошибки, информация о существующем ParamSet

Ответ при ошибке валидации:

- Статус: 400 Bad Request или 422 Unprocessable Entity
- Тело: описание ошибок валидации

#### PUT /api/ui-override

Процесс:

1. Colly определяет путь к файлу ParamSet
2. Colly проверяет, существует ли файл в Git
3. Если файл не существует:
   1. Возвращает 404 Not Found (PUT используется только для обновления существующих ParamSet)
4. Если файл существует:
   1. Colly извлекает ожидаемый hash из заголовка If-Match
   2. Получает текущий commit hash файла
   3. Сравнивает текущий hash с ожидаемым
   4. Если совпадают:
      1. Обновляет файл
      2. Коммитит изменения в Git
      3. Получает новый commit hash
      4. Возвращает успех с новым ETag
   5. Если не совпадают:
      1. Возвращает 412 Precondition Failed
      2. Включает текущую версию и содержимое в ответ

Запрос:

- Заголовок If-Match: ожидаемый ETag (commit hash)
- Тело: JSON с обновленным содержимым ParamSet

Успешный ответ:

- Статус: 200 OK
- Заголовок ETag: новый commit hash
- Тело: сообщение об успехе и новая версия

Ответ при конфликте версии:

- Статус: 412 Precondition Failed
- Заголовок ETag: текущий commit hash
- Тело: описание ошибки, текущая и ожидаемая версии, текущее содержимое

Ответ если ParamSet не существует:

- Статус: 404 Not Found
- Тело: описание ошибки, информация о том, что ParamSet не найден

UI при получение 412:

1. Отображает ошибку
2. Обновляет отображаемое значение оверрайда на полученное в теле (изменения пользователя теряются)

#### Конфликт при Git push

1. Локальный коммит успешен
2. При push обнаружен конфликт (кто-то запушил раньше)

Обработка:

1. Откат локального коммита
2. Pull последних изменений
3. Получение новой версии из удаленного репозитория
4. Возврат ошибки 409 Conflict с текущей версией

### Appendix 1. факты о парамсетах

1. парамсеты могут быть расположены в репозитории в трех папках:
   1. `environments/parameters`
   2. `environments/parameters/<cluster-name>`
   3. `environments/parameters/<cluster-name>/<env-name>`
2. парамсеты ассоциируются к объектам определенного энвайрмента:
   1. клауду - по зарезервированому слову `cloud`
   2. неймспейсу - по аттрибуту `deployPostfix` неймспейса
3. к объектам выше парамсет может быть проаасооциирован к контекстам
   1. деплой
   2. рантайм
   3. пайплайн
4. один парамсет может быть проассоциирован к нескольким энвайментам/объектам/контекстам
5. энвайрмент идентифицируется по environmentId = `<clusterName>/<envroronmentName>`
6. уникальность парамсета определяет имя + location

### Appendix 2. Валидация структуры ParamSet

- Для `level: environment` и `context: deployment|runtime`: `parameters` обязателен, `applications` должен быть пустым
- Для `level: environment` и `context: pipeline`: `parameters` обязателен, `applications` должен быть пустым
- Для `level: namespace` и `context: deployment|runtime`: `parameters` обязателен, `applications` должен быть пустым
- Для `level: namespace` и `context: pipeline`: `parameters` обязателен, `applications` должен быть пустым
- Для `level: application` и `context: deployment|runtime`: `parameters` должен быть пустым, `applications` обязателен и не пустой
- Для `level: application` и `context: pipeline`: недопустимо (pipeline параметры не могут быть на уровне application)

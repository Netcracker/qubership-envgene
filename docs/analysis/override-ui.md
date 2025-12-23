# Override UI

- [Override UI](#override-ui)
  - [Problem Statement](#problem-statement)
  - [Scenarios](#scenarios)
  - [Proposed Approach](#proposed-approach)
    - [Prototype](#prototype)
    - [Варианты реализации UI оверрайда в энвгене](#варианты-реализации-ui-оверрайда-в-энвгене)
      - [Option 1. Env Specific Parameters Override](#option-1-env-specific-parameters-override)
      - [Option 2. Env Instance Override](#option-2-env-instance-override)
      - [Option 3. Effective Set Override](#option-3-effective-set-override)
    - [Реализация в Колли](#реализация-в-колли)
  - [Use Cases](#use-cases)
  - [Open Questions](#open-questions)

## Problem Statement

1. **Нам удобнее в UI**

   Работа через Git требует определенных навыков и привычек. Для пользователей, которые привыкли работать через UI, это может вызывать неудобство и отторжение.

2. **EnvGene сложный**

   EnvGene содержит большое количество разнообразных [объектов](/docs/envgene-objects.md), которые необходимы для реализации различных сценариев использования. Пользователь должен изучить и понять эти объекты, чтобы выполнять даже простые действия, такие как изменение одного параметра, что создает высокий барьер входа для новых пользователей и требует значительного времени на изучение системы.

3. **Поменять один параметр долго**

   Изменение параметра в EnvGene занимает определенное время: checkout репозитория, изменение YAML-файла в Git, push в удаленный репозиторий. В сценариях разработки, когда разработчик работает с одним окружением, проводит dev-тест и требуются частые изменения параметров, текущий подход по работе с параметрами приносит значительные накладные расходы — изменение одного параметра занимает длительное время, что приводит к потере времени разработчика.

## Scenarios

Сценарии ниже подразумевают что в качестве CM используется EnvGene в noCMDB режиме

1. **Dev/QA Test**

   Разработчик/QA или группа разработчиков/QA получили развернутое в облаке окружение для тестирования изменений.

   В процессе отладки и тестирования требуется многократный редеплой отдельных приложений с изменением их параметров в CM для достижения корректной работы функциональности.

   Полученные в результате отладки и тестирования изменения параметров требуют сохранения в шаблоне окружения для воспроизводимости в будущих окружениях и использования в других инстансах.

2. **"Озеленение" CI окружения**

   После упавших автотестов при автоматизированном деплое солюшена в CI окружение, QA инженер вносит в этот солюшен фиксы/хот-фиксы для достижения успешного прохождения тестов.

   Процесс включает многократный редеплой отдельных приложений, что требует изменения параметров этих приложений в CM.

   Полученные в результате отладки и тестирования изменения параметров требуют сохранения в шаблоне окружения для воспроизводимости в будущих окружениях и использования в других инстансах.

<!-- ## Use Cases

1. **View parameters:**
   1. View parameter sources:
      1. User defined parameters
         1. In Environment Instance objects:
            1. Tenant
               1. Deploy context
               2. Pipeline context
            2. Cloud
               1. Deploy context
               2. Pipeline context
               3. Runtime context
            3. Namespace
               1. Deploy context
               2. Pipeline context
               3. Runtime context
            4. Application
               1. Deploy context
               2. Runtime context
            5. Credentials
            6. Resource Profile override
         2. In shared objects
            1. Shared Credentials
            2. Shared Parameter sets
            3. Shared Resource Profile override
      2. DD/SBOM parameters
         1. Resource Profile override
         2. Build time parameters
   2. View Effective Set
      1. For an Environment
      2. For a namespace (cluster/env/ns)
      3. For an application (cluster/env/ns/app)
   3. View parameter override
   4. Parameter search by key and value
      1. In user defined parameters
      2. In Effective Set
2. **Change parameters:**
   1. In Environment Instance objects:
      1. Tenant
         1. Deploy context
         2. Pipeline context
      2. Cloud
         1. Deploy context
         2. Pipeline context
         3. Runtime context
      3. Namespace
         1. Deploy context
         2. Pipeline context
         3. Runtime context
      4. Application
         1. Deploy context
         2. Runtime context
      5. Credentials
      6. Resource Profile override
   2. In shared objects
      1. Shared Credentials
      2. Shared Parameter sets
      3. Shared Resource Profile override
   3. In Effective Set
   4. Change parameter override
   5. Change and:
      1. save for next runs
      2. use only until next regeneration
3. **Create objects:**
   1. Environment Instance objects:
      1. Tenant
      2. Cloud
      3. Namespace
      4. Application
      5. Credentials
      6. Resource Profile override
   2. Shared objects
      1. Shared Credentials
      2. Shared Parameter sets
      3. Shared Resource Profile override
4. **Delete objects:**
   1. Environment Instance objects:
      1. Tenant
      2. Cloud
      3. Namespace
      4. Application
      5. Credentials
      6. Resource Profile override
   2. Shared objects
      1. Shared Credentials
      2. Shared Parameter sets
      3. Shared Resource Profile override
5. **View how a change affected Effective Set**
6. **View parameter change history**
7. **Rollback changes**
8. **Bulk environments update**
9. **Remove parameters**
10. **View diff:**
    1. Between environments
    2. Before saving/commit
11. **Navigate parameter structure**
12. **Persist parameters obtained from an Environment in Environment template**
13. **Object validation before saving**
14. **Check for conflicts during parallel changes**
15. **Built-in help, contextual hints**

**Notes:**

1. Service object doesn't exist, but for dev cases it's needed to be able to set parameters, for example, to replace docker image tag without rebuilding DD. Similar to override case passed as pipeline attribute -->

## Proposed Approach

![override-ui-arch.png](/docs/images/override-ui-arch.png)

### Prototype

![override-ui-prototype.html](/docs/analysis/override-ui-prototype.html)

### Варианты реализации UI оверрайда в энвгене

![override-ui-options.png](/docs/images/override-ui-options.png)

#### Option 1. Env Specific Parameters Override

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

   3. парамсеты имеют следующую структуру:
      1. для `deployment` и `runtime` контекста:

            ```yaml
            name: string
            parameters: {}
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

4. Возможность создавать креды не предоставляется
   1. **Assumption**: В тех репозиториях/сайтах где используется Override UI энкрипт репозитория не требуется

#### Option 2. Env Instance Override

1. Все то же самое что и в **Option 1. Env Specific Parameters Override**
2. При создание UI оверрайда значения мержатся в режиме Shallow Merge в Application энвайрмента:
   1. для `deploy` в аттрибут `deployParameters` Application объекта расположенного в `environments/<cluster>/<env>/Namespaces/<ns>/Applications/<app>.yml`
   2. для `runtime` в аттрибут `technicalConfigurationParameters` Application объекта расположенного в `environments/<cluster>/<env>/Namespaces/<ns>/Applications/<app>.yml`
   3. для `pipeline` в аттрибут `e2eParameters` во все Namespace объекты энвайрмента, расположенные в `environments/<cluster>/<env>/namespace.yml`

#### Option 3. Effective Set Override

1. Все то же самое что и в **Option 2. Env Instance Override**
2. При создание UI оверрайда значения мержатся в режиме Shallow Merge в файлы ES:
   1. для `deploy` в `effective-set/deployment/<ns>/<app>/values/deployment-parameters.yaml`
   2. для `runtime` в `effective-set/runtime/<ns>/<app>/parameters.yaml`
   3. для `pipeline` в `effective-set/pipeline/parameters.yaml`

### Реализация в Колли

Колли умеет для Option 1 в Инстансном репозитории:

1. CRUD парамсеты
2. Update инвентори - ассоциировать парамсеты

## Use Cases

1. Create override.
   1. Add a new parameter to:
      1. An application deployment context
      2. An application runtime context
      3. An Environment pipeline context
   2. Override a parameter value for:
      1. An application deployment context
      2. An application runtime context
      3. An Environment pipeline context
   3. ~~Remove a parameter~~
2. View override parameters for:
   1. An application deployment context
   2. An application runtime context
   3. An Environment pipeline context
3. Update override
4. Delete override

## Open Questions

1. Необходимо ли обрабатывать часть UI оверрайд параметров как сенсетив параметры - энкриптить при сохранение в репозиторий?
2. Нужен ли UI оверрайд параметров из DD?
3. Как очищать инвентори от UI оверрайдов при "сдаче" энва?
   1. удалять новый, создавать старый
4. Какой процесс сохранения параметров полученных в Dev/QA Test и "Озеленение" CI окружения в энв темплейте

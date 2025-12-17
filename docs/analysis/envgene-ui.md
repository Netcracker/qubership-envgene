# EnvGene UI

- [EnvGene UI](#envgene-ui)
  - [Problem Statement](#problem-statement)
  - [Scenarios](#scenarios)
  - [Use Cases](#use-cases)
  - [Proposed Approach](#proposed-approach)
  - [UI](#ui)
    - [Effective Set override](#effective-set-override)
    - [Env Instance override](#env-instance-override)
  - [Работа с локальными файлами + CLI](#работа-с-локальными-файлами--cli)
  - [Сделать энвген объекты опциональными](#сделать-энвген-объекты-опциональными)
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

2. **Стабилизация, "озеленение" CI окружения**

   После упавших автотестов при автоматизированном деплое солюшена в CI окружение, QA инженер вносит в этот солюшен фиксы/хот-фиксы для достижения успешного прохождения тестов.

   Процесс включает многократный редеплой отдельных приложений, что требует изменения параметров этих приложений в CM.

   Полученные в результате отладки и тестирования изменения параметров требуют сохранения в шаблоне окружения для воспроизводимости в будущих окружениях и использования в других инстансах.

3. **Создание нового окружения**

   DevOps инженер разворачивает новый инстанс солюшена на основе шаблона окружения для предоставления его разработчику/QA.

   В процессе создания требуется настройка параметров окружения, приложений и конфигурации через CM.

## Use Cases

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
   3. Parameter search by key and value
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
   4. Change and:
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
7. **View diff:**
   1. Between environments
   2. Before saving/commit
8. **Navigate parameter structure**
9. **Persist parameters obtained from an Environment in Environment template**
10. **Object validation before saving**
11. **Check for conflicts during parallel changes**
12. **Built-in help, contextual hints**

**Notes:**

1. Service object doesn't exist, but for dev cases it's needed to be able to set parametrs, for example, to replace docker image tag without rebuilding DD. Similar to override case passed as pipeline attribute)

## Proposed Approach

[envgene-ui.md](/docs/images/envgene-ui.png)

## UI

### Effective Set override

<!-- 1. Оверрайдится эффектив сет
2. При оверрайде оверрайд также сохраняется и в парамсете и на объекте аппликейшен, для воспроизводимости с этапов env_build, generate_effective_set
3. Эффектив сет может быть применен сразу -->

### Env Instance override

<!-- 1. Оверрайдится энв инстанс
   1. Namespace ИЛИ
   2. Application
2. При оверрайде оверрайд также сохраняется в парамсете, для воспроизводимости с этапов env_build
3. Требуется гегенерация эффектив сета -->

## Работа с локальными файлами + CLI

## Сделать энвген объекты опциональными

## Open Questions

1. Могу ли я через ресурсные профили задать любой параметр и он попадет в персервисные параметры?
   1. `/effective-set/deployment/<ns>/<app-name>/values/per-service-parameters/<service-name>/deployment-parameters.yaml`
   2. `/effective-set-7/effective-set/deployment/<ns>/<app-name>/values/deploy-descriptor.yaml:<service-name>`
   3. `/effective-set-7/effective-set/deployment/<ns>/<app-name>/values/credentials.yaml:<service-name>`

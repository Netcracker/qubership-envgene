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
      - [Override UI API](#override-ui-api)
      - [Effective Set API](#effective-set-api)
    - [Обработка конфликтов при параллельных изменениях через UI разными пользователями и одновременном изменении через UI и Git](#обработка-конфликтов-при-параллельных-изменениях-через-ui-разными-пользователями-и-одновременном-изменении-через-ui-и-git)
      - [Версионирование через Git](#версионирование-через-git)
      - [Обработка конфликтов](#обработка-конфликтов)
      - [GET `/environments/<envId>/ui-parameters`](#get-environmentsenvidui-parameters)
      - [POST `/environments/<envId>/ui-parameters`](#post-environmentsenvidui-parameters)
      - [Детали обработки конфликтов](#детали-обработки-конфликтов)
  - [План реализации](#план-реализации)

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
         - UI override парамсеты (с `type: "ui-override"`) должны быть в конце списка - если нет, падает
         - UI override парамсеты должны иметь `type: "ui-override"` и имя файла должно соответствовать паттерну UI override - если нет, падает
         - Парамсеты с `type: "ui-override"` должны иметь имя файла, соответствующее паттерну UI override - если нет, падает
      3. Во время `env_inventory_generation` (или в первой джобе?) происходит валидация, что создаются или изменяются ui-override парамсеты - если да, падает

   3. парамсеты имеют следующую структуру:
      1. для `deployment` и `runtime` контекста:

            ```yaml
            name: string
            type: "ui-override"  # Обязательно для UI override парамсетов
            parameters: <>
            applications:
               - appName: string
                 parameters: map
            ```

      2. для `pipeline` контекста: `pipeline-ui-override.yaml`

            ```yaml
            name: string
            type: "ui-override"  # Обязательно для UI override парамсетов
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

      2. Во время `env_build` происходит валидация:
         - UI override парамсеты (с `type: "ui-override"`) должны быть в конце списка - если нет, падает
         - UI override парамсеты должны иметь `type: "ui-override"` и имя файла должно соответствовать паттерну UI override - если нет, падает
         - Парамсеты с `type: "ui-override"` должны иметь имя файла, соответствующее паттерну UI override - если нет, падает
      3. Во время `env_inventory_generation` (или в первой джобе?) происходит валидация, что создаются или изменяются ui-override парамсеты - если да, падает

   3. парамсеты имеют следующую структуру в зависимости от уровня:
      1. Deployment и Runtime контексты:

         1. На уровне Environment:

               ```yaml
               name: deploy-ui-override  # или runtime-ui-override
               type: "ui-override"  # Обязательно для UI override парамсетов
               parameters: map  # Параметры уровня Environment
               applications: []  # Пусто, т.к. параметры на уровне Environment
               ```

         2. На уровне Namespace:

               ```yaml
               name: <deploy-postfix>-deploy-ui-override  # или <deploy-postfix>-runtime-ui-override
               type: "ui-override"  # Обязательно для UI override парамсетов
               parameters: map  # Параметры уровня Namespace
               applications: []  # Пусто, т.к. параметры на уровне Namespace
               ```

         3. На уровне Application:

               ```yaml
               name: <deploy-postfix>-deploy-ui-override  # или <deploy-postfix>-runtime-ui-override
               type: "ui-override"  # Обязательно для UI override парамсетов
               parameters: <>  # Пусто, т.к. параметры на уровне Application
               applications:
                  - appName: string
                    parameters: map  # Параметры уровня Application
               ```

      2. Pipeline контекст:

         1. На уровне Environment:

               ```yaml
               name: pipeline-ui-override
               type: "ui-override"  # Обязательно для UI override парамсетов
               parameters: map  # Параметры уровня Environment
               applications: []  # Пусто
               ```

         2. На уровне Namespace:

               ```yaml
               name: <deploy-postfix>-pipeline-ui-override
               type: "ui-override"  # Обязательно для UI override парамсетов
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

Детальное описание ParamSet API, объектной модели и endpoints см. в [colly-paramset-api.md](./colly-paramset-api.md).

Endpoints для работы с ParamSet (`/api/v1/paramset/`) в текущей версии реализовывать не планируется. Для работы с UI override параметрами используются convenience endpoints.

#### Override UI API

Colly предоставляет convenience endpoints для работы с UI override параметрами:

- `GET /api/v1/environments/{environmentId}/ui-parameters` - получение UI override параметров
- `POST /api/v1/environments/{environmentId}/ui-parameters` - создание/обновление UI override параметров

Поддерживаются три уровня:

- **Environment Level** - параметры применяются ко всем namespace в окружении
- **Namespace Level** - параметры применяются ко всем приложениям в namespace
- **Application Level** - параметры применяются к конкретному приложению

Детальное описание API endpoints, алгоритмов, примеров запросов/ответов и обработки ошибок см. в [colly-paramset-api.md](./colly-paramset-api.md#api-endpoints).

#### Effective Set API

Детальное описание Effective Set API, объектной модели, вариантов реализации и алгоритмов формирования параметров см. в [colly-effective-set-api.md](./colly-effective-set-api.md).

### Обработка конфликтов при параллельных изменениях через UI разными пользователями и одновременном изменении через UI и Git

#### Версионирование через Git

- `commitHash` ParamSet = Git commit hash последнего коммита файла
- Используется [HTTP ETag](https://datatracker.ietf.org/doc/html/rfc7232#section-2.3) для оптимистичной блокировки
- При каждом изменении создается новый коммит в Git

#### Обработка конфликтов

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
     - Предложить разрешить конфликт (merge или overwrite)

#### GET `/environments/<envId>/ui-parameters`

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

#### POST `/environments/<envId>/ui-parameters`

Процесс:

1. Colly валидирует входные данные (context, parameters, namespaceName, applicationName)
2. Colly определяет путь к файлу ParamSet на основе уровня и контекста
3. Если ParamSet уже существует:
   1. Обновляет параметры (merge)
   2. Коммитит изменения в Git
   3. Получает новый commit hash
   4. Возвращает успех с новым ETag
4. Если ParamSet не существует:
   1. Создает файл ParamSet в Git
   2. Добавляет ассоциацию в `env_definition.yml`
   3. Коммитит изменения в Git
   4. Получает новый commit hash
   5. Возвращает успех с новым ETag

Запрос:

- Тело: JSON с данными для создания ParamSet:

Успешный ответ (ParamSet создан):

- Статус: 201 Created
- Заголовок Location: `/environments/{environmentId}/ui-parameters`
- Заголовок ETag: новый commit hash
- Тело: `map` (созданные параметры)

Успешный ответ (ParamSet обновлен):

- Статус: 200 OK
- Заголовок ETag: новый commit hash
- Тело: `map` (обновленные параметры)

Ответ при ошибке валидации:

- Статус: 400 Bad Request или 422 Unprocessable Entity
- Тело: описание ошибок валидации

#### Детали обработки конфликтов

**Для POST запросов:**

- POST поддерживает создание и обновление (upsert)
- Если ParamSet существует, параметры мержатся
- Оптимистичная блокировка через `If-Match` не используется для POST (upsert операция)

**Для PUT запросов (если будут реализованы):**

- PUT требует обязательный заголовок `If-Match` с ожидаемой версией
- При несовпадении версий возвращается `412 Precondition Failed`
- В теле ответа включается текущая версия и содержимое

**Конфликт при Git push:**

- Если локальный коммит успешен, но push не удался (кто-то запушил раньше)
- Откат локального коммита
- Pull последних изменений
- Возврат `409 Conflict` с текущей версией

**UI обработка конфликтов:**

- При получении `412` или `409`:
  - Показать ошибку пользователю
  - Отобразить текущее содержимое из ответа
  - Предложить разрешить конфликт (merge или overwrite)

## План реализации

1. Ввести типизацию парамсетов:

      ```yaml
      name: string
      type: enum[ "standard" | "ui-override" ]  # default: "standard"
      parameters: map
      applications: list
      ```

   - Поддержка в Colly API
   - Поддержка в EnvGene:
     - Валидация `type: "ui-override"` в `env_build` (проверка, что UI override парамсеты в конце списка)
     - Валидация соответствия `type` и имени файла
     - Удаление `type` аттрибута на cmdb_import

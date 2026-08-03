# UC-MIG-1. Перенос значений локальных Credentials во внешний Secret Store

- [Описание](#описание)
- [Ограничения](#ограничения)
- [Входящие параметры](#входящие-параметры)
- [Предусловия](#предусловия)
- [Алгоритм](#алгоритм)

## Описание

До перевода Credentials на `type: external` нужно перенести текущие значения из Instance
Repository во внешний Secret Store. Пользователь запускает Migration CLI.

Migration CLI сам находит Credentials, строит размещение по входной политике, собирает
временный External Credential Context и вызывает
[`external-cred-provision`](/docs/features/external-creds-provisioning-cli.md).

Пользователь передаёт:

- откуда читать Instance Repository
- политику размещения (`secretStore`, тип store, правило `remoteRefPath`)
- режим: проверка (по умолчанию) или запись (`--execute`)

## Ограничения

- Типы: `usernamePassword`, `secret`.
- Переносятся только реальные значения в `data`.
- Заглушки (`envgeneNullValue`, пустые значения) **не** пишутся в store.
- В store пишет только `external-cred-provision` со `strategy: overwrite`.
- Без `--execute` запись в store не выполняется.

## Входящие параметры

```bash
migration-cli \
  --instance-repo /path/to/instance-repository \
  --secret-store default_store \
  --store-type vault \
  --mount-path secret \
  --remote-ref-path-template "{{ cloud }}/{{ env }}" \
  --env cluster-1/env-1 \
  --execute
```

| Параметр                       | Обязательный | Зачем |
|--------------------------------|--------------|-------|
| `--instance-repo`              | да           | Корень Instance Repository. Источник Credential-файлов и `data`. |
| `--secret-store`               | да           | Id Secret Store. |
| `--store-type`                 | да           | Тип store для сборки VALS (`vault`, `gcp`, `aws`, …). |
| параметры store                | да, от type  | Например `--mount-path` (Vault), `--project-id` (GCP), `--region` (AWS). |
| `--remote-ref-path-template`   | да           | Правило префикса пути в store. `credId` в конец шаблона не входит. |
| `--env`                        | нет          | Сузить область до `cluster/env`. Не указан → весь репозиторий. |
| `--execute`                    | нет          | Без флага - только проверка. С флагом - запись в store. |

Цепочка:

```text
пользователь
  → migration-cli (repo + политика размещения + [--execute])
    → отчёт в консоль (что будет перенесено и куда)
    → временный External Credential Context
      → external-cred-provision [--dry-run] <context-path>
        → без --execute: только проверки
        → с --execute: запись в Secret Store
```

Путь в store: значение шаблона `remote-ref-path-template` (после подстановки `cloud` / `env`) +
`credId`. Пользователь `credId` в шаблон не дописывает.

## Предусловия

- Instance Repository читается Migration CLI.
- Credentials ещё local (`usernamePassword` / `secret`), в `data` есть исходные значения.
- Пользователь задал политику размещения (store + path template).
- Для `--execute` настроена auth в окружении процесса для `external-cred-provision`.

## Алгоритм

1. Пользователь запускает `migration-cli` с политикой размещения.
2. CLI находит Credential-файлы в области:

   | Источник       | Где                                                   |
   |----------------|-------------------------------------------------------|
   | Cloud Passport | `*-creds.yml`                                         |
   | Shared         | `sharedMasterCredentialFiles` + unbound               |
   | System         | `/configuration/credentials/`, deployer `*-creds.yml` |

   Generated `.../Credentials/credentials.yml` не читается.

3. Берёт top-level ключи с `type: usernamePassword` или `type: secret`.
4. Читает `data`. Если значение зашифровано - расшифровывает. Кладёт в память.
5. Отмечает real / stub. Stub в перенос не включает.
6. Один `credId` в нескольких Instance-источниках - значение с высшим приоритетом:

   ```text
   Cloud Passport < Shared
   ```

   System в этот ряд не входит.
7. Ошибка, если один `credId` и в System, и в Instance - или в двух System-файлах.
8. Для каждого real `credId` вычисляет адрес в store:
   - `secretStore` из `--secret-store`
   - `remoteRefPath` из `--remote-ref-path-template` после подстановки `cloud` / `env`
9. Пишет в консоль отчёт: какие `credId` пойдут в перенос, из какого источника, по какому
   пути в store, и какие пропущены как stub. Это предварительный список до вызова provision -
   без паролей.
10. Пишет временный External Credential Context. В `data` Context - plaintext из памяти, не
    `_generateValue`. На каждой записи `strategy: overwrite`. 
11. Если у одного `credId` после подстановки path разный на разные env - отдельный Context на
    каждое окружение.
12. Вызывает `external-cred-provision`:
    - без `--execute` → с `--dry-run`
    - с `--execute` → apply (запись)
# UC-MIG-1. Генерация input для переноса значений в Secret Store

- [Описание](#описание)
- [Ограничения](#ограничения)
- [Входящие параметры](#входящие-параметры)
- [Предусловия](#предусловия)
- [Алгоритм](#алгоритм)
- [Результат](#результат)

## Описание

До перевода Credentials на `type: external` нужно перенести текущие значения из Instance
Repository во внешний Secret Store.

CLI собирает **input** для provision: External Credential Context YAML.

Запись в store - отдельный шаг: пользователь (или миграционная процедура) запускает
`external-cred-provision` по сгенерированному файлу.

Migration CLI:

- находит local Credentials в Instance Repository
- читает реальные значения из `data`
- по входной политике размещения строит VALS-пути
- пишет Context-файл в формате, который принимает `external-cred-provision`

Пользователь передаёт:

- Instance Repository
- политику размещения (`secretStore`, тип store, правило `remoteRefPath`)
- куда сохранить Context-файл

## Ограничения

- Типы: `usernamePassword`, `secret`.
- В Context попадают только реальные значения из `data`.
- Заглушки (`envgeneNullValue`, пустые значения) **не** попадают в Context.
- Generated `environments/.../Credentials/credentials.yml` **не** читается.
- В Context на каждой записи: plaintext из Git (не `_generateValue`), `strategy: overwrite`.

## Входящие параметры

Имена флагов черновые.

```bash
migration-cli \
  --instance-repo /path/to/instance-repository \
  --secret-store default_store \
  --store-type vault \
  --mount-path secret \
  --remote-ref-path-template "{{ cloud }}/{{ env }}" \
  --output /path/to/external-credentials-context.yaml \
  --env cluster-1/env-1
```

| Параметр                     | Обязательный | Зачем |
|------------------------------|--------------|-------|
| `--instance-repo`            | да           | Корень Instance Repository. Источник Credential-файлов и `data`. |
| `--secret-store`             | да           | ID Secret Store для сборки VALS. |
| `--store-type`               | да           | Тип store для сборки VALS (`vault`, `gcp`, `aws`, …). |
| параметры store              | да, от type  | Например `--mount-path` (Vault), `--project-id` (GCP), `--region` (AWS). |
| `--remote-ref-path-template` | да           | Правило префикса пути в store. `credId` в конец шаблона не входит. |
| `--output`                   | да           | Путь к Context YAML - input для `external-cred-provision`. |
| `--env`                      | нет          | `cluster/env`. Не указан → весь репозиторий. |

Цепочка:

```text
пользователь
  → migration-cli (repo + политика + --output)
    → отчёт в консоль (что войдёт в Context и куда)
    → файл External Credential Context
```

Путь в store: значение шаблона `remote-ref-path-template` (после подстановки `cloud` / `env`) +
`credId`. Пользователь `credId` в шаблон не дописывает.

## Предусловия

- Instance Repository читается Migration CLI.
- Credentials ещё local (`usernamePassword` / `secret`), в `data` есть исходные значения.
- Пользователь задал политику размещения (store + path template).

## Алгоритм

1. Пользователь запускает `migration-cli` с политикой размещения и `--output`.
2. CLI находит Credential-файлы в области:

   | Источник       | Где                                                   |
   |----------------|-------------------------------------------------------|
   | Cloud Passport | `*-creds.yml`                                         |
   | Shared         | `sharedMasterCredentialFiles` + unbound               |
   | System         | `/configuration/credentials/`, deployer `*-creds.yml` |

   Generated `.../Credentials/credentials.yml` не читается.

3. Берёт top-level ключи с `type: usernamePassword` или `type: secret`.
4. Читает `data`. Если значение зашифровано - расшифровывает. Кладёт в память.
5. Отмечает real / stub. Stub в Context не включает.
6. Один `credId` в нескольких Instance-источниках - значение с высшим приоритетом:

   ```text
   Cloud Passport < Shared
   ```

   System в этот ряд не входит.
7. Ошибка, если один `credId` и в System, и в Instance - или в двух System-файлах.
8. Для каждого real `credId` вычисляет адрес в store:
   - `secretStore` из `--secret-store`
   - `remoteRefPath` из `--remote-ref-path-template` после подстановки `cloud` / `env`
9. Пишет в консоль отчёт: какие `credId` войдут в Context, из какого источника, по какому
   пути в store, и какие пропущены как stub - без паролей.
10. Пишет External Credential Context в `--output`. В `data` - plaintext из памяти, не
    `_generateValue`. На каждой записи `strategy: overwrite`.
11. Если у одного `credId` после подстановки path разный на разные env - отдельный Context-файл
    на каждое окружение (или несколько документов - уточнить при реализации).
12. Завершается. `external-cred-provision` **не** вызывается.

## Результат

- На диске - Context YAML (input для `external-cred-provision`).
- В консоли - список `credId`, вошедших в Context (без паролей).
- Secret Store не изменён.
- Git / Instance Repository не изменён.

Дальше отдельно:

```bash
external-cred-provision /path/to/external-credentials-context.yaml
```

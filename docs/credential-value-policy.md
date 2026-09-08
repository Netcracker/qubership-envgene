# Credential value policy

- [Credential value policy](#credential-value-policy)
  - [Recommended characters](#recommended-characters)
  - [Forbidden characters](#forbidden-characters)
  - [Size constraints](#size-constraints)

This policy applies to credential values in EnvGene. It covers:

- `usernamePassword` credential type (applies to both `username` and `password` fields)
- `secret` credential type (applies to the `secret` value)

## Recommended characters

- Letters: `a-z`, `A-Z`
- Digits: `0-9`
- Basic symbols: `-` `_` `.` `:` `/`
- Grouping: `(` `)` `[` `]` `{` `}`
- Angle brackets: `<` `>`
- Common symbols: `@` `#` `%` `+` `=` `,` `;` `~` `&` `*` `|` `^` `` ` `` `?` `!`

## Forbidden characters

Do not use the following characters in credential values:

- `"` (double quote)
- `'` (single quote)
- `\` (backslash)
- `$` (dollar sign)

## Size constraints

Recommended maximum credential value size:**50 KB**.
Credential values exceeding 50 KB may cause performance issues during encryption, storage and transmission.

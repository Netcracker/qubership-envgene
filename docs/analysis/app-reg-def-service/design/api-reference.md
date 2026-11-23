# API reference

> _Placeholder. The human-readable companion to openapi.yaml. openapi.yaml is the machine-readable
> contract, this page explains the semantics._

## Conventions

> _Placeholder. Base path, authentication, content types, the optional zone parameter, and the error
> model._

## resolve and resolveBatch

> _Placeholder. Input (app:version, optional zone, or a list) and the response: artifact download-info
> (DD or SD), all registry sections normalized to v2, auth-ready (blind), and appdef metadata._

## getRegDef

> _Placeholder. Returns the normalized v2 reg def object by name. getAppDef and the list endpoints are open
> questions (O2, O3)._

## create and update

> _Placeholder. Separate operations, each returns the written object. Create fails if the def exists,
> update fails if it is absent. The name is validated or normalized to the kebab convention._

## Error model

> _Placeholder. Not found, invalid def, name conflict, and the write conflict (409)._

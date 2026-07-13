# Cleanup application parameters

- [Cleanup application parameters](#cleanup-application-parameters)
  - [Overview](#overview)
  - [Parameters](#parameters)

## Overview

This document lists the parameters consumed by the cleanup application during a CLEAN run of the
instance pipeline.

## Parameters

| Subsystem     | Cleanup context                          | Pipeline context                             |
|---------------|------------------------------------------|----------------------------------------------|
| ArgoCD        | `ARGOCD_URL`                             | `DCL_CONFIG_ARGOCD_URL`                      |
| ArgoCD        | `ARGOCD_USER`                            | `DCL_CONFIG_ARGOCD_USER`                     |
| ArgoCD        | `ARGOCD_PASSWORD`                        | `DCL_CONFIG_ARGOCD_PASSWORD`                 |
| ArgoCD        | `ARGOCD_AUTH_SSO_URL`                    | `DCL_CONFIG_ARGOCD_AUTH_SSO_URL`             |
| ArgoCD        | `ARGOCD_AUTH_SSO_CLIENT_ID`              | `DCL_CONFIG_ARGOCD_AUTH_SSO_CLIENT_ID`       |
| ArgoCD        | `ARGOCD_AUTH_SSO_CLIENT_SECRET`          | `DCL_CONFIG_ARGOCD_AUTH_SSO_CLIENT_SECRET`   |
| Cloud         | `K8S_TOKEN`                              |                                              |
| Cloud         | `CLOUD_PROTOCOL`                         |                                              |
| Cloud         | `CLOUD_API_HOST`                         |                                              |
| Cloud         | `CLOUD_API_PORT`                         |                                              |
| Control plane | `PRIVATE_GATEWAY_URL`                    |                                              |
| DBaaS         | `DBAAS_ENABLED`                          |                                              |
| DBaaS         | `API_DBAAS_ADDRESS`                      |                                              |
| DBaaS         | `DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME` |                                              |
| DBaaS         | `DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD` |                                              |
| Consul        | `CONSUL_ENABLED`                         |                                              |
| Consul        | `CONSUL_URL`                             |                                              |
| Consul        | `CONSUL_PUBLIC_URL`                      |                                              |
| Consul        | `CONSUL_ADMIN_TOKEN`                     |                                              |
| MaaS          | `MAAS_ENABLED`                           |                                              |
| MaaS          | `MAAS_INTERNAL_ADDRESS`                  |                                              |
| MaaS          | `MAAS_CREDENTIALS_USERNAME`              |                                              |
| MaaS          | `MAAS_CREDENTIALS_PASSWORD`              |                                              |
| CDN           | `CDN_STORAGE_SERVER_URL`                 |                                              |
| CDN           | `CDN_STORAGE_URL`                        |                                              |
| CDN           | `CDN_STORAGE_USERNAME`                   |                                              |
| CDN           | `CDN_STORAGE_USER`                       |                                              |
| CDN           | `CDN_STORAGE_PASSWORD`                   |                                              |
| CDN           | `CDN_STORAGE_PROVIDER`                   |                                              |
| CDN           | `CDN_STORAGE_READ_TIMEOUT`               |                                              |
| CDN           | `CDN_STORAGE_REGION`                     |                                              |
| CDN           | `S3_REGION`                              |                                              |
| CDN           | `DISABLE_S3_SSL`                         |                                              |
| CDN           | `DISABLE_BUCKETS_CLEANUP`                |                                              |
| Certificates  | `SSL_SECRET_VALUE`                       |                                              |
| Certificates  | `CA_BUNDLE_CERTIFICATE`                  |                                              |

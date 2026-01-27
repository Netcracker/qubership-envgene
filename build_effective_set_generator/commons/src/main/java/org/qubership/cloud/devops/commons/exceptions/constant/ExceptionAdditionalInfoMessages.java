/*
 * Copyright 2024-2025 NetCracker Technology Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.qubership.cloud.devops.commons.exceptions.constant;

public class ExceptionAdditionalInfoMessages {
    public static final String REGISTRY_MAVEN_CONFIG_NOT_FOUND = "Registry definition with name '%s' doesn't have mandatory Maven Config definition.";
    public static final String REGISTRY_DOCKER_CONFIG_NOT_FOUND = "Registry definition with name '%s' doesn't have mandatory Docker Config definition.";
    public static final String APPLICATION_NOT_FOUND_FORMAT = "Application data not found for %s Please check logged errors";
    public static final String APPLICATION_MULTIPLE_NOT_FOUND_FORMAT = "Application definitions with names '%s' couldn't be found.";
    public static final String TENANT_GLOBAL_E2E_PARAMETERS_NOT_FOUND = "Tenant definition with name '%s' doesn't have mandatory Global E2E Parameters definition.";

    public static final String CLOUD_MAAS_NOT_FOUND = "Cloud definition with name '%s' doesn't have mandatory MaaS config definition.";
    public static final String CLOUD_VAULT_NOT_FOUND = "Cloud definition with name '%s' doesn't have mandatory Vault config definition.";
    public static final String CLOUD_CONSUL_NOT_FOUND = "Cloud definition with name '%s' doesn't have mandatory Consul config definition.";
    public static final String ENTITY_NOT_FOUND = "%s data is unavailable. Check if file is present or logs for any errors";

    public static final String ENTITY_NOT_FOUND_PARAMS = "%s data is unavailable.Check if file is present or logs for any errors.Might impact some parameters";


}

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

package org.qubership.cloud.devops.commons.utils.constant;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

import java.util.Arrays;
import java.util.List;

@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class ApplicationConstants {
    public static final String SERVICES = "services";
    public static final String CONFIGURATIONS = "configurations";
    public static final String FRONTENDS = "frontends";
    public static final String SMARTPLUG = "smartplug";
    public static final String CDN = "cdn";
    public static final String SAMPLREPO = "sampleRepo";
    public static final String DEPLOY_DESC = "deploy_desc";
    public static final String COMMON_DEPLOY_DESC = "common_deploy_desc";
    public static final String PER_SERVICE_DEPLOY_PARAMS = "per_service_deploy_params";
    public static final String APPR_CHART_NAME = "appChartName";
    public static final String APPLICATION_ZIP = "application/zip";
    public static final String APPLICATION_XML = "application/xml";
    public static final String APPLICATION_VND_OSGI_BUNDLE = "application/vnd.osgi.bundle";
    public static final String APPLICATION_JAVA_ARCHIVE = "application/java-archive";
    public static final String APPLICATION_VND_QUBERSHIP_CONFIGURATION_SMARTPLUG = "application/vnd.qubership.configuration.smartplug";
    public static final String APPLICATION_VND_QUBERSHIP_CONFIGURATION_FRONTEND = "application/vnd.qubership.configuration.frontend";
    public static final String APPLICATION_VND_QUBERSHIP_CONFIGURATION_CDN = "application/vnd.qubership.configuration.cdn";
    public static final String APPLICATION_VND_QUBERSHIP_CONFIGURATION = "application/vnd.qubership.configuration";
    public static final String APPLICATION_VND_QUBERSHIP_SERVICE = "application/vnd.qubership.service";
    public static final String APPLICATION_OCTET_STREAM = "application/octet-stream";
    public static final String K8S_TOKEN = "K8S_TOKEN";
    public static final List<String> SECURED_KEYS = Arrays.asList("DBAAS_AGGREGATOR_USERNAME", "DBAAS_AGGREGATOR_PASSWORD",
            "DBAAS_CLUSTER_DBA_CREDENTIALS_USERNAME", "DBAAS_CLUSTER_DBA_CREDENTIALS_PASSWORD", "MAAS_CREDENTIALS_USERNAME",
            "MAAS_CREDENTIALS_PASSWORD", "VAULT_TOKEN", "CONSUL_ADMIN_TOKEN", "SSL_SECRET_VALUE");
}

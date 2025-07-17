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

@NoArgsConstructor(access = AccessLevel.PRIVATE)
public class NamespaceConstants {
    public static final String PRIVATE_GATEWAY_URL = "PRIVATE_GATEWAY_URL";
    public static final String PRIVATE_IDENTITY_PROVIDER_URL = "PRIVATE_IDENTITY_PROVIDER_URL";

    public static final String NAMESPACE = "NAMESPACE";
    public static final String BUILD_TAG_NEW = "BUILD_TAG_NEW";

    public static final String PUBLIC_GATEWAY_URL = "PUBLIC_GATEWAY_URL";
    public static final String PUBLIC_IDENTITY_PROVIDER_URL = "PUBLIC_IDENTITY_PROVIDER_URL";
    public static final String GATEWAY_URL = "GATEWAY_URL";
    public static final String STATIC_CACHE_SERVICE_ROUTE_HOST = "STATIC_CACHE_SERVICE_ROUTE_HOST";
    public static final String PARAMETER_SET = "parameterSet";
    public static final String APP = "app";
    public static final String E2E = "e2e";
    public static final String CONFIG_SERVER = "config-server";
    public static final String SSL_SECRET = "SSL_SECRET";
    public static final String ORIGIN_NAMESPACE = "ORIGIN_NAMESPACE";

}

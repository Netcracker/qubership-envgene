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
package org.qubership.cloud.devops.commons.utils;

import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Getter;

@AllArgsConstructor(access = AccessLevel.PRIVATE)
@Getter
public enum ServiceArtifactType {
    SMART_PLUG("application/vnd.qubership.configuration.smartplug", "application/vnd.osgi.bundle"),
    FRONT_END("application/vnd.qubership.configuration.frontend", "application/zip"),
    CDN("application/vnd.qubership.configuration.cdn", "application/zip"),
    CONFIGURATION("application/vnd.qubership.configuration", "application/zip");
    private final String serviceMimeType;

    private final String artifactMimeType;

    public static ServiceArtifactType of(String mimeType) {
        if (SMART_PLUG.getServiceMimeType().equalsIgnoreCase(mimeType)) {
            return SMART_PLUG;
        }
        if (FRONT_END.getServiceMimeType().equalsIgnoreCase(mimeType)) {
            return FRONT_END;
        }
        if (CDN.getServiceMimeType().equalsIgnoreCase(mimeType)) {
            return CDN;
        }
        if (CONFIGURATION.getServiceMimeType().equalsIgnoreCase(mimeType)) {
            return CONFIGURATION;
        }
        return null;
    }
}

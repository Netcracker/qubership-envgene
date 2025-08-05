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

package org.qubership.cloud.devops.cli.utils;

import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import org.cyclonedx.model.Component;
import org.cyclonedx.model.ExternalReference;
import org.cyclonedx.model.Property;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.commons.pojo.bom.ApplicationBomDTO;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImpl implements BomReaderUtils {
    private final BomReaderUtilsImplV2 bomReaderUtilsImplV2;
    private final BomReaderUtilsImplV1 bomReaderUtilsImplV1;
    private final SharedData sharedData;

    public BomReaderUtilsImpl(BomReaderUtilsImplV2 bomReaderUtilsImplV2, BomReaderUtilsImplV1 bomReaderUtilsImplV1, SharedData sharedData) {
        this.bomReaderUtilsImplV2 = bomReaderUtilsImplV2;
        this.bomReaderUtilsImplV1 = bomReaderUtilsImplV1;
        this.sharedData = sharedData;
    }

    public ApplicationBomDTO getAppServicesWithProfiles(String appName, String appFileRef, String baseline, Profile override) {
        if ("v2.0".equalsIgnoreCase(sharedData.getEffectiveSetVersion())) {
            return bomReaderUtilsImplV2.getAppServicesWithProfiles(appName, appFileRef, baseline, override);
        }
        return bomReaderUtilsImplV1.getAppServicesWithProfiles(appName, appFileRef, baseline, override);
    }

    public String getExternalRefValue(Component component, String propertyName) {
        return component.getExternalReferences().stream()
                .filter(ref -> propertyName.equals(ref.getType().getTypeName()))
                .map(ExternalReference::getUrl)
                .findFirst().orElse(null);
    }

    public String getPropertyValue(Component component, String propertyName) {
        return component.getProperties().stream()
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse(null);
    }
}

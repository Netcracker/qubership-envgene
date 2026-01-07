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

package org.qubership.cloud.devops.cli.service.implementation;

import lombok.extern.slf4j.Slf4j;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.exceptions.*;
import org.qubership.cloud.devops.commons.pojo.profile.model.ApplicationProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ParameterProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.ServiceProfile;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.service.interfaces.TenantConfigurationService;
import org.qubership.cloud.devops.commons.pojo.profile.dto.ProfileFullDto;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.utils.Parameter;
import org.qubership.cloud.devops.commons.utils.mapper.ProfileMapper;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@ApplicationScoped
public class ProfileServiceCliImpl implements ProfileService {
    private final InputData inputData;

    private final ProfileMapper profileMapper;

    private final TenantConfigurationService tenantConfigurationService;

    @Inject
    public ProfileServiceCliImpl(InputData inputData,
                                 ProfileMapper profileMapper,
                                 TenantConfigurationService tenantConfigurationService) {
        this.inputData = inputData;
        this.profileMapper = profileMapper;
        this.tenantConfigurationService = tenantConfigurationService;
    }

    @Override
    public ProfileFullDto getProfileDtoByTenant(String tenantName, String profileName) {
        ProfileFullDto profileFullDto =  inputData.getProfileFullDtoMap().get(profileName);
        if (profileFullDto == null) {
            throw new NotFoundException(String.format("Profile: %s not found, check if the file is present", profileName));
        }
        return profileFullDto;
    }

    @Override
    public Profile getProfileByTenant(String tenantName, String profileName) {
        if (profileName == null || profileName.isEmpty()) {
            return null;
        }
        ProfileFullDto profileFullDto = getProfileDtoByTenant(tenantName, profileName);
        Tenant tenant = tenantConfigurationService.getTenantByName(tenantName);
        return profileMapper.convertToEntity(profileFullDto, tenant);
    }

    public void setOverrideProfiles(String appName, String serviceName, Profile overrideProfile, Map<String, Object> profileValues) {
        expandDottedKeys(profileValues);
        if (overrideProfile != null) {
            ApplicationProfile override = overrideProfile.getApplications().stream()
                    .filter(app -> appName.equals(app.getName()))
                    .findFirst()
                    .orElse(null);

            if (override != null) {
                ServiceProfile serviceOverride = override.getServices().stream()
                        .filter(serviceProfileEntity -> serviceName.equals(serviceProfileEntity.getName()))
                        .findFirst().orElse(null);
                if (serviceOverride != null) {
                    for (ParameterProfile param : serviceOverride.getParameters()) {
                        putNestedValue(profileValues, param.getName(), param.getValue());
                    }
                }
            }
        }
    }

    public void setOverrideProfilesWithOrigin(String appName, String serviceName, Profile overrideProfile, Map<String, Object> profileValues, String origin) {
        expandDottedKeys(profileValues);
        if (overrideProfile != null) {
            ApplicationProfile override = overrideProfile.getApplications().stream()
                    .filter(app -> appName.equals(app.getName()))
                    .findFirst()
                    .orElse(null);

            if (override != null) {
                ServiceProfile serviceOverride = override.getServices().stream()
                        .filter(serviceProfileEntity -> serviceName.equals(serviceProfileEntity.getName()))
                        .findFirst().orElse(null);
                if (serviceOverride != null) {
                    for (ParameterProfile param : serviceOverride.getParameters()) {
                        putNestedValue(profileValues, param.getName(), new Parameter(param.getValue(),origin,false) );
                    }
                }
            }
        }
    }

    @SuppressWarnings("unchecked")
    private void putNestedValue(Map<String, Object> profileValues, String key, Object value) {
        String[] parts = key.split("\\.");
        Map<String, Object> current = profileValues;

        for (int i = 0; i < parts.length - 1; i++) {
            current = (Map<String, Object>) current.computeIfAbsent(parts[i], k -> new LinkedHashMap<String, Object>());
        }
        current.put(parts[parts.length - 1], value);
    }

    @SuppressWarnings("unchecked")
    private void expandDottedKeys(Map<String, Object> map) {
        List<String> dottedKeys = map.keySet().stream()
                .filter(k -> k.contains("."))
                .toList();

        for (String dottedKey : dottedKeys) {
            Object val = map.remove(dottedKey);
            String[] parts = dottedKey.split("\\.");

            Map<String, Object> current = map;
            for (int i = 0; i < parts.length - 1; i++) {
                current = (Map<String, Object>) current.computeIfAbsent(
                        parts[i],
                        k -> new LinkedHashMap<String, Object>()
                );
            }
            current.put(parts[parts.length - 1], val);
        }
    }

}

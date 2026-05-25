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

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.model.Namespace;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.service.interfaces.NamespaceConfigurationService;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.utils.convert.PojoConverterUtils;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND;

@ApplicationScoped
public class NamespaceConfigurationServiceCliImpl implements NamespaceConfigurationService {

    private final InputData inputData;

    private final ProfileService profileService;


    @Inject
    public NamespaceConfigurationServiceCliImpl(InputData inputData,
                                                ProfileService profileService) {
        this.inputData = inputData;
        this.profileService = profileService;
    }

    @Override
    public Namespace getNamespaceByCloud(String cloudName, String tenantName, String namespace) {
        NamespaceDTO namespaceDTO = inputData.getNamespaceDTOMap().get(namespace);
        if (namespaceDTO == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Namespace "));
        }
        String profileName = namespaceDTO.getProfile() != null ? namespaceDTO.getProfile().getName() : null;
        Profile profileEntity = profileService.getProfileByTenant(tenantName, profileName);
        return PojoConverterUtils.convertDTOToNamespace(tenantName,
                cloudName, namespaceDTO, profileEntity);
    }
}

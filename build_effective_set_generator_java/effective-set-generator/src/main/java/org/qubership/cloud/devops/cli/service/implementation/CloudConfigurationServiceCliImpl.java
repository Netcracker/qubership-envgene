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
import org.qubership.cloud.devops.commons.pojo.clouds.dto.CloudDTO;
import org.qubership.cloud.devops.commons.pojo.clouds.model.Cloud;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.service.interfaces.CloudConfigurationService;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.utils.convert.PojoConverterUtils;

@ApplicationScoped
public class CloudConfigurationServiceCliImpl implements CloudConfigurationService {

    private final InputData inputData;
    private final ProfileService profileService;


    @Inject
    public CloudConfigurationServiceCliImpl(InputData inputData,
                                            ProfileService profileService) {
        this.inputData = inputData;
        this.profileService = profileService;
    }

    @Override
    public Cloud getCloudByTenant(String tenant, String cloud) {
        CloudDTO cloudDTO = inputData.getCloudDTO();
        String profileName = cloudDTO.getProfile() != null ? cloudDTO.getProfile().getName() : null;
        Profile profileEntity = profileService.getProfileByTenant(tenant, profileName);
        return PojoConverterUtils.convertDTOToCloud(tenant, cloudDTO, profileEntity);
    }
}

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

package org.qubership.cloud.devops.commons.utils.mapper;

import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages;
import org.qubership.cloud.devops.commons.pojo.tenants.model.Tenant;
import org.qubership.cloud.devops.commons.service.interfaces.ApplicationService;
import org.qubership.cloud.devops.commons.pojo.profile.dto.ProfileFullDto;
import org.qubership.cloud.devops.commons.pojo.profile.model.ApplicationProfile;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.modelmapper.ModelMapper;

import java.util.List;
import java.util.stream.Collectors;

import static java.util.Objects.isNull;

@ApplicationScoped
public class ProfileMapper {

    private final ModelMapper mapper;
    private final ApplicationService applicationService;

    @Inject
    public ProfileMapper(ModelMapper mapper, ApplicationService applicationService) {
        this.mapper = mapper;
        this.applicationService = applicationService;
    }

    public Profile convertToEntity(ProfileFullDto profileDto, Tenant tenant) {
        Profile profileEntity = mapper.map(profileDto, Profile.class);
        if (profileEntity.getApplications() != null) {
            profileEntity.getApplications().forEach(a -> {
                a.getServices().forEach(s -> {
                    s.getParameters().forEach(p -> p.setServiceProfile(s));
                    s.setApplicationProfile(a);
                });
                a.setProfile(profileEntity);
            });
        }
        profileEntity.setTenant(tenant);
        return profileEntity;
    }

}

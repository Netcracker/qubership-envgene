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
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationLinkDTO;
import org.qubership.cloud.devops.commons.pojo.clouds.dto.CloudDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.service.interfaces.ApplicationService;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import java.util.List;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND;


@ApplicationScoped
@Slf4j
public class ApplicationServiceCliImpl implements ApplicationService {

    private final InputData inputData;

    @Inject
    public ApplicationServiceCliImpl(InputData inputData) {
        this.inputData = inputData;
    }

    @Override
    public Application getByName(String applicationName,  String namespace) {
        NamespaceDTO namespaceDTO = inputData.getNamespaceDTOMap().get(namespace);
        if (namespaceDTO == null) {
            return null;
        }
        ApplicationLinkDTO application = getApplicationLinkDTO(applicationName, namespaceDTO.getApplications());

        if (application == null) {
            CloudDTO cloudDTO = inputData.getCloudDTO();
            ApplicationLinkDTO cloudapp = getApplicationLinkDTO(applicationName, cloudDTO.getApplications());
            if (cloudapp == null) {
                log.warn(String.format(ENTITY_NOT_FOUND, "Application"));
                return null;
            }
        }
        return Application.builder().name(application.getName()).technicalParams(application.getTechnicalConfigurationParameters())
                .params(application.getDeployParameters()).build();
    }

    private static ApplicationLinkDTO getApplicationLinkDTO(String applicationName, List<ApplicationLinkDTO> applications) {
        ApplicationLinkDTO appDTO = applications
                .stream()
                .filter(app -> app.getName().equals(applicationName))
                .findFirst()
                .orElse(null);
        return appDTO;
    }

}

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

import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.exceptions.NotFoundException;
import org.qubership.cloud.devops.commons.pojo.applications.model.Application;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationLinkDTO;
import org.qubership.cloud.devops.commons.service.interfaces.ApplicationService;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import static org.qubership.cloud.devops.commons.exceptions.constant.ExceptionAdditionalInfoMessages.ENTITY_NOT_FOUND;


@ApplicationScoped
public class ApplicationServiceCliImpl implements ApplicationService {

    private final InputData inputData;

    @Inject
    public ApplicationServiceCliImpl(InputData inputData) {
        this.inputData = inputData;
    }

    @Override
    public Application getByName(String applicationName) {
        ApplicationLinkDTO applicationDTO = getApplicationFromYaml(applicationName);
        if (applicationDTO == null) {
            throw new NotFoundException(String.format(ENTITY_NOT_FOUND, "Application"));
        }
        return Application.builder().name(applicationDTO.getName()).technicalParams(applicationDTO.getTechnicalConfigurationParameters())
                .params(applicationDTO.getDeployParameters()).build();
    }

    @Override
    public ApplicationLinkDTO getApplicationFromYaml(String applicationName) {
        return inputData.getApplicationLinkDTOMap().get(applicationName);
    }
}

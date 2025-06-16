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
import org.cyclonedx.model.Bom;
import org.cyclonedx.model.Component;
import org.qubership.cloud.devops.commons.exceptions.BomProcessingException;
import org.qubership.cloud.devops.commons.pojo.bom.ApplicationBomDTO;
import org.qubership.cloud.devops.commons.pojo.bom.EntitiesMap;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;

import java.io.File;
import java.util.regex.Pattern;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImplV1 {
    private static final Pattern MAVEN_PATTERN = Pattern.compile("(pkg:maven.*)\\?registry_id=(.*)&repository_id=(.*)");
    private final FileDataConverter fileDataConverter;
    private final RegistryConfigurationService registryConfigurationService;
    private final BomCommonUtils bomCommonUtils;

    public BomReaderUtilsImplV1(FileDataConverter fileDataConverter, RegistryConfigurationService registryConfigurationService, BomCommonUtils bomCommonUtils) {
        this.fileDataConverter = fileDataConverter;
        this.registryConfigurationService = registryConfigurationService;
        this.bomCommonUtils = bomCommonUtils;
    }

    public ApplicationBomDTO getAppServicesWithProfiles(String appName, String appFileRef, String baseline, Profile override) {
        Bom bomContent = fileDataConverter.parseSbomFile(new File(appFileRef));
        EntitiesMap entitiesMap = new EntitiesMap();
        try {
            Component component = bomContent.getMetadata().getComponent();
            if (component.getMimeType().equals("application/vnd.qubership.application")) {
                ApplicationBomDTO applicationBomDto = component.getComponents()
                        .stream()
                        .map(subComp -> {
                            RegistrySummaryDTO registrySummaryDTO = bomCommonUtils.getRegistrySummaryDTO(subComp, MAVEN_PATTERN);
                            String mavenRepoName = registryConfigurationService.getMavenRepoForApp(registrySummaryDTO);
                            return ApplicationBomDTO.builder().name(appName).artifactId(subComp.getName()).groupId(subComp.getGroup())
                                    .version(subComp.getVersion()).mavenRepo(mavenRepoName).build();
                        }).findFirst().orElse(null);

                bomCommonUtils.getEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override);

                if (applicationBomDto != null) {
                    applicationBomDto.setServices(entitiesMap.getServiceMap());
                    applicationBomDto.setConfigurations(entitiesMap.getConfigurationMap());
                    applicationBomDto.setFrontends(entitiesMap.getFrontEndMap());
                    applicationBomDto.setSmartplugs(entitiesMap.getSmartplugMap());
                    applicationBomDto.setCdn(entitiesMap.getCdnMap());
                    applicationBomDto.setSampleRepo(entitiesMap.getRepoMap());
                }
                return applicationBomDto;
            }
        } catch (Exception e) {
            throw new BomProcessingException("error reading application sbom \n Root Cause: " + e.getMessage());
        }
        return null;
    }

}

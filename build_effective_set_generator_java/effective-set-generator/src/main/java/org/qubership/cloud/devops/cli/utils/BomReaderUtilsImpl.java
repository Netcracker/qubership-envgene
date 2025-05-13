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

import com.fasterxml.jackson.core.type.TypeReference;
import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import org.cyclonedx.model.*;
import org.cyclonedx.model.component.data.ComponentData;
import org.cyclonedx.model.component.data.Content;
import org.qubership.cloud.devops.commons.pojo.bom.EntitiesMap;
import org.qubership.cloud.devops.commons.exceptions.BomProcessingException;
import org.qubership.cloud.devops.commons.pojo.bom.*;
import org.qubership.cloud.devops.commons.pojo.profile.model.Profile;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistrySummaryDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.ProfileService;
import org.qubership.cloud.devops.commons.service.interfaces.RegistryConfigurationService;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;
import org.qubership.cloud.parameters.processor.dto.DeploymentConfig;

import java.io.File;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage.REGISTRY_EXTRACT_FAILED;
import static org.qubership.cloud.devops.commons.utils.ConsoleLogger.logError;

@ApplicationScoped
@Slf4j
public class BomReaderUtilsImpl implements BomReaderUtils {
    private static final Pattern MAVEN_PATTERN = Pattern.compile("(pkg:maven.*)\\?registry_id=(.*)&repository_id=(.*)");

    private static final Pattern DOCKER_PATTERN = Pattern.compile("(pkg:docker.*)\\?registry_id=(.*)&repository_id=(.*)");
    private final FileDataConverter fileDataConverter;

    private final ProfileService profileService;

    private final RegistryConfigurationService registryConfigurationService;

    public BomReaderUtilsImpl(FileDataConverter fileDataConverter, ProfileService profileService, RegistryConfigurationService registryConfigurationService) {
        this.fileDataConverter = fileDataConverter;
        this.profileService = profileService;
        this.registryConfigurationService = registryConfigurationService;
    }

    public ApplicationBomDTO getAppServicesWithProfiles(String appName, String appFileRef, String baseline, Profile override) {
        Bom bomContent = fileDataConverter.parseSbomFile(new File(appFileRef));
        EntitiesMap entitiesMap = new EntitiesMap();
        try {
            Component component = bomContent.getMetadata().getComponent();
            if (component.getMimeType().contains("application")) {
                ApplicationBomDTO applicationBomDto = component.getComponents()
                        .stream()
                        .map(subComp -> {
                            RegistrySummaryDTO registrySummaryDTO = getRegistrySummaryDTO(subComp, MAVEN_PATTERN);
                            String mavenRepoName = registryConfigurationService.getMavenRepoForApp(registrySummaryDTO);
                            return ApplicationBomDTO.builder().name(appName).artifactId(subComp.getName()).groupId(subComp.getGroup())
                                    .version(subComp.getVersion()).mavenRepo(mavenRepoName).build();
                        }).findFirst().orElse(null);

                getEntities(entitiesMap, bomContent.getComponents(), appName, baseline, override);

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
            throw new BomProcessingException("Error reading application sbom due to "+e.getMessage());
        }
        return null;
    }

    private void getEntities(EntitiesMap entitiesMap, List<Component> components, String appName, String baseline, Profile override) {
        for (Component component : components) {
            if (component.getMimeType().equals("application/vnd.qubership.service")) {
                processServiceComponent(entitiesMap.getServiceMap(),component, appName, baseline, override);
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.smartplug")) {
                getOtherComponents(entitiesMap.getSmartplugMap(), component, "spar");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.frontend")) {
                getOtherComponents(entitiesMap.frontEndMap, component, "zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration")) {
                getOtherComponents(entitiesMap.getConfigurationMap(), component, "zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.cdn")) {
                getOtherComponents(entitiesMap.getCdnMap(), component, "zip");
            } else if (component.getMimeType().equals("application/vnd.qubership.configuration.sampleRepo")) {
                getOtherComponents(entitiesMap.getRepoMap(), component, "zip");
            }
        }
    }

    private void getOtherComponents(Map<String, Map<String, Object>> configMap, Component component, String type) {
        Map<String, Object> configParams = new TreeMap<>();
        Component subComponent = component.getComponents().stream().filter(artifact -> artifact.getMimeType().equals(type)).findFirst().get();
        configParams.put("artifact.gav", String.format("%s:%s:%s", subComponent.getName(),subComponent.getGroup(), subComponent.getVersion()));
        configParams.put("artifact.groupId", subComponent.getGroup());
        configParams.put("artifact.artifactId", subComponent.getName());
        configParams.put("artifact.version", subComponent.getVersion());
        configMap.put(component.getName(), configParams);
    }

    private static RegistrySummaryDTO getRegistrySummaryDTO(Component component, Pattern pattern) {
        Matcher regMatcher = pattern.matcher(component.getPurl());
        RegistrySummaryDTO registrySummaryDTO= null;
        if (regMatcher.find()) {
            String registryName = regMatcher.group(2);
            registryName = registryName.replace("%20", " ");
            String repoId = regMatcher.group(3);
            registrySummaryDTO =RegistrySummaryDTO.builder().name(registryName).repoId(repoId)
                    .build();
        } else {
            logError(String.format(REGISTRY_EXTRACT_FAILED, component.getName()));
        }
        return registrySummaryDTO;
    }

    private void processServiceComponent(Map<String, Map<String, Object>> serviceMap , Component component, String appName, String baseline, Profile override) {
        String gitBranch = getPropertyValue(component, "git_branch");
        String imageType = getPropertyValue(component, "image_type");

        String imageName = null;
        String dockerRepo = null;
        String dockerTag = null;
        boolean isFacadeGateway = false;
        RegistrySummaryDTO registrySummaryDTO = null;
        Map<String, String> profileValues = new HashMap<>();

        for (Component subComponent : component.getComponents()) {
            switch (subComponent.getType().getTypeName()) {
                case "container":
                    imageName = subComponent.getName();
                    dockerRepo = subComponent.getGroup();
                    dockerTag = subComponent.getVersion();
                    registrySummaryDTO = getRegistrySummaryDTO(subComponent, DOCKER_PATTERN);
                    break;

                case "data":
                    if ("deployment-configuration".equals(subComponent.getName())) {
                        isFacadeGateway = extractGatewayFlag(subComponent);
                    } else if ("resource-profile-baselines".equals(subComponent.getName())) {
                        profileValues = extractProfileValues(subComponent, appName, component.getName(), override, baseline);
                    }
                    break;
            }
        }

        Map<String, Object> serviceParams = new HashMap<>();
        serviceParams.put("SERVICE_NAME", component.getName());
        serviceParams.put("SERVICE_TYPE", imageType != null? imageType : "");
        serviceParams.put("TAG", dockerTag != null ? dockerTag : "");
        serviceParams.put("DOCKER_TAG", imageName != null ? imageName : "");
        serviceParams.put("BRANCH", gitBranch);
        serviceParams.put("IMAGE_REPOSITORY", String.format("%s/%s/%s", registryConfigurationService.getDockerRepoForService(registrySummaryDTO), dockerRepo, imageName));
        if (isFacadeGateway) {
            serviceParams.put("OPENSHIFT_SERVICE_NAME", component.getName() + "v1" );
            serviceParams.put("DEPLOYMENT_RESOURCE_NAME", component.getName() + "v1");
            serviceParams.put("DEPLOYMENT_VERSION", "v1");
        }
        if (profileValues != null && !profileValues.isEmpty()) {
            serviceParams.putAll(profileValues);
        }
        serviceMap.put(component.getName(), serviceParams);
    }

    public String getPropertyValue(Component component, String propertyName) {
        return component.getProperties().stream()
                .filter(property -> propertyName.equals(property.getName()))
                .map(Property::getValue)
                .findFirst()
                .orElse(null);
    }

    public String getExternalRefValue(Component component, String propertyName) {
        return component.getExternalReferences().stream()
                .filter(ref -> propertyName.equals(ref.getType().getTypeName()))
                .map(ExternalReference::getUrl)
                .findFirst().orElse(null);
    }

    private boolean extractGatewayFlag(Component dataComponent) {
        return dataComponent.getData().stream()
                .map(ComponentData::getContents)
                .map(Content::getAttachment)
                .map(AttachmentText::getText)
                .map(encodedText -> fileDataConverter.decodeAndParse(encodedText, DeploymentConfig.class))
                .map(deploymentConfig -> deploymentConfig.getDeployOptions().isGenerateFacadeGateway())
                .findFirst()
                .orElse(false);
    }

    private Map<String, String> extractProfileValues(Component dataComponent, String appName, String serviceName ,
                                                     Profile overrideProfile, String baseline) {
        Map<String, String> profileValues = new HashMap<>();

        for (ComponentData data : dataComponent.getData()) {
            if (baseline.equals(data.getName().split("\\.")[0])) {
                Content content = data.getContents();
                String encodedText = content.getAttachment().getText();
                profileValues = fileDataConverter.decodeAndParse(encodedText, new TypeReference<HashMap<String, String>>() {
                });

                profileService.setOverrideProfiles(appName, serviceName, overrideProfile, profileValues);
                break;
            }
        }
        return profileValues;
    }
}

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

package org.qubership.cloud.devops.cli.repository.implementation;


import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.collections4.MapUtils;
import org.apache.commons.io.FilenameUtils;
import org.cyclonedx.model.Bom;
import org.cyclonedx.model.Component;
import org.json.JSONArray;
import org.json.JSONObject;
import org.qubership.cloud.devops.cli.constants.GenericConstants;
import org.qubership.cloud.devops.cli.exceptions.constants.ExceptionMessage;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SBApplicationDTO;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SolutionBomDTO;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SolutionDescriptorDTO;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.utils.FileSystemUtils;
import org.qubership.cloud.devops.commons.exceptions.FileParseException;
import org.qubership.cloud.devops.commons.pojo.applications.dto.ApplicationLinkDTO;
import org.qubership.cloud.devops.commons.pojo.bg.BgDomainEntityDTO;
import org.qubership.cloud.devops.commons.pojo.clouds.dto.CloudDTO;
import org.qubership.cloud.devops.commons.pojo.consumer.ConsumerDTO;
import org.qubership.cloud.devops.commons.pojo.consumer.Property;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;
import org.qubership.cloud.devops.commons.pojo.cs.CompositeStructureDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespaceDTO;
import org.qubership.cloud.devops.commons.pojo.namespaces.dto.NamespacePrefixDTO;
import org.qubership.cloud.devops.commons.pojo.profile.dto.ProfileFullDto;
import org.qubership.cloud.devops.commons.pojo.registries.dto.RegistryDTO;
import org.qubership.cloud.devops.commons.pojo.tenants.dto.TenantDTO;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataRepository;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;

import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.*;
import java.util.stream.Collectors;

import static org.qubership.cloud.devops.cli.constants.GenericConstants.*;


@ApplicationScoped
public class FileDataRepositoryImpl implements FileDataRepository {
    private final FileDataConverter fileDataConverter;
    private final InputData inputData;
    private final String sourceDir;
    private final SharedData sharedData;

    private final BomReaderUtils bomReaderUtils;
    private final FileSystemUtils fileSystemUtils;


    @Inject
    public FileDataRepositoryImpl(FileDataConverter fileDataConverter,
                                  SharedData sharedData,
                                  InputData inputData,
                                  BomReaderUtils bomReaderUtils,
                                  FileSystemUtils fileSystemUtils) {
        this.fileDataConverter = fileDataConverter;
        this.inputData = inputData;
        this.sharedData = sharedData;
        this.bomReaderUtils = bomReaderUtils;
        this.fileSystemUtils = fileSystemUtils;
        this.sourceDir = String.format("%s/%s", sharedData.getEnvsPath(), sharedData.getEnvId());
    }

    /*  **
     * Reads files from given environment folder in remote repo.
     *
     * @param nsWithAppsFromSD    A map where key is namespace name and value as only applications populated based
     *                            on solution sbom.                           .
     * @param profilesMap         A map where profile name is key and profile dto as value read from Profiles folder.
     * @param namespaceMap        A map where namespace name is key and value as namespace dto read from Namespaces folder.
     *                            Populates only the namespace that are part of solution sbom.
     * @param cloudApps           List of applications from Applications folder that are part of solution sbom.
     * @param appsToProcess       List of application names that are part of solution sbom.
     * @param appsOnNamespace     List of applications that should be linked to namespace
     *                            from Namespaces/{ns}/Applications folder that are part of solution sbom.
     **/

    @Override
    public void prepareProcessingEnv() {
        try {
            Map<String, List<String>> nsWithAppsFromSD = new HashMap<>();
            Set<String> appsToProcess = new HashSet<>();
            loadSDData(nsWithAppsFromSD, appsToProcess);
            loadRegistryData();
            loadConsumerData();
            traverseSourceDirectory(nsWithAppsFromSD, appsToProcess);
            populateEnvironments();
            correctDeployPostfix();
            fileSystemUtils.createEffectiveSetFolder(inputData.getSolutionBomDTO());
        } catch (Exception e) {
            throw new FileParseException("Error preparing data due to " + e.getMessage());
        }

    }

    private void correctDeployPostfix() {
        List<SBApplicationDTO> applicationDTOList = inputData.getSolutionBomDTO().map(SolutionBomDTO::getApplications)
                .orElseGet(Collections::emptyList);
        applicationDTOList.parallelStream().forEach(app -> {
            app.setNamespace(getNamespaceName(app.getNamespace()));
        });
    }

    private void loadConsumerData() {
        Map<String, ConsumerDTO> consumerDTOMap = new LinkedHashMap<>();
        if (CollectionUtils.isNotEmpty(sharedData.getPcsspPaths())) {
            sharedData.getPcsspPaths().forEach(path -> {
                try {
                    String name = FilenameUtils.getBaseName(path);
                    if (name.contains(".")) {
                        name = name.substring(0, name.indexOf("."));
                    }
                    ConsumerDTO consumerDTO = ConsumerDTO.builder().build();
                    List<Property> properties = new ArrayList<>();
                    String jsonContent = new String(Files.readAllBytes(Paths.get(path)));
                    JSONObject consumerObject = new JSONObject(jsonContent);
                    JSONArray requiredFieldArray = (JSONArray) consumerObject.get("required");
                    List<String> requiredFields = requiredFieldArray.toList().stream().map(Object::toString).collect(Collectors.toList());
                    JSONObject propertiesObject = (JSONObject) consumerObject.get("properties");
                    Map<String, Object> propertiesObjectMap = propertiesObject.toMap();
                    propertiesObjectMap.forEach((key, value) -> {
                        Property property = Property.builder().build();
                        property.setName(key);
                        property.setRequired(requiredFields.contains(key));
                        Map<String, String> map = (Map<String, String>) value;
                        property.setValue(map.get("default"));
                        property.setType(map.get("type"));
                        properties.add(property);
                    });
                    consumerDTO.setProperties(properties);
                    consumerDTOMap.put(name, consumerDTO);
                } catch (IOException e) {
                    throw new FileParseException(String.format(ExceptionMessage.FILE_READ_ERROR, path, e.getMessage()));
                }
            });
        }
        inputData.setConsumerDTOMap(consumerDTOMap);
    }

    private void populateEnvironments() {
        Path basePath = Paths.get(sharedData.getEnvsPath());
        Map<String, List<NamespacePrefixDTO>> clusterMap = new HashMap<>();
        Set<String> foldersToSkip = Set.of("parameters", "credentials", "resource_profiles", "cloud-passport", "app-deployer");
        try {
            Files.walkFileTree(basePath, new SimpleFileVisitor<>() {
                @Override
                public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) throws IOException {
                    if (dir.equals(basePath)) {
                        return FileVisitResult.CONTINUE;
                    }
                    if (foldersToSkip.contains(dir.getFileName().toString())) {
                        return FileVisitResult.SKIP_SUBTREE;
                    }
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                    if (file.toString().endsWith(GenericConstants.YAML_EXT) || file.toString().endsWith(GenericConstants.YML_EXT)) {
                        handleNamespaceYamlFile(file, clusterMap);
                    }
                    return FileVisitResult.CONTINUE;
                }

            });
            inputData.setClusterMap(prepareEnvMap(clusterMap));
        } catch (Exception e) {
            throw new FileParseException("Failure in reading input Directory", e);
        }

    }

    private Map<String, Object> prepareEnvMap(Map<String, List<NamespacePrefixDTO>> clusterMap) {
        if (MapUtils.isEmpty(clusterMap)) {
            return new HashMap<>();
        }
        Map<String, Object> finalMap = new TreeMap<>();
        clusterMap.entrySet().stream().forEach(
                entry -> {
                    Map<String, Object> namespacesMap = new TreeMap<>();
                    Map<String, Object> namespaceMap = new TreeMap<>();
                    List<NamespacePrefixDTO> namespacePrefixDTOS = entry.getValue();
                    namespacePrefixDTOS.stream().forEach(key -> {
                        Map<String, Object> deployPostFixMap = new TreeMap<>();
                        deployPostFixMap.put("deployPostfix", key.getDeployPostFix());
                        namespaceMap.put(key.getName(), deployPostFixMap);
                    });
                    namespacesMap.put("namespaces", namespaceMap);
                    finalMap.put(entry.getKey(), namespacesMap);
                }
        );
        return finalMap;
    }

    private void traverseSourceDirectory(Map<String, List<String>> nsWithAppsFromSD, Set<String> appsToProcess) {
        Map<String, ProfileFullDto> profilesMap = new HashMap<>();
        Map<String, NamespaceDTO> namespaceMap = new HashMap<>();
        List<ApplicationLinkDTO> cloudApps = new ArrayList<>();
        Map<String, List<ApplicationLinkDTO>> appsOnNamespace = new HashMap<>();
        Path basePath = Paths.get(sourceDir);
        Set<String> foldersToVisit = Set.of(NS_FOLDER, APPS_FOLDER, CREDS_FOLDER, PROFILES_FOLDER, basePath.getFileName().toString());
        if (inputData.getNamespaceDTOMap() == null || inputData.getNamespaceDTOMap().isEmpty()) {
            inputData.setNamespaceDTOMap(new HashMap<>());
        }
        try {
            Files.walkFileTree(basePath, new SimpleFileVisitor<>() {

                @Override
                public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                    if (dir.getParent().getFileName().toString().equals(GenericConstants.NS_FOLDER)) {
                        String namespace = dir.getFileName().toString();
                        String correctedNamespace = getCorrectedNamespace(dir.getFileName().toString());
                        if (!nsWithAppsFromSD.containsKey(correctedNamespace)) {
                            Path namespaceYaml = dir.resolve("namespace.yml");
                            if (Files.exists(namespaceYaml)) {
                                NamespaceDTO namespaceDTO = fileDataConverter.parseInputFile(NamespaceDTO.class, namespaceYaml.toFile());
                                inputData.getNamespaceDTOMap().put(namespace, namespaceDTO);
                            }
                            return FileVisitResult.SKIP_SUBTREE;
                        }
                    }

                    if (!dir.getParent().getFileName().toString().equals(GenericConstants.NS_FOLDER)
                            && !foldersToVisit.contains(dir.getFileName().toString())) {
                        return FileVisitResult.SKIP_SUBTREE;
                    }

                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                    if (file.toString().endsWith(GenericConstants.YAML_EXT) || file.toString().endsWith(GenericConstants.YML_EXT)) {
                        handleYamlFile(file, profilesMap, namespaceMap, appsOnNamespace, nsWithAppsFromSD, cloudApps, appsToProcess);
                    }
                    return FileVisitResult.CONTINUE;
                }

                @Override
                public FileVisitResult postVisitDirectory(Path dir, IOException exc) {
                    String currentFolder = dir.getFileName().toString();
                    if (currentFolder.equals(GenericConstants.PROFILES_FOLDER)) {
                        inputData.setProfileFullDtoMap(profilesMap);

                    } else if (currentFolder.equals(GenericConstants.NS_FOLDER)) {
                        namespaceMap.replaceAll((name, namespaceDTO) -> {
                            List<ApplicationLinkDTO> applications = appsOnNamespace.get(name);
                            return namespaceDTO.toBuilder().applications(applications == null ? Collections.emptyList() : applications).build();
                        });
                        inputData.getNamespaceDTOMap().putAll(namespaceMap);
                    }
                    return FileVisitResult.CONTINUE;
                }
            });
        } catch (Exception e) {
            throw new FileParseException("Failure in reading input Directory", e);
        }
        inputData.setCloudDTO(inputData.getCloudDTO().toBuilder().applications(cloudApps).build());
    }

    private String getCorrectedNamespace(String namespace) {
        if (namespace.endsWith("-origin")) {
            return namespace.substring(0, namespace.indexOf("-origin"));
        } else if (namespace.endsWith("-peer")) {
            return namespace.substring(0, namespace.indexOf("-peer"));
        }
        return namespace;
    }

    private void handleNamespaceYamlFile(Path file, Map<String, List<NamespacePrefixDTO>> clusterMap) {
        Path parent = file.getParent();
        String name = file.getFileName().toString().split("\\.")[0];
        if ("namespace".equalsIgnoreCase(name)) {
            NamespaceDTO namespaceDTO = fileDataConverter.parseInputFile(NamespaceDTO.class, file.toFile());
            Path environment = parent.getParent().getParent();
            Path cluster = parent.getParent().getParent().getParent();
            NamespacePrefixDTO namespacePrefixDTO = NamespacePrefixDTO.builder().build();
            List<NamespacePrefixDTO> namespacePrefixDTOS = clusterMap.get(cluster.getFileName().toString() + "/" + environment.getFileName().toString());
            if (CollectionUtils.isEmpty(namespacePrefixDTOS)) {
                namespacePrefixDTOS = new ArrayList<>();
            }
            namespacePrefixDTO.setName(namespaceDTO.getName());
            namespacePrefixDTO.setDeployPostFix(parent.getFileName().toString());
            namespacePrefixDTOS.add(namespacePrefixDTO);
            clusterMap.put(cluster.getFileName().toString() + "/" + environment.getFileName().toString(), namespacePrefixDTOS);
        }
    }

    private void handleYamlFile(Path file, Map<String, ProfileFullDto> profilesMap, Map<String, NamespaceDTO> namespaceMap,
                                Map<String, List<ApplicationLinkDTO>> appsOnNamespace, Map<String, List<String>> nsWithAppsFromSD,
                                List<ApplicationLinkDTO> cloudApps, Set<String> appsToProcess) {
        Path parent = file.getParent();
        String name = file.getFileName().toString().split("\\.")[0];

        switch (name) {
            case "tenant":
                TenantDTO tenantDTO = fileDataConverter.parseInputFile(TenantDTO.class, file.toFile());
                inputData.setTenantDTO(tenantDTO);
                break;
            case "cloud":
                CloudDTO cloudDTO = fileDataConverter.parseInputFile(CloudDTO.class, file.toFile());
                inputData.setCloudDTO(cloudDTO);
                break;
            case "namespace":
                String namespace = parent.getFileName().toString();
                NamespaceDTO namespaceDTO = fileDataConverter.parseInputFile(NamespaceDTO.class, file.toFile());
                namespaceMap.putIfAbsent(namespace, namespaceDTO);
                break;
            case "credentials":
                TypeReference<Map<String, CredentialDTO>> typeReference = new TypeReference<>() {
                };
                Map<String, CredentialDTO> credentialDTOMap = fileDataConverter.parseInputFile(typeReference, file.toFile());
                if (credentialDTOMap != null) {
                    credentialDTOMap.replaceAll((id, cred) ->
                            CredentialDTO.builder().credentialsId(id)
                                    .data(cred.getData()).description(cred.getDescription()).build());
                    inputData.setCredentialDTOMap(credentialDTOMap);
                }
                break;
            case "composite_structure":
                CompositeStructureDTO compositeStructureDTO = fileDataConverter.parseInputFile(CompositeStructureDTO.class, file.toFile());
                inputData.setCompositeStructureDTO(compositeStructureDTO);
                break;
            case "bg_domain":
                BgDomainEntityDTO bgDomainEntityDTO = fileDataConverter.parseInputFile(BgDomainEntityDTO.class, file.toFile());
                inputData.setBgDomainEntityDTO(bgDomainEntityDTO);
                break;
            default:
                processOtherFiles(file, parent, profilesMap, appsOnNamespace, nsWithAppsFromSD, cloudApps, appsToProcess);
                break;
        }
    }

    private void processOtherFiles(Path file, Path parent, Map<String, ProfileFullDto> profilesMap,
                                   Map<String, List<ApplicationLinkDTO>> appsOnNamespace, Map<String, List<String>> nsWithAppsFromSD
            , List<ApplicationLinkDTO> cloudApps, Set<String> appsToProcess) {

        String folderName = parent.getFileName().toString();
        if (folderName.equals(GenericConstants.PROFILES_FOLDER)) {
            ProfileFullDto profileFullDto = fileDataConverter.parseInputFile(ProfileFullDto.class, file.toFile());
            profileFullDto.setApplications(profileFullDto.getApplications().stream()
                    .filter(app -> appsToProcess.contains(app.getName())).collect(Collectors.toList()));
            profilesMap.putIfAbsent(profileFullDto.getName(), profileFullDto);

        } else if (folderName.equals(GenericConstants.APPS_FOLDER)) {
            processApplicationFiles(file, parent, appsOnNamespace, nsWithAppsFromSD, cloudApps, appsToProcess);
        }
    }

    private void processApplicationFiles(Path file, Path parent, Map<String, List<ApplicationLinkDTO>> appsOnNamespace,
                                         Map<String, List<String>> nsWithAppsFromSD, List<ApplicationLinkDTO> cloudApps,
                                         Set<String> appsToProcess) {

        ApplicationLinkDTO applicationLinkDTO = fileDataConverter.parseInputFile(ApplicationLinkDTO.class, file.toFile());
        if (parent.getParent().getParent().getFileName().toString().equals(GenericConstants.NS_FOLDER)) {
            String namespace = parent.getParent().getFileName().toString();
            String correctedNamespace = getCorrectedNamespace(namespace);
            String appName = file.getFileName().toString().replaceFirst("\\.(ya?ml)$", "");
            if (checkIfAppValid(correctedNamespace, appName, nsWithAppsFromSD)) {
                appsOnNamespace.computeIfAbsent(namespace, k -> new ArrayList<>()).add(applicationLinkDTO);
            }
        } else {
            if (appsToProcess.contains(applicationLinkDTO.getName())) cloudApps.add(applicationLinkDTO);
        }
    }

    private boolean checkIfAppValid(String namespace, String app, Map<String, List<String>> nsWithAppsFromSD) {
        List<String> sdApps = nsWithAppsFromSD.get(namespace);
        return sdApps != null && sdApps.contains(app);
    }

    private void loadSDData(Map<String, List<String>> nsWithAppsFromSD, Set<String> appsToProcess) {
        Optional<String> sdPath = sharedData.getSdPath();
        if (sdPath.isPresent()) {
            SolutionDescriptorDTO solDescDTO = fileDataConverter.parseInputFile(SolutionDescriptorDTO.class, new File(sdPath.get()));
            List<SBApplicationDTO> applications = solDescDTO.getApplications().stream()
                    .map(applicationDTO -> getSbApplicationDTO(nsWithAppsFromSD, appsToProcess, applicationDTO))
                    .collect(Collectors.toList());

            inputData.setSolutionBomDTO(Optional.ofNullable(SolutionBomDTO.builder().applications(applications).build()));
        }
    }

    private SBApplicationDTO getSbApplicationDTO(Map<String, List<String>> nsWithAppsFromSD, Set<String> appsToProcess, SolutionDescriptorDTO.ApplicationDTO applicationDTO) {
        String namespace = applicationDTO.getDeployPostfix();
        String appName = applicationDTO.getVersion().split(":")[0];
        String appVersion = applicationDTO.getVersion().replace(":", "-");
        String appFileRef = String.format("%s/%s", sharedData.getSbomsPath().get(), appVersion + ".sbom.json");
        SBApplicationDTO dto = SBApplicationDTO.builder()
                .appName(appName)
                .appVersion(appVersion)
                .namespace(namespace)
                .appFileRef(appFileRef)
                .build();
        appsToProcess.add(appName);
        nsWithAppsFromSD.computeIfAbsent(namespace, k -> new ArrayList<>()).add(appName);
        return dto;
    }

    private String getNamespaceName(String deployPostFix) {
        if (inputData.getBgDomainEntityDTO() != null) {
            NamespaceDTO namespaceDTO =
                    inputData.getNamespaceDTOMap().getOrDefault(deployPostFix,
                            inputData.getNamespaceDTOMap().getOrDefault(deployPostFix + "-origin",
                                    inputData.getNamespaceDTOMap().get(deployPostFix + "-peer")));
            if (namespaceDTO != null) {
                String originalNamespace = namespaceDTO.getName();
                BgDomainEntityDTO.NamespaceDTO originNamespaceDTO = inputData.getBgDomainEntityDTO().getOriginNamespace();
                BgDomainEntityDTO.NamespaceDTO peerNamespaceDTO = inputData.getBgDomainEntityDTO().getPeerNamespace();
                if (originalNamespace.equalsIgnoreCase(originNamespaceDTO.getName())) {
                    return deployPostFix + "-origin";
                } else if (originalNamespace.equalsIgnoreCase(peerNamespaceDTO.getName())) {
                    return deployPostFix + "-peer";
                }
            }
        }
        return deployPostFix;
    }

    private void loadRegistryData() {
        Optional<String> registryPath = sharedData.getRegistryPath();
        if (registryPath.isPresent()) {
            Map<String, RegistryDTO> registries = fileDataConverter.parseInputFile(new TypeReference<HashMap<String, RegistryDTO>>() {
            }, new File(registryPath.get()));
            Map<String, RegistryDTO> registryMap = new HashMap<>();

            for (Map.Entry<String, RegistryDTO> entry : registries.entrySet()) {
                String cleanKey = entry.getKey().replace("%20", " ");
                registryMap.put(cleanKey, entry.getValue());
            }
            inputData.setRegistryDTOMap(registryMap);
        }
    }

}

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

package org.qubership.cloud.devops.cli;

import io.opentelemetry.api.trace.NoopTracer;
import io.opentelemetry.api.trace.Tracer;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.BeforeAll;
import org.modelmapper.ModelMapper;
import org.qubership.cloud.devops.cli.parser.CliParameterParser;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataConverterImpl;
import org.qubership.cloud.devops.cli.repository.implementation.FileDataRepositoryImpl;
import org.qubership.cloud.devops.cli.service.implementation.*;
import org.qubership.cloud.devops.cli.utils.*;
import org.qubership.cloud.devops.cli.utils.di.CliDI;
import org.qubership.cloud.devops.commons.Injector;
import org.qubership.cloud.devops.commons.exceptions.CreateWorkDirException;
import org.qubership.cloud.devops.commons.repository.interfaces.FileDataConverter;
import org.qubership.cloud.devops.commons.service.interfaces.*;
import org.qubership.cloud.devops.commons.utils.BomReaderUtils;
import org.qubership.cloud.devops.commons.utils.CredentialUtils;
import org.qubership.cloud.devops.commons.utils.mapper.ProfileMapper;
import org.qubership.cloud.devops.commons.utils.otel.OpenTelemetryProvider;
import org.qubership.cloud.parameters.processor.ParametersProcessor;
import org.qubership.cloud.parameters.processor.service.ParametersCalculationServiceV1;
import org.qubership.cloud.parameters.processor.service.ParametersCalculationServiceV2;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.qubership.cloud.devops.cli.TestConstants.*;

@Slf4j
public class BaseInit {

    public static  CliParameterParser cliParameterParser;

    static Path pathDir;

    @BeforeAll
    public static void init() throws CreateWorkDirException, IOException {
        pathDir =  Files.createTempDirectory("effective-set");
        log.info("Temperory File location "+ pathDir.toFile().getAbsolutePath());
        SharedData sharedData = new SharedData();
        setSharedData(sharedData, pathDir);
        InputData inputData = new InputData();
        FileSystemUtils fileSystemUtils = new FileSystemUtils(sharedData);
        FileDataConverter fileDataConverter = new FileDataConverterImpl(fileSystemUtils);
        OpenTelemetryProvider openTelemetryProvider = new OpenTelemetryProvider() {
            @Override
            public Tracer getTracer() {
                return new NoopTracer();
            }

            @Override
            public <T, E extends Exception> T withSpan(String spanName, ThrowingSupplier<T, E> delegate) throws E {
                return delegate.get();
            }
        };
        ParametersProcessor parametersProcessor = new ParametersProcessor(openTelemetryProvider);
        ParametersCalculationServiceV1 parametersCalculationServiceV1 = new ParametersCalculationServiceV1(parametersProcessor);
        ParametersCalculationServiceV2 parametersCalculationServiceV2 = new ParametersCalculationServiceV2(parametersProcessor);
        cliParameterParser = new CliParameterParser(parametersCalculationServiceV1, parametersCalculationServiceV2, inputData, fileDataConverter, sharedData, fileSystemUtils);
        ApplicationService applicationService = new ApplicationServiceCliImpl(inputData);
        TenantConfigurationService tenantConfigurationService = new TenantConfigurationServiceCliImpl(inputData);
        ProfileMapper mapper = new ProfileMapper(new ModelMapper(), applicationService);
        ProfileService profileService = new ProfileServiceCliImpl(inputData,mapper, tenantConfigurationService);
        CloudConfigurationService cloudConfigurationService = new CloudConfigurationServiceCliImpl(inputData, profileService);
        RegistryConfigurationService registryConfigurationService =
                new RegistryConfigurationServiceImpl(inputData);
        BomCommonUtils bomCommonUtils = new BomCommonUtils(fileDataConverter, registryConfigurationService, profileService);
        BomReaderUtilsImplV1 bomReaderUtilsImplV1 = new BomReaderUtilsImplV1(fileDataConverter, registryConfigurationService, bomCommonUtils);
        BomReaderUtilsImplV2 bomReaderUtilsImplV2 = new BomReaderUtilsImplV2(fileDataConverter, profileService, registryConfigurationService, sharedData, bomCommonUtils);
        BomReaderUtils bomReaderUtils = new BomReaderUtilsImpl(bomReaderUtilsImplV2, bomReaderUtilsImplV1, sharedData);
        FileDataRepositoryImpl fileDataRepository = new FileDataRepositoryImpl(fileDataConverter, sharedData
        , inputData, bomReaderUtils, fileSystemUtils);
        NamespaceConfigurationService namespaceConfigurationService = new NamespaceConfigurationServiceCliImpl(inputData, profileService);
        CredentialUtils credentialUtils = new CredentialUtilsCliImpl(inputData);

        CliDI cdi = new CliDI();
        Injector provider = new Injector(cdi);
        provider.setRegistryConfigurationService(registryConfigurationService);
        provider.setCloudConfigurationService(cloudConfigurationService);
        provider.setTenantConfigurationService(tenantConfigurationService);
        provider.setNamespaceConfigurationService(namespaceConfigurationService);
        provider.getDi().add(credentialUtils);
        provider.getDi().add(applicationService);
        provider.getDi().add(bomReaderUtils);

        fileDataRepository.prepareProcessingEnv();
    }

    private static void setSharedData(SharedData sharedData, Path customDir) {
        sharedData.setEnvId(ENV_ID);
        sharedData.setEnvsPath(ENV_FOLDER);
        sharedData.setSbomsPath(SBOM_PATH);
        sharedData.setSolsbomPath(SOL_SBOM);
        sharedData.setRegistryPath(REG_PATH);
        sharedData.setEffectiveSetVersion(EFFECTIVE_SET_VERSION);
        sharedData.setOutputDir(customDir.toFile().getAbsolutePath());
    }
}

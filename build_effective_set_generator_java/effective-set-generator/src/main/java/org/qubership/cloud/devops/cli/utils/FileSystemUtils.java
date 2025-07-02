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
import jakarta.inject.Inject;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.io.FileUtils;
import org.qubership.cloud.devops.cli.exceptions.DirectoryCreateException;
import org.qubership.cloud.devops.cli.pojo.dto.sd.SBApplicationDTO;
import org.qubership.cloud.devops.cli.pojo.dto.shared.SharedData;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

@ApplicationScoped
@Slf4j
public class FileSystemUtils {
    @Getter
    private final String envsPath;
    private final SharedData data;

    @Inject
    public FileSystemUtils(SharedData data) {
        this.envsPath = String.format("%s/%s", data.getEnvsPath(), data.getEnvId());
        this.data = data;
    }

    public File getFileFromGivenPath(String... args) {
        return new File(String.join("/", args));
    }

    public void createEffectiveSetFolder(List<SBApplicationDTO> applicationDTOList) throws IOException {
        if ("v2.0".equalsIgnoreCase(data.getEffectiveSetVersion())) {
            createEffectiveSetTwo(applicationDTOList);
        } else {
            createEffectiveSetOne(applicationDTOList);
        }
    }

    private void createEffectiveSetTwo(List<SBApplicationDTO> applicationDTOList) throws IOException {
        File file = getFileFromGivenPath(data.getOutputDir());
        if (file.exists()) {
            FileUtils.forceDelete(file);
        }
        file.mkdir();
        Path pipelinePath = getFileFromGivenPath(data.getOutputDir(), "pipeline").toPath();
        Files.createDirectories(pipelinePath);
        applicationDTOList
                .forEach(app->{
                    try {
                        Path deploymentPath = getFileFromGivenPath(data.getOutputDir(), "deployment", app.getNamespace(), app.getAppName(), "values").toPath();
                        Files.createDirectories(deploymentPath);
                        Path runtimePath = getFileFromGivenPath(data.getOutputDir(), "runtime", app.getNamespace(), app.getAppName()).toPath();
                        Files.createDirectories(runtimePath);
                    } catch (IOException e) {
                        throw new DirectoryCreateException("Error creating directory for application "+app.getAppName()+" due to "+e.getMessage());
                    }

                });
    }

    private void createEffectiveSetOne(List<SBApplicationDTO> applicationDTOList) throws IOException {
        File file = getFileFromGivenPath(data.getOutputDir());
        if (file.exists()) {
            FileUtils.forceDelete(file);
        }
        file.mkdir();

        applicationDTOList
                .forEach(app->{
                    Path appPath = getFileFromGivenPath(data.getOutputDir(), app.getNamespace(), app.getAppName()).toPath();
                    try {
                        Files.createDirectories(appPath);
                    } catch (IOException e) {
                        throw new DirectoryCreateException("Error creating directory for application "+app.getAppName()+" due to "+e.getMessage());
                    }

                });
    }


}

package org.qubership.cloud.devops.commons.pojo.bom;


import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class ConfigDTO {
    private String name;
    private String mimeType;
    private String gav;
    private String artifactName;
    private String groupId;
    private String version;
}

package org.qubership.cloud.parameters.processor.dto;

import lombok.Builder;
import lombok.Data;
import org.qubership.cloud.devops.commons.utils.Parameter;

import java.util.Map;

@Data
@Builder
public class Params {
    Map<String, Parameter> deployParams;
    Map<String, Parameter> techParams;
    Map<String, Parameter> e2eParams;
}

package org.qubership.cloud.devops.cli.utils.extcreds;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.qubership.cloud.devops.cli.pojo.dto.input.InputData;
import org.qubership.cloud.devops.commons.pojo.credentials.dto.CredentialDTO;

import java.util.LinkedHashMap;
import java.util.Map;

@ApplicationScoped
public class ExternalCredUtils {

    private final InputData inputData;

    @Inject
    public ExternalCredUtils(InputData inputData) {
        this.inputData = inputData;
    }

    private static final String HELM_VALUES = "helm-values";

    private static final String EXT_VALUES = "external-values";

    private static final String VALS = "vals";

    private static final String ESO = "eso";

    public void processExternalCreds(Map<String, Object> paramsWithExtCreds, String secretFlow, boolean esoSupport) {
        String refShape = resolveReferenceShape(secretFlow, esoSupport);
        Map<String, Object> finalResolvedParams = new LinkedHashMap<>();
        if (VALS.equals(refShape)) {
            createValsData(paramsWithExtCreds, inputData.getCredentialDTOMap(), finalResolvedParams);
        } else if (ESO.equals(refShape)) {
            createEsoData(paramsWithExtCreds, inputData.getCredentialDTOMap(), finalResolvedParams);
        }


    }

    public String resolveReferenceShape(String secretFlow, Boolean esoSupport) {

        String flow = (secretFlow == null || secretFlow.isBlank()) ? HELM_VALUES : secretFlow;
        boolean eso = Boolean.TRUE.equals(esoSupport);

        switch (flow) {
            case HELM_VALUES:
                return VALS;

            case EXT_VALUES:
                if (eso) {
                    return ESO;
                }
                throw new IllegalStateException("Secret Flow is \"external-values\" with ESO disabled which is not supported. Failing Effective set generation");

            default:
                return VALS;
        }
    }

    private void createValsData(Map<String, Object> paramsWithExtCreds, Map<String, CredentialDTO> credentials, Map<String, Object> finalResolvedParams) {

    }

    private void createEsoData(Map<String, Object> paramsWithExtCreds, Map<String, CredentialDTO> credentials, Map<String, Object> finalResolvedParams) {

    }
}


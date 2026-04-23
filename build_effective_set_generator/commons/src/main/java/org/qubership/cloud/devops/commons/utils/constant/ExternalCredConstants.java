package org.qubership.cloud.devops.commons.utils.constant;

import java.util.regex.Pattern;

public class ExternalCredConstants {

    public static final String HELM_VALUES = "helm-values";

    public static final String EXT_VALUES = "external-values";

    public static final String VALS = "vals";

    public static final String ESO = "eso";

    public static final String SECRET_FLOW = "SECRET_FLOW";
    public static final String ESO_SUPPORT = "ESO_SUPPORT";
    public static final String SECRET_NAME = "Final Normalized Secret Name";
    public static final String CREDID = "Credential ID";
    public static final Pattern VAULT_PATTERN = Pattern.compile("^[a-zA-Z0-9/_-]+$");
    public static final Pattern AZURE_PATTERN = Pattern.compile("^[a-zA-Z0-9-]+$");
    public static final Pattern AWS_PATTERN = Pattern.compile("^[a-zA-Z0-9\\-/_+=.@!]+$");
    public static final Pattern GCP_PATTERN = Pattern.compile("^[a-zA-Z0-9_-]+$");
    public static final int MAX_CRED_ID_LENGTH = 32;
    public static final int AZURE_MAX_LENGTH = 127;
    public static final int AWS_MAX_LENGTH = 512;
    public static final int GCP_MAX_LENGTH = 255;
    public static final int AZURE_SEGMENT_MAX = 20;
    public static final int AWS_SEGMENT_MAX = 119;
    public static final int GCP_SEGMENT_MAX = 53;
}

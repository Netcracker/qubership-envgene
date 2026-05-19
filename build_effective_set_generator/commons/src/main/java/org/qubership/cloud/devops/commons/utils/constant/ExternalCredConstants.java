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

package org.qubership.cloud.devops.commons.utils.constant;

import java.util.regex.Pattern;

public class ExternalCredConstants {

    public static final String HELM_VALUES = "helm-values";

    public static final String EXT_VALUES = "external-values";

    public static final String VALS = "vals";

    public static final String ESO = "eso";

    public static final String SECRET_FLOW = "SECRET_FLOW";
    public static final String ESO_SUPPORT = "eso_support";
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

    public static final String REMOTE_KEY = "remoteKeyName";

    public static final String SECRET_STORE_ID = "secretStoreId";

    public static final String NORM_SECRET_NAME = "normalizedSecretName";

    public static final String SECRET_KEYS = "secretKeys";

    public static final String SECRET_STORES = "secretStores";

    public static final String CREDS = "credentials";

    public static final String PROPS = "properties";

    public static final String TYPE = "type";
    public static final String URL = "url";
    public static final String MOUNT_PATH = "mountPath";
    public static final String VAULT_NAME = "vaultName";
    public static final String REGION = "region";
    public static final String PROJECT_ID = "projectId";


}

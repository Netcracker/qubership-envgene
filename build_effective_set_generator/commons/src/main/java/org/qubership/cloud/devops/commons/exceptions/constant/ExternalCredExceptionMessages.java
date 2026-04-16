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

package org.qubership.cloud.devops.commons.exceptions.constant;

public class ExternalCredExceptionMessages {

    public static final String ESO_DISABLED_MESSAGE = "Secret Flow is \"external-values\" with ESO disabled which is not supported. Failing Effective set generation";

    public static final String EXT_CRED_NOT_FOUND = "Credential '%s' not found in External Credentials provided";

    public static final String SECRET_NOT_FOUND = "SecretStore '%s' not found in secret file for credential '%s'.";

    public static final String UNEXPECTED_FLOW = "Unexpected flow in prepareFinalValue. refShape=%s, credId=%s, property=%s";

    public static final String MULTI_PROPERTY_ERROR = "Credential in external template has properties but no property provided in cred '%s' referenced in parameter";

    public static final String SINGLE_PROPERTY_ERROR = "No properties defined for credential %s in external credential template.";

    public static final String INVALID_PROPERTY = "Invalid property '%s' referred in parameter for external credential id '%s'.";

    public static final String NORMALIZATION_INPUT_ERROR = "Inputs to build Normalized secret name is null. remoteRefPath = %s, credId = %s, secretStoreType = %s";

    public static final String UNSUPPORTED_SECRET_TYPE = "Unsupported secret store type: '%s' for credId [%s] and remoteRefPath [%s]. Supported are vault, aws, gcp, azure.";

    public static final String INVALID_CHARACTER = "Invalid characters in %s [%s] for type %s. %n Allowed pattern: %s. %n Please validate cred id and remoteRefPath.";

    public static final String INVALID_LENGTH = "Length exceeded for %s [%s] for type %s. Max allowed: %d, actual: %d";

    public static final String INVALID_CRED_FORMAT = "External creds found in local creds only environment";

    public static final String MIXED_CREDS = "Exiting as mixture of external and non-external credentials is not allowed";

    public static final String EXT_TEMPLATE_FOUND = "External Credentials not found in parameter but external template found";

}

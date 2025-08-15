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

package org.qubership.cloud.devops.cli.exceptions;

public class DirectoryCreateException extends RuntimeException {
    private static final long serialVersionUID = -3238514400757338416L;

    public DirectoryCreateException(String message) {
        super(message);
    }

    public DirectoryCreateException(String message, Throwable cause) {
        super(message, cause);
    }

    public DirectoryCreateException(Throwable cause) {
        super(cause);
    }

    public DirectoryCreateException() {
    }
}

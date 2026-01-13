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

package org.qubership.cloud.devops.commons.utils;

import lombok.extern.slf4j.Slf4j;
import java.util.Date;


@Slf4j
public class ConsoleLogger {
    private static final String BLUE = "\u001B[34;20m";
    private static final String WHITE = "\u001B[97;20m";
    private static final String YELLOW = "\u001B[33;20m";
    private static final String RED = "\u001B[31;20m";
    private static final String RESET = "\u001B[0m";

    public static void logError(String message) {
        log.error(formatMessage("ERROR", message, RED));
    }

    public static void logWarning(String message) {
        log.warn(formatMessage("WARNING", message, YELLOW));
    }

    public static void logInfo(String message) {
        log.info(formatMessage("INFO", message, WHITE));
    }

    public static void logDebug(String message) {
        log.debug(formatMessage("DEBUG", message, BLUE));
    }

    private static String formatMessage(String level, String message, String color) {
        StackTraceElement ste = Thread.currentThread().getStackTrace()[3];
        String timestamp = String.format("%tF %<tT,%<tL", new Date());
        return String.format("%s%s [%s] %s [%s:%d]%s",
                color,
                timestamp,
                level,
                message,
                ste.getFileName(),
                ste.getLineNumber(),
                RESET);
    }
}


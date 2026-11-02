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

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class HelmNameNormalizerTest {

    @Test
    void normalizesLowercaseNameAndReplacesUnderscores() {
        assertEquals("my-chart", HelmNameNormalizer.normalize("my_chart", 63));
    }

    @Test
    void encodesUppercaseCharacters() {
        assertEquals("mychart-g", HelmNameNormalizer.normalize("myChart", 63));
    }

    @Test
    void truncatesEncodedNameToFitProvidedLimit() {
        String result = HelmNameNormalizer.normalize("VeryLongChartName", 12);

        assertEquals(11, result.length());
        assertEquals("verylong-3s", result);
    }

    @Test
    void usesLimitPassedByCaller() {
        String name = "VeryLongChartName";

        String shortLimitResult = HelmNameNormalizer.normalize(name, 10);
        String largerLimitResult = HelmNameNormalizer.normalize(name, 16);

        assertEquals(8, shortLimitResult.length());
        assertEquals(14, largerLimitResult.length());
    }

    @Test
    void truncatesCookieAuthenticationDemoWithLimitOf29() {
        assertEquals("cookie-authentication--19atc",
                HelmNameNormalizer.normalize("Cookie-Authentication-Demo", 29));
    }

    @Test
    void preservesCookieAuthenticationDemoWithLimitOf219() {
        assertEquals("cookie-authentication-demo-k4t1k",
                HelmNameNormalizer.normalize("Cookie-Authentication-Demo", 219));
    }
}

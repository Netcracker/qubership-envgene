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

package org.qubership.cloud.devops.gstringtojinjavatranslator;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava.*;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.GStringToJinJavaTranslator;
import org.qubership.cloud.devops.gstringtojinjavatranslator.translator.error.TranslationException;

import com.hubspot.jinjava.Jinjava;
import com.hubspot.jinjava.JinjavaConfig;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;

class TranslationTests {
    private GStringToJinJavaTranslator translator;
    private Jinjava jinjava;
    private Map<String, Object> context;

    @BeforeEach
    void setUp() {
        translator = new GStringToJinJavaTranslator();
        setUpJinJava();
        setUpJinJavaContext();
    }

    private void setUpJinJava() {
        JinjavaConfig config = JinjavaConfig.newBuilder()
                .withTokenScannerSymbols(new LessThanTokenScannerSymbols())
                .withFailOnUnknownTokens(true)
                .build();
        jinjava = new CustomJinjava(config);
        jinjava.registerFilter(new EnvSuffixFilter());
        jinjava.registerFilter(new EnvPrefixFilter());
        jinjava.registerFunction(Functions.randomFunction());
    }

    private void setUpJinJavaContext() {
        context = new HashMap<>();
        context.put("key1", "value1");
        context.put("double", Map.of("double.key", "double value"));
        context.put("key2", "$key1");
        context.put("key3", "${key1[0..-2]}");
        context.put("BOOL_PARAM", "false");
        context.put("RandomMessageInJinjava", "randomMsg1");
        context.put("AnotherMessageInJinjava", "randomMsg2");
        context.put("COMPOSITE_GATEWAY_MEMORY_LIMIT", "128Mi");
        context.put("TEST_SERVICE_NAME_2", "first-second-third");
        context.put("BASE_DEPLOYER_TIMEOUT", "15");
        context.put("CUSTOM_HOST", "k8s-apps3.k8s.sdntest.example.com");
        context.put("CDC_KAFKA_SECURITY_PROTOCOL", "SASL_SSL");
        context.put("CLOUD_PUBLIC_HOST", "cloudbss-svt21.k8s.sdntest.example.com");
        context.put("CLOUDNAME", "AZUREAKS-test_apps");
        context.put("NAMESPACE", "st5-bss-st5");
        context.put("OM_WIRELESS_BILLING_ENDPOINT", "resource/merlinPOToBillingBridge/v1/productOrderToBilling");
        context.put("tenant", prepareTenantMapObject());
        context.put("record", Map.of("log", "first\tsecond"));
        context.put("creds", Map.of("userpass_cred", Map.of("username", "test1")));
    }

    private Map<String, Object> prepareTenantMapObject() {
        Map<String, Object> tenant = new HashMap<>();
        Map<String, Object> cloud = new HashMap<>();
        Map<String, Object> namespace = new HashMap<>();
        Map<String, Object> application = new HashMap<>();
        Map<String, Object> entity = new HashMap<>();
        entity.put("service_name", "entity-service-name");
        application.put("ocs-rejected-events-backend", entity);
        namespace.put("cicd-dev-1-apps", Map.of("application", application));
        cloud.put("app.db.url", "first@second@third");
        cloud.put("Single_site_ocs", Map.of("namespace", namespace));
        tenant.put("cloud", Map.of(
                "app.db.url", "first@second@third",
                "CLOUD_HELM_RESOURCE_TIMEOUT", "15"));
        tenant.put("CLOUD-OCS-PRODUCT", Map.of("cloud", cloud));
        return tenant;
    }

    private static Stream<Arguments> testTranslation() {
        return Stream.of(
                Arguments.of("", "", ""),
                Arguments.of(" ", " ", " "),
                Arguments.of("$key1", "<<key1>>", "value1"),
                Arguments.of("<<RandomMessageInJinjava>>","<<RandomMessageInJinjava>>", "randomMsg1"),
                Arguments.of(
                        "This is <<RandomMessageInJinjava>> and <<AnotherMessageInJinjava>>.",
                        "This is <<RandomMessageInJinjava>> and <<AnotherMessageInJinjava>>.",
                        "This is randomMsg1 and randomMsg2."),
                Arguments.of("This is simple text","This is simple text","This is simple text"),
                Arguments.of(
                        "${COMPOSITE_GATEWAY_MEMORY_LIMIT}",
                        "<<COMPOSITE_GATEWAY_MEMORY_LIMIT>>",
                        "128Mi"),
                Arguments.of(
                        "${TEST_SERVICE_NAME_2.tokenize('-')[-1]}",
                        "<<TEST_SERVICE_NAME_2.split('-')[-1]>>",
                        "third"),
                Arguments.of(
                        "${BASE_DEPLOYER_TIMEOUT ? BASE_DEPLOYER_TIMEOUT : 1}",
                        "<<BASE_DEPLOYER_TIMEOUT ? BASE_DEPLOYER_TIMEOUT : 1>>",
                        "15"),
                Arguments.of(
                        "${BOOL_PARAM ?: \"\"}",
                        "<<BOOL_PARAM ? BOOL_PARAM : \"\">>",
                        "false"
                ),
                Arguments.of(
                        "${tenant.cloud.get(\"app.db.url\").split(\"@\")[1]}",
                        "<<tenant.cloud[\"app.db.url\"].split(\"@\")[1]>>",
                        "second"),
                Arguments.of(
                        "${tenant.cloud.CLOUD_HELM_RESOURCE_TIMEOUT}",
                        "<<tenant.cloud.CLOUD_HELM_RESOURCE_TIMEOUT>>",
                        "15"),
                Arguments.of("${10}", "<<10>>", "10"),
                Arguments.of(
                        "${CLOUD_PUBLIC_HOST.replaceFirst(\"^.*\\\\.\", \"\")}",
                        "<<CLOUD_PUBLIC_HOST.replaceFirst(\"^.*\\\\.\",\"\")>>",
                        "com"),
                Arguments.of(
                        "${OM_WIRELESS_BILLING_ENDPOINT?: \"\"}",
                        "<<OM_WIRELESS_BILLING_ENDPOINT ? OM_WIRELESS_BILLING_ENDPOINT : \"\">>",
                        "resource/merlinPOToBillingBridge/v1/productOrderToBilling"),
                Arguments.of(
                        "${tenant['CLOUD-OCS-PRODUCT'].cloud['Single_site_ocs'].namespace['cicd-dev-1-apps'].application['ocs-rejected-events-backend'].service_name}",
                        "<<tenant['CLOUD-OCS-PRODUCT'].cloud['Single_site_ocs'].namespace['cicd-dev-1-apps'].application['ocs-rejected-events-backend'].service_name>>",
                        "entity-service-name"),
                Arguments.of("${ NAMESPACE }", "<<NAMESPACE>>", "st5-bss-st5"),
                Arguments.of(
                        "${record['log'].gsub(/\\t+/,' ')}",
                        "<<record['log'].replaceAll(\"\\t+\",' ')>>",
                        "first second"),
                Arguments.of(
                        "${record.\"log\"}",
                        "<<record.log>>",
                        "first\tsecond"),
                Arguments.of(
                        "${\"uim-edss-email-high.\" + NAMESPACE + \".svc.cluster.local\"}",
                        "<<\"uim-edss-email-high.\" + NAMESPACE + \".svc.cluster.local\">>",
                        "uim-edss-email-high.st5-bss-st5.svc.cluster.local"),
                Arguments.of(
                        "${ CDC_KAFKA_SECURITY_PROTOCOL.contains(\"SSL\") }",
                        "<<CDC_KAFKA_SECURITY_PROTOCOL.contains(\"SSL\")>>",
                        "true"),
                Arguments.of(
                        "${ CUSTOM_HOST.replaceFirst(/(\\\\..*)*$/, \"\").replace(\"-\",\"_\") }",
                        "<<CUSTOM_HOST.replaceFirst(\"(\\\\..*)*$\",\"\").replace(\"-\",\"_\")>>",
                        "k8s_apps3"),
                Arguments.of(
                        "${ creds[\"userpass_cred\"].username }",
                        "<<creds[\"userpass_cred\"].username>>",
                        "test1"),
                Arguments.of(
                        "${['bss'].findResult{ if (NAMESPACE.contains(it)) NAMESPACE.substring(0, NAMESPACE.indexOf(it)) } ?: ''}",
                        "<<['bss'] | envPrefix('')>>",
                        "st5-"),
                Arguments.of(
                        "${['oss','bss'].findResult{ if (NAMESPACE.contains(it)) NAMESPACE.substring(NAMESPACE.indexOf(it) + it.length()) } ?: ''}",
                        "<<['oss','bss'] | envSuffix('')>>",
                        "-st5"),
                Arguments.of(
                        "${CLOUDNAME.replace(\"_apps\",\"\").replace(\"_\", \"-\").toLowerCase()}",
                        "<<CLOUDNAME.replace(\"_apps\",\"\").replace(\"_\",\"-\").toLowerCase()>>",
                        "azureaks-test"),
                Arguments.of(
                        "${lower(RandomMessageInJinjava)}",
                        "<<RandomMessageInJinjava | lower>>",
                        "randommsg1"),
                Arguments.of(
                        "${ if (test1.contains(\"true\")) '1'}",
                        "<<test1.contains(\"true\") ? '1' : 'null'>>",
                        "null"
                ),
                Arguments.of("/$","/$","/$"),
                Arguments.of("$","$","$"),
                Arguments.of(
                        "---${key1}---{{key1}}---",
                        "---<<key1>>---{{key1}}---",
                        "---value1---{{key1}}---"),
                Arguments.of(
                        "---${key1}---{{name}}---",
                        "---<<key1>>---{{name}}---",
                        "---value1---{{name}}---"),
                Arguments.of(
                        "---${key1}---\\{{name\\}}---",
                        "---<<key1>>---\\{{name\\}}---",
                        "---value1---\\{{name\\}}---"),
                Arguments.of(
                        "---{{name}}---${key1}---",
                        "---{{name}}---<<key1>>---",
                        "---{{name}}---value1---")
        );
    }

    @ParameterizedTest
    @MethodSource
    void testTranslation(String input, String expectedTranslation, String expectedProcession) {
        String translated = translator.translate(input);
        assertEquals(expectedTranslation, translated);
        String out = jinjava.render(translated, context);
        assertEquals(expectedProcession, out);
    }

    @Test
    void mathRandomTest() {
        String translated = translator.translate("${Math.random()}");
        assertEquals("<<random()>>", translated);
        String out = jinjava.render(translated, context);
        assertTrue(isDouble(out));
    }

    @Test
    void ErrorLexerTest() {
        Exception exception = assertThrows(TranslationException.class, () ->
                translator.translate("${ hello::world }"));
        assertTrue(exception.getMessage().contains("No viable alternative"));
    }

    private boolean isDouble(String string)
    {
        try
        {
            Double.parseDouble(string);
        }
        catch (NumberFormatException e)
        {
            return false;
        }
        return true;
    }
}

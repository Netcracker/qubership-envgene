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

import groovy.lang.GString;
import groovy.lang.MissingPropertyException;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

import java.util.Map;


@Getter
@Setter
@Builder
public class Parameter extends GString {

    public static final Parameter NULL = new Parameter(null, null, true);
    @Builder.Default
    private Object value = null;
    @Builder.Default
    private String origin = null;
    @Builder.Default
    private boolean parsed = false;
    @Builder.Default
    private boolean valid = true;

    @Builder.Default
    private boolean processed = false;

    @Builder.Default
    private boolean secured = false;

    @Builder.Default
    private String translated = null;

    public Parameter(Object value, String origin, boolean parsed, boolean valid, boolean processed, boolean secured, String translated) {
        super(new Object[]{});
        this.value = value;
        this.origin = origin;
        this.parsed = parsed;
        this.valid = valid;
        this.processed = processed;
        this.secured = secured;
        this.translated = translated;
    }

    public Parameter(Object value) {
        super(new Object[]{});
        if (value instanceof Parameter) {
            this.value = ((Parameter) value).value;
            this.origin = ((Parameter) value).origin;
            this.parsed = ((Parameter) value).parsed;
            this.valid = ((Parameter) value).valid;
            this.processed = ((Parameter) value).processed;
            this.secured = ((Parameter) value).secured;
            this.translated = ((Parameter) value).translated;
        } else {
            this.value = value;
            this.origin = "";
            this.parsed = false;
            this.valid = true;
            this.processed = false;
            this.secured = false;
            this.translated = "";
        }
    }

    public Parameter(Object value, String translated) {
        super(new Object[]{});
        if (value instanceof Parameter) {
            this.value = ((Parameter) value).value;
            this.origin = ((Parameter) value).origin;
            this.parsed = ((Parameter) value).parsed;
            this.valid = ((Parameter) value).valid;
            this.processed = ((Parameter) value).processed;
            this.secured = ((Parameter) value).secured;
            this.translated = translated;
        } else {
            this.value = value;
            this.origin = "";
            this.parsed = false;
            this.valid = true;
            this.processed = false;
            this.secured = false;
            this.translated = translated;
        }
    }

    @Override
    public String[] getStrings() {
        if (value == null) return new String[]{""};
        if (secured) return new String[]{"\u0096" + value + "\u0097"};
        return new String[]{value.toString()};
    }

    @Override
    public String toString() {
        if (translated != null && !translated.isEmpty()) {
            if (secured) {
                return "\u0096" + translated + "\u0097";
            } else {
                return translated;
            }
        }

        if (value != null) {
            return super.toString();
        }
        return "";
    }

    public Parameter(Object value, String origin, boolean parsed) {
        this(value, origin, parsed, false, null);
    }

    public Parameter(Object value, String origin, boolean parsed, boolean secured, String translated) {
        super(new Object[]{});
        this.value = value;
        this.origin = origin;
        this.parsed = parsed;
        this.valid = true;
        this.processed = false;
        this.secured = secured;
        this.translated = translated;
    }

    public Parameter get(String key) {
        if (value instanceof Map) {
            return ((Map<String, Parameter>) value).get(key);
        }
        throw new MissingPropertyException(key, this.getClass());
    }

}
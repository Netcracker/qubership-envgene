package org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava;

import com.hubspot.jinjava.el.TruthyTypeConverter;
import com.hubspot.jinjava.objects.SafeString;
import com.hubspot.jinjava.util.HasObjectTruthValue;

import java.lang.reflect.Array;
import java.util.Collection;
import java.util.Map;

public class GroovyTruthyTypeConverter extends TruthyTypeConverter {
    @Override
    protected Boolean coerceToBoolean(Object object) {
        if (object == null) {
            return false;
        } else if (object instanceof HasObjectTruthValue) {
            return ((HasObjectTruthValue)object).getObjectTruthValue();
        } else if (object instanceof Boolean) {
            Boolean b = (Boolean)object;
            return b;
        } else if (object instanceof Number) {
            return ((Number)object).doubleValue() != (double)0.0F;
        } else if (object instanceof String) {
            return !"".equals(object);
        } else if (!(object instanceof SafeString)) {
            if (object.getClass().isArray()) {
                return Array.getLength(object) != 0;
            } else if (object instanceof Collection) {
                return ((Collection)object).size() != 0;
            } else if (object instanceof Map) {
                return ((Map)object).size() != 0;
            } else {
                return true;
            }
        } else {
            return !"".equals(object.toString());
        }
    }
}
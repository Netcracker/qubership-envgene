package org.qubership.cloud.devops.gstringtojinjavatranslator.jinjava;

import com.hubspot.jinjava.Jinjava;
import com.hubspot.jinjava.JinjavaConfig;
import com.hubspot.jinjava.el.ExtendedSyntaxBuilder;
import com.hubspot.jinjava.el.ext.eager.EagerExtendedSyntaxBuilder;
import jinjava.de.odysseus.el.ExpressionFactoryImpl;
import jinjava.de.odysseus.el.misc.TypeConverter;
import jinjava.de.odysseus.el.tree.TreeBuilder;
import jinjava.javax.el.ExpressionFactory;

import java.util.Properties;

public class CustomJinjava extends Jinjava {
    private final ExpressionFactory expressionFactory;
    private final ExpressionFactory eagerExpressionFactory;

    public CustomJinjava(JinjavaConfig globalConfig) {
        super(globalConfig);
        Properties expConfig = new Properties();

        expConfig.setProperty(
                TreeBuilder.class.getName(),
                ExtendedSyntaxBuilder.class.getName()
        );
        Properties eagerExpConfig = new Properties();

        eagerExpConfig.setProperty(
                TreeBuilder.class.getName(),
                EagerExtendedSyntaxBuilder.class.getName()
        );
        eagerExpConfig.setProperty(ExpressionFactoryImpl.PROP_CACHE_SIZE, "0");

        TypeConverter converter = new GroovyTruthyTypeConverter();
        this.expressionFactory = new ExpressionFactoryImpl(expConfig, converter);
        this.eagerExpressionFactory = new ExpressionFactoryImpl(eagerExpConfig, converter);
    }

    @Override
    public ExpressionFactory getExpressionFactory() {
        return expressionFactory;
    }

    @Override
    public ExpressionFactory getEagerExpressionFactory() {
        return eagerExpressionFactory;
    }
}

package org.qubership.cloud.devops.cli.logger;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.annotation.PostConstruct;
import org.jboss.logging.Logger.Level;

@ApplicationScoped
public class LoggingInitializer {

    @Inject
    LogLevelMapper logLevelMapper;

    @PostConstruct
    public void init() {
        Level logLevel = logLevelMapper.getMappedLevel()
        System.setProperty("quarkus.log.level", logLevel.name())
    }
}

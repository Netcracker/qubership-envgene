package org.qubership.cloud.devops.cli.parser;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;
import java.util.concurrent.ForkJoinPool;


public class MemoryMonitor {

    public static void logMemoryUsage() {

        MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
        MemoryUsage heapUsage = memoryBean.getHeapMemoryUsage();
        int parallelism = ForkJoinPool.commonPool().getParallelism();

        System.out.println(
                "Heap Info -> Init (-Xms): " + heapUsage.getInit() / 1024 / 1024 + " MB, " +
                        "Used: " + heapUsage.getUsed() / 1024 / 1024 + " MB, " +
                        "Max (-Xmx): " + heapUsage.getMax() / 1024 / 1024 + " MB, " +
                        "ParallelStream threads: " + parallelism
        );

    }
}

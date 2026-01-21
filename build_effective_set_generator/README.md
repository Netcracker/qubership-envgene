# *Parameter Calculator command-line tool*

The Calculator command-line tool tool will determine the effective parameter set based on the provided environment instance and
solution descriptor.

## **Features**

1. The command-line tool tool resolves the macros in parameters using either jinjava or groovy templates.
2. It merges the parameters from different layers to get the final list of effective parameters.
3. Parameter values from previous layer can be overridden with new value on current and next layers using same parameter name with different value.
4. It segregates the secured parameters.

## **Prerequisites:**

1. Java 17
2. Maven > 3.8.1

## **Build and run in Intellij:**

1. To build the project within Idea, you can run configuration with

    `mvn clean install`

2. To run the application, create quarkus maven run configuration with working directory as
    effective-set-generator and VM Options as below.

    `-Dquarkus.args="--env-id xxxxx --envs-path xxxx--local-sd-path xxxxx/sd.yml --output xxx/effective-set
    --cmdb-url=<url> --cmdb-username=<username> --cmdb-token=<API Token>"`

## **Running in a Docker Container**

The simplest way to get the effective-set-generator Docker image is to pull from GitHub Container Registry:

    `docker pull xxx`

Alternately, you can build it from source yourself:

First run mvn clean install and run below command

    `docker build -t effective-set-generator:latest -f Dockerfile.jvm .`

Finally, to run it, mount the directory you want to scan to /configs and pass the appropriate inputs:

    `docker run  -v ${Directory}:/configs/ effective-set-generator:latest
    --env-id xxxxx --envs-path xxxx--local-sd-path xxxxx /sd.yml --output /configs/effective-set
    --cmdb-url=<url> --cmdb-username=<username> --cmdb-token=<API Token>
    `
Usages:

    `--env-id/-e            environment ID in <cluster-name>/<environment-name> notation.

    --envs-path/-ep         path to '/environments' folder

    --local-sd-path/-lsdp   path to Full SD file.

    --output/-o             Destination folder to write final effective set parameter files.`

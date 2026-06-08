import os
import re
import sys


def merge_java_opts(base, override):
    result = base
    allowed_override = []

    for opt in override.split():

        if opt.startswith("-Xms"):
            result = re.sub(r"-Xms[^ ]+", "", result)
            allowed_override.insert(0, opt)

        elif opt.startswith("-Xmx"):
            result = re.sub(r"-Xmx[^ ]+", "", result)
            allowed_override.insert(0, opt)

        elif opt.startswith("-Djava.util.concurrent.ForkJoinPool.common.parallelism="):
            result = re.sub(
                r"-Djava\.util\.concurrent\.ForkJoinPool\.common\.parallelism=[^ ]+",
                "",
                result,
            )
            allowed_override.insert(0, opt)

    return result + (" " + " ".join(allowed_override) if allowed_override else "")


def main():
    java_options = os.getenv("JAVA_OPTIONS", "")
    calculator_cli_java_options = os.getenv(
        "CALCULATOR_CLI_JAVA_OPTIONS",
        "",
    )

    if calculator_cli_java_options:
        java_options = merge_java_opts(
            java_options,
            calculator_cli_java_options,
        )

        java_options = " ".join(java_options.split())

    os.environ["JAVA_OPTIONS"] = java_options

    print(f"DEBUG: JAVA_OPTIONS={java_options}")

    os.execvp(
        "/deployments/run-java.sh",
        ["/deployments/run-java.sh"] + sys.argv[1:],
    )


if __name__ == "__main__":
    main()

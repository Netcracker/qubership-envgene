import os

os.environ.setdefault("ENVIRONMENT_NAME", "test-env")
os.environ.setdefault("CLUSTER_NAME", "test-cluster")
os.environ.setdefault("CI_PROJECT_DIR", os.path.dirname(__file__))

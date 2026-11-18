from build_env.render_config_env import EnvGenerator


def render_cluster(inventory, cloud_passport):
    gen = EnvGenerator()
    gen.ctx.env_definition = {"inventory": inventory, "envTemplate": {"name": "t"}}
    gen.ctx.cloud_passport = cloud_passport
    gen.generate_config()
    return gen.ctx.config["environment"]["cluster"]


FULL_PASSPORT = {
    "cloud": {
        "CLOUD_PROTOCOL": "https",
        "CLOUD_API_HOST": "api.passport-host.cloud",
        "CLOUD_API_PORT": "7443",
        "CLOUD_PUBLIC_HOST": "passport-host.cloud",
    }
}

OTHER_PASSPORT = {
    "cloud": {
        "CLOUD_PROTOCOL": "http",
        "CLOUD_API_HOST": "api.passport.com",
        "CLOUD_API_PORT": "8443",
        "CLOUD_PUBLIC_HOST": "passport.com",
    }
}

FROM_CLUSTER_URL = {
    "cloud_api_protocol": "HTTPS",
    "cloud_api_url": "api.example.com",
    "cloud_api_port": "6443",
    "cloud_public_url": "example.com",
}

FROM_PASSPORT = {
    "cloud_api_protocol": "HTTPS",
    "cloud_api_url": "api.passport-host.cloud",
    "cloud_api_port": "7443",
    "cloud_public_url": "passport-host.cloud",
}

EMPTY = {
    "cloud_api_protocol": "",
    "cloud_api_url": "",
    "cloud_api_port": "",
    "cloud_public_url": "",
}


def test_clusterurl_set_no_passport():
    cluster = render_cluster(
        {"environmentName": "e", "clusterUrl": "https://api.example.com:6443"}, {}
    )
    assert cluster == FROM_CLUSTER_URL


def test_clusterurl_set_with_passport():
    cluster = render_cluster(
        {"environmentName": "e", "clusterUrl": "https://api.example.com:6443"}, OTHER_PASSPORT
    )
    assert cluster == FROM_CLUSTER_URL


def test_clusterurl_absent_full_passport():
    cluster = render_cluster({"environmentName": "e"}, FULL_PASSPORT)
    assert cluster == FROM_PASSPORT


def test_clusterurl_absent_no_passport():
    cluster = render_cluster({"environmentName": "e"}, {})
    assert cluster == EMPTY


def test_clusterurl_absent_passport_missing_port():
    passport = {"cloud": {k: v for k, v in FULL_PASSPORT["cloud"].items() if k != "CLOUD_API_PORT"}}
    cluster = render_cluster({"environmentName": "e"}, passport)
    assert cluster["cloud_api_port"] == ""
    assert cluster["cloud_public_url"] == "passport-host.cloud"

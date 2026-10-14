from build_env.jinja.jinja import create_jinja_env, jinja_template


def test_same_source_compiles_once():
    assert jinja_template("{{ name }}") is jinja_template("{{ name }}")


def test_cached_template_renders_each_context():
    template = jinja_template("{{ name | default('none') }}")

    assert template.render(name="a") == "a"
    assert template.render(name="b") == "b"
    assert template.render() == "none"


def test_env_is_shared_and_keeps_filters():
    assert create_jinja_env() is create_jinja_env()
    assert jinja_template("{{ url | urlsplit('hostname') }}").render(url="https://host:8080/p") == "host"

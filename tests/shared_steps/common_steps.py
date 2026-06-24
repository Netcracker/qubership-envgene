from pytest_bdd import given, then, when, parsers


@then(parsers.parse('the pipeline log shows "{message}"'))
def pipeline_log_shows(workspace, message):
    """
    Generic step to verify that the subprocess stdout/stderr contains a specific message.
    Automatically handles cross-platform slashes and placeholder replacements.
    """
    expected = message.replace("<path>", str(workspace.base_dir)).replace('\\', '/')
    output = workspace.stdout.replace('\\', '/') + "\n" + workspace.stderr.replace('\\', '/')

    if "<application-name>" in expected:
        prefix = expected.split("<application-name>")[0]
        found = any(line.endswith(prefix) or prefix in line for line in output.splitlines())
    else:
        found = expected in output

    if not found:
        clean_msg = message.replace("<path>", "").replace('\\', '/')
        if "<application-name>" in clean_msg:
            prefix = clean_msg.split("<application-name>")[0]
            found = any(prefix in line for line in output.splitlines())
        else:
            found = clean_msg in output

    assert found, f"Expected message not found in logs: {message}\nOutput: {output}"

@given(parsers.parse('the pipeline has {param} set to "{value}"'))
def set_pipeline_param(workspace, param, value):
    if not hasattr(workspace, 'extra_env'):
        workspace.extra_env = {}
    workspace.extra_env[param] = value

@then('the effective set is generated successfully')
def effective_set_generated(workspace):
    assert workspace.returncode == 0, f"Pipeline failed to generate effective set. STDOUT: {workspace.stdout}\nSTDERR: {workspace.stderr}"

@then('the pipeline fails')
def pipeline_fails(workspace):
    assert workspace.returncode != 0, "Pipeline should have failed but returned 0"

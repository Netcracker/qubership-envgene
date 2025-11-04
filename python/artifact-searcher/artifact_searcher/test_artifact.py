import aiohttp
from aiohttp import web
from artifact_searcher.utils import models
from artifact_searcher.artifact import resolve_snapshot_version

async def test_resolve_snapshot_version(aiohttp_server):
    async def handler(request):
        return web.Response(
            text="""
            <metadata>
              <versioning>
                <snapshotVersions>
                  <snapshotVersion>
                    <classifier></classifier>
                    <extension>pom</extension>
                    <value>1.0.0-20240702.123456-3</value>
                  </snapshotVersion>
                  <snapshotVersion>
                    <classifier>graph</classifier>
                    <extension>json</extension>
                    <value>1.0.0-20240702.123456-2</value>
                  </snapshotVersion>
                  <snapshotVersion>
                    <classifier></classifier>
                    <extension>json</extension>
                    <value>1.0.0-20240702.123456-1</value>
                  </snapshotVersion>
                </snapshotVersions>
              </versioning>
            </metadata>
            """,
            content_type="application/xml"
        )
    app_web = web.Application()
    app_web.router.add_get('/repo/com/example/app/1.0.0-SNAPSHOT/maven-metadata.xml', handler)
    server = await aiohttp_server(app_web)

    mvn_cfg = models.MavenConfig(
        target_snapshot="repo",
        target_staging="repo",
        target_release="repo",
        repository_domain_name=str(server.make_url('/')),
    )
    dcr_cfg = models.DockerConfig()
    reg = models.Registry(
        name="registry",
        maven_config=mvn_cfg,
        docker_config=dcr_cfg,
    )
    app = models.Application(
        name="app",
        artifact_id="app",
        group_id="com.example",
        registry=reg,
        solution_descriptor=False,
    )

    async with aiohttp.ClientSession() as session:
        resolved = await resolve_snapshot_version(session, app, "1.0.0-SNAPSHOT", "repo")
        assert resolved == "1.0.0-20240702.123456-1"

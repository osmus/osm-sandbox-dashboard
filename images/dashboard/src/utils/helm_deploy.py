from pyhelm3 import Client
import asyncio
client = Client()
async def list_releases():
    releases = await client.list_releases(all=True, all_namespaces=True)
    for release in releases:
        revision = await release.current_revision()
        print(release.name, release.namespace, revision.revision, str(revision.status))
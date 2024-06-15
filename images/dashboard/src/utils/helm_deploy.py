from pyhelm3 import Client
import asyncio

client = Client()

async def list_releases():
    releases = await client.list_releases(all=True, all_namespaces='default')
    release_list = []
    for release in releases:
        revision = await release.current_revision()
        release_info = {
            "name": release.name,
            "namespace": release.namespace,
            "revision": revision.revision,
            "status": str(revision.status)
        }
        release_list.append(release_info)

    return release_list
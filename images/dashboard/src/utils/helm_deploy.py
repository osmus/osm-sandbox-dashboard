from pyhelm3 import Client
import asyncio

client = Client()

avoid_releases = ["prod", "production", "staging"]


async def list_releases(namespace):
    releases = await client.list_releases(
        all=False, all_namespaces=False, namespace=namespace
    )
    release_list = []
    for release in releases:
        if release.name not in avoid_releases:
            revision = await release.current_revision()

            release_info = {
                "name": release.name,
                "namespace": release.namespace,
                "revision": revision.revision,
                "status": str(revision.status).replace("ReleaseRevisionStatus.", ""),
            }
            release_list.append(release_info)

    return release_list

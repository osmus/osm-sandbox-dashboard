from pyhelm3 import Client
import asyncio

client = Client()


async def list_releases():
    releases = await client.list_releases(all=True, all_namespaces=True)
    for release in releases:
        revision = await release.current_revision()
        print(release.name, release.namespace, revision.revision, str(revision.status))


# if __name__ == "__main__":
#     asyncio.run(list_releases())


async def instal_upgrade_release(release, chart):
    try:
        # Install or upgrade a release
        revision = await client.install_or_upgrade_release(
            release, chart, atomic=True, wait=True
        )
        print(
            revision.release.name,
            revision.release.namespace,
            revision.revision,
            str(revision.status),
        )
        return {
            "name": revision.release.name,
            "namespace": revision.release.namespace,
            "revision": revision.revision,
            "status": str(revision.status),
        }
    except Exception as e:
        print(f"Failed to install or upgrade release: {e}")
        return None

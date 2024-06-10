from pyhelm3 import Client
import asyncio

async def list_releases():
    client = Client(kubeconfig="/root/.kube/config")
    releases = await client.list_releases(all=True, all_namespaces=True)
    for release in releases:
        revision = await release.current_revision()
        print(release.name, release.namespace, revision.revision, str(revision.status))

if __name__ == "__main__":
    asyncio.run(list_releases())

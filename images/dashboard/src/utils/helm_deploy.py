from pyhelm3 import Client
import asyncio
import subprocess
import re
import os
client = Client()

avoid_releases = ["prod", "production", "staging"]
osm_sandbox_chart = os.environ.get("OSM_SANDBOX_CHART")
namespace = os.environ.get("NAMESPACE")

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
                # "status": str(revision.status).replace("ReleaseRevisionStatus.", ""),
            }
            release_list.append(release_info)

    return release_list

def replace_placeholders_and_save(template_values_files,values_files):
    with open(template_values_files, 'r') as file:
        file_content = file.read()
    placeholders = re.findall(r'{{(.*?)}}', file_content)
    for placeholder in placeholders:
        env_var = placeholder.strip()
        replacement_value = os.getenv(env_var, '')
        if not replacement_value:
            print(f"Environment variable {env_var} is not set.")
        file_content = file_content.replace(f'{{{{{env_var}}}}}', replacement_value)
    with open(values_files, 'w') as file:
        file.write(file_content)
    return values_files


async def create_upgrade(box_name, values_file):
    print(box_name, values_file)
    command = [
        "helm", "upgrade", "--install", box_name, osm_sandbox_chart,
        "-f", values_file, "--namespace", namespace
    ]
    print(" ".join(command))
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("Helm upgrade/install output:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Error during Helm upgrade/install:", e.stderr)
        return e.stderr

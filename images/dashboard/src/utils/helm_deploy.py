import logging
from pyhelm3 import Client
import asyncio
import subprocess
import re
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = Client()

avoid_releases = ["prod", "production", "staging", "dev"]
osm_sandbox_chart = os.environ.get("OSM_SANDBOX_CHART")


async def list_releases(namespace):
    releases = await client.list_releases(all=False, all_namespaces=False, namespace=namespace)
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


def replace_placeholders_and_save(box_name, label_value):
    os.environ["BOX_NAME"] = box_name
    os.environ["LABEL_VALUE"] = label_value
    values_file = f"values/values_{box_name}.yaml"
    with open("values/osm-seed.template.yaml", "r") as file:
        file_content = file.read()
    placeholders = re.findall(r"{{(.*?)}}", file_content)
    for placeholder in placeholders:
        env_var = placeholder.strip()
        replacement_value = os.getenv(env_var, "")
        if not replacement_value:
            logging.warning(f"Environment variable {env_var} is not set.")
        file_content = file_content.replace(f"{{{{{env_var}}}}}", replacement_value)
    with open(values_file, "w") as file:
        file.write(file_content)
    return values_file


async def create_upgrade(box_name, namespace, values_file):
    command = [
        "helm",
        "upgrade",
        "--install",
        box_name,
        osm_sandbox_chart,
        "-f",
        values_file,
        "--namespace",
        namespace,
    ]
    logging.info(f"Running command: {' '.join(command)}")
    deploy_date = datetime.now().isoformat()

    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        status = "success"
        return result.stdout, deploy_date, status
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        status = "failure"
        return e.stderr, deploy_date, status


async def delete_release(box_name, namespace):
    command = [
        "helm",
        "delete",
        box_name,
        "--namespace",
        namespace,
    ]
    logging.info(f"Running command: {' '.join(command)}")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(e.stderr)
        return e.stderr

import logging
from pyhelm3 import Client
import asyncio
import subprocess
import re
import os
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException


def convert_memory_to_mib(memory_kib):
    return str(int(memory_kib[:-2]) // 1024) + "Mi"


async def list_nodes():
    try:
        config.load_kube_config()
    except ConfigException:
        config.load_incluster_config()
    api_instance = client.CoreV1Api()
    node_list = api_instance.list_node()
    nodes = {}
    for node in node_list.items:
        node_labels = node.metadata.labels
        node_name = node.metadata.name
        label = node_labels.get("nodegroup_type")
        if label != "dashboard-node":

            allocatable_cpu = node.status.allocatable["cpu"]
            allocatable_memory = convert_memory_to_mib(node.status.allocatable["memory"])
            capacity_cpu = node.status.capacity["cpu"]
            capacity_memory = convert_memory_to_mib(node.status.capacity["memory"])

            node_info = {
                "name": node_name,
                "instance_type": node_labels.get("node.kubernetes.io/instance-type"),
                "region": node_labels.get("topology.kubernetes.io/region"),
                "zone": node_labels.get("topology.kubernetes.io/zone"),
                "allocatable": {"cpu": allocatable_cpu, "memory": allocatable_memory},
                "capacity": {"cpu": capacity_cpu, "memory": capacity_memory},
            }
            if label not in nodes:
                nodes[label] = [node_info]
            else:
                nodes[label].append(node_info)
    return nodes


# async def get_resources():
#     nodes = await list_nodes()
#     print(nodes)

# # To run the get_resources coroutine
# if __name__ == "__main__":
#     asyncio.run(get_resources())

import os
import re
import asyncio
from kubernetes import client, config
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import List, Dict, Any
import logging
from pyhelm3 import Client
import subprocess
from kubernetes.config.config_exception import ConfigException


def list_pods(namespace):
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    ret = v1.list_namespaced_pod(namespace=namespace)
    pod_list = []
    for i in ret.items:
        creation_timestamp = i.metadata.creation_timestamp
        if creation_timestamp:
            creation_timestamp_str = creation_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            creation_timestamp_str = None
        pod_info = {
            "namespace": i.metadata.namespace,
            "pod": i.metadata.name,
            "state": i.status.phase,
            "release": i.metadata.labels.get("release", "-"),
            "created": creation_timestamp_str,
            "run": i.metadata.labels.get("run", "-"),
        }
        pod_list.append(pod_info)
    grouped_pods = defaultdict(list)
    for pod in pod_list:
        grouped_pods[pod["release"]].append(pod)
        del pod["release"]
        del pod["namespace"]
    return grouped_pods


def normalize_status(state_list: List[str]) -> str:
    unique_statuses = set(state_list)
    if len(unique_statuses) == 1 and "Running" in unique_statuses:
        return "Running"
    return "Pending"


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

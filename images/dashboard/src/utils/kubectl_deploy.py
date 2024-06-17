import asyncio
from kubernetes import client, config
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import List, Dict, Any


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
            "status": i.status.phase,
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


def normalize_status(status_list: List[str]) -> str:
    unique_statuses = set(status_list)
    if len(unique_statuses) == 1 and "Running" in unique_statuses:
        return "Running"
    return "Pending"

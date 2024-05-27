def check_database_instance(instance_name: str) -> str:
    if instance_name == "xyz":
        return "running"
    else:
        return "not found"

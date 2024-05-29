import os

client_id = os.getenv("OSM_CLIENT_ID")
client_secret = os.getenv("OSM_CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
osm_instance_url = os.getenv("OSM_INSTANCE_URL")
osm_instance_scopes = os.getenv("OSM_INSTANCE_SCOPES")

def get_osm_credentials():
    return client_id, client_secret, redirect_uri, osm_instance_url, osm_instance_scopes

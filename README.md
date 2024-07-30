# OpenStreetMap Sandbox Dashboard

This is a basic dashboard based on an API that allows the creation of OSM-sandbox instances. It also enables users to utilize their OpenStreetMap accounts, allowing them to make edits in the OSM-sandbox.

## Development

```sh
docker compose up db
docker compose run --service-ports api bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```


## Production Deploy

```sh
aws ec2 create-volume \
    --volume-type gp2 \
    --size 10 \
    --availability-zone us-east-1a \
    --tag-specifications \
    'ResourceType=volume,Tags=[{Key=Enviroment,Value=production},{Key=Name,Value=osmseed-production-dashboard}]'
```

Update the IR with the volume ID in the values file, and make a commit in the repository. This will deploy the app in Kubernetes.

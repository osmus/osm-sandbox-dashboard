# OpenStreetMap Sandbox Dashboard

This is a basic dashboard based on an API that allows the creation of OSM-sandbox instances. It also enables users to utilize their OpenStreetMap accounts, allowing them to make edits in the OSM-sandbox.

## Development

```sh
docker compose up db
docker compose run --service-ports api bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
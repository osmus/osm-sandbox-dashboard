# OpenStreetMap Sandbox Dashboard
``
docker compose run --service-ports api bash   
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
helm upgrade --install dashboard ./charts
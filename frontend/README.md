# Frontend Demo

Open `index.html` in a browser after starting the API locally.

## Run the API

```bash
uvicorn src.api.main:app --reload
```

If `uvicorn` is not installed in your environment, install the project dependencies first or use the local API module instructions printed by:

```bash
python -m src.api.main
```

## API Base

The demo uses `http://127.0.0.1:8000` by default. You can edit the API base URL in the top bar.

## Available Endpoints

- `GET /health`
- `GET /config`
- `POST /generate`
- `POST /workflow`
- `POST /campaign`
- `POST /assets`
- `POST /reports/markdown`
- `GET /storage/records`
- `GET /storage/records/{record_type}`
- `GET /storage/records/{record_type}/{record_id}`
- `GET /reports/latest`

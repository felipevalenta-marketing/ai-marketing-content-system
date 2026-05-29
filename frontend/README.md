# Frontend UI Platform

This folder contains the React + TypeScript + Vite frontend for the AI Marketing Content System.

## Install

```bash
cd frontend
npm install
```

## Run

Start the API first:

```bash
uvicorn src.api.main:app --reload
```

Start the frontend:

```bash
npm run dev
```

Build the frontend:

```bash
npm run build
```

Open:

```text
http://127.0.0.1:5173
```

If you prefer proxy-based development, the Vite dev server is configured to proxy API routes to `http://127.0.0.1:8000`.

## API Base URL

Default API base URL:

```text
http://127.0.0.1:8000
```

The app also honors `VITE_API_BASE_URL=http://localhost:8000` at build time.
You can edit the base URL in the top bar of the app at runtime, and the value is stored locally for convenience.

If you need a build-time override in local or CI runs, set:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Pages

- Dashboard
- Content Studio
- Workflow Center
- Campaign Studio
- Asset Studio
- Reports Center
- Storage Explorer
- Analytics Center
- Governance Center
- System Config

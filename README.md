# ai-marketing-content-system
AI-powered multi-brand marketing content system for Wenzel &amp; Partner Real Estate. Generates premium social media copy, property content, visual campaign assets, and AI-driven marketing workflows using scalable modular architecture, markdown knowledge bases, and reusable AI pipelines.

## CLI

Examples:

```bash
python main.py config
python main.py smoke
python main.py generate --dry-run --brand wenzel_partner --platform instagram --content-type instagram_post --audience relocation_clients --location sant_llorenc_des_cardassar --objective generate_leads
python main.py campaign --dry-run --brand wenzel_partner --campaign-type property_launch --platforms instagram,facebook,linkedin
python main.py assets --dry-run --brand wenzel_partner --campaign-type property_launch --platforms instagram,facebook --assets image_prompt,video_prompt
python main.py validate --content-type instagram_post --platform instagram --text "Discover a calm Mallorca lifestyle with trusted local guidance."
python main.py workflow --workflow-type full_campaign_package --brand wenzel_partner --platform instagram --content-type instagram_post --campaign-type property_launch --objective generate_leads --audience relocation_clients --location sant_llorenc_des_cardassar --assets image_prompt,video_prompt,social_post --dry-run --report --markdown
python main.py api
```

Markdown reports export to `outputs/reports/markdown/`, and the export index is stored at `outputs/reports/markdown/index.json`.

## Local API and Frontend UI Platform

Run the API locally with:

```bash
uvicorn src.api.main:app --reload
```

Run the frontend platform:

```bash
cd frontend
npm install
npm run dev
npm run build
```

Open `http://127.0.0.1:5173` for the UI platform. If `uvicorn` is not installed yet, run `python -m src.api.main` to print local startup instructions and the frontend path.

## Deployment

For Docker and production-like local deployment instructions, see [deployment/README.md](deployment/README.md).

The standard local deployment flow is:

```bash
cp .env.example .env
python scripts/check_env.py
docker compose config
docker compose up --build
```

## CI/CD

GitHub Actions validation and release-readiness checks are documented in [docs/CI_CD.md](docs/CI_CD.md).
Use the documented local commands there to mirror the CI pipeline on your machine.
The CI layer now also includes pipeline health, dependency validation, documentation validation, structure validation, and release readiness scoring.

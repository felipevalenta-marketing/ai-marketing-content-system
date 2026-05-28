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
```

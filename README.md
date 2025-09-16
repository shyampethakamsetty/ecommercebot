# demo.nopcommerce AI Assistant

AI-powered shopping automation for nopCommerce demo store with visual workflow testing.

![workflow](https://github.com/user-attachments/assets/dd6ea8a2-e2d6-4e6d-8697-cf896f42db7a)

**📊 Interactive Architecture Diagram**: [View on Excalidraw](https://excalidraw.com/#json=SzqgID-IVMm00_4AyCUN4,ZJAsah-gSFLFTrcdRJRUXQ)

## What it does

- **AI Chat Interface**: Natural language shopping requests
- **Automated Workflows**: Login → Search → Filter → Add to Cart → Checkout
- **Visual Testing**: Screenshots of each step for verification
- **Dynamic Credentials**: Support for multiple test accounts

## How it works

1. **Chat with AI**: `"buy books under 50 with email: test@demo.com password: password1"`
2. **LLM Parsing**: Extracts intent, products, price filters, and credentials
3. **Playwright Automation**: Executes full e-commerce workflow on demo.nopcommerce.com
4. **Visual Feedback**: Real-time screenshots of each automation step

## Quick Start

```bash
# Clone and start all services
git clone <repo>
cd BotMart
docker compose up -d

# Access the chat interface
open http://localhost:3000
```

## Environment

Set `OPENAI_API_KEY` in `.env` for LLM-powered intent recognition.

---

**Tech Stack**: FastAPI • Celery • Playwright • React • PostgreSQL • Redis

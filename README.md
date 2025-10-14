# 🛒 AI-Powered E-commerce Automation Bot

**Intelligent web automation system that enables natural language e-commerce operations with visual workflow documentation.**

![workflow](https://github.com/user-attachments/assets/dd6ea8a2-e2d6-4e6d-8697-cf896f42db7a)

**📊 Interactive Architecture Diagram**: [View on Excalidraw](https://excalidraw.com/#json=SzqgID-IVMm00_4AyCUN4,ZJAsah-gSFLFTrcdRJRUXQ)

## 🚀 Features

### Core Functionality
- **🤖 Natural Language Processing**: Convert human commands into executable e-commerce workflows
- **🔄 Complete Automation**: Login → Search → Filter → Add to Cart → Checkout → Order Confirmation
- **📸 Visual Documentation**: Real-time screenshots of every automation step for transparency
- **👥 Multi-User Support**: Handle multiple test accounts with dynamic credential management
- **🎯 Intelligent Filtering**: Advanced price range and category filtering with LLM parsing
- **📊 Real-time Progress**: Live task tracking with WebSocket updates

### Advanced Capabilities
- **🔒 Secure Authentication**: JWT-based session management with MongoDB Atlas
- **⚡ Asynchronous Processing**: Celery task queue for scalable background processing
- **🛡️ Anti-Detection**: Stealth techniques and proxy rotation for reliable automation
- **📱 Responsive UI**: Modern React interface with real-time chat and image viewing
- **🐳 Containerized**: Full Docker deployment with orchestrated microservices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI       │    │   Celery Worker │
│   (Port 3000)   │◄──►│   Backend       │◄──►│   (Playwright)  │
│                 │    │   (Port 8001)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   MongoDB Atlas │    │   Redis Queue   │
│   (Port 443)    │    │   Database      │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 💬 Usage Examples

### Basic Shopping Commands
```bash
# Simple product search and purchase
"buy me books under 50 bucks user: test@demo.com pass: password1"

# Advanced filtering with price ranges
"add to cart mobile above 500 dollars user: test@demo.com pass: password1"

# Complete checkout workflow
"search for laptops and checkout user: test@demo.com pass: password1"

# Category-specific searches
"buy electronics under 1000 user: test@demo.com pass: password1"
```

### Supported Operations
- **🔍 Product Search**: Natural language product discovery
- **💰 Price Filtering**: Above/below/between price ranges
- **📂 Category Navigation**: Automatic category detection and navigation
- **🛒 Cart Management**: Add single or multiple products to cart
- **💳 Checkout Process**: Complete order placement with saved addresses
- **📧 Account Management**: Automatic login with provided credentials

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance API framework with automatic documentation
- **Celery**: Distributed task queue for asynchronous processing
- **Playwright**: Modern browser automation with stealth capabilities
- **MongoDB Atlas**: Cloud-native NoSQL database for user and session data
- **Redis**: In-memory data store for task queuing and caching
- **JWT**: Secure authentication and session management

### Frontend
- **React.js**: Modern UI library with hooks and functional components
- **Vite**: Fast build tool and development server
- **Axios**: HTTP client for API communication
- **CSS3**: Advanced styling with gradients, animations, and responsive design

### Infrastructure
- **Docker & Docker Compose**: Containerization and orchestration
- **Nginx**: Reverse proxy and SSL termination
- **Linux**: Ubuntu server environment
- **Cloudflare**: DNS and security services

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- OpenAI API key for LLM functionality
- Domain name (optional, for production deployment)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ecommercebot
```

2. **Configure environment variables**
```bash
# Copy the example environment file
cp .env.template .env

# Edit .env with your configuration
nano .env
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/ecommercebot
SECRET_KEY=your_secret_key_for_jwt
REDIS_URL=redis://redis:6379
```

3. **Start all services**
```bash
# Build and start all containers
docker-compose up -d

# Check service status
docker-compose ps
```

4. **Access the application**
- **Frontend**: https://your-domain.com or http://localhost:3000
- **API Documentation**: https://your-domain.com:8001/docs
- **Flower (Task Monitor)**: https://your-domain.com:5555

### First-Time Setup

1. **Register Test Account**: Visit https://demo.nopcommerce.com/register
2. **Add Saved Address**: Configure billing/shipping address in account settings
3. **Start Chatting**: Use the format: `"buy books under 50 user: your@email.com pass: yourpassword"`

## 📋 API Endpoints

### Chat Interface
- `POST /api/chat/query` - Submit natural language shopping request
- `GET /api/tasks/{task_id}` - Get task status and results
- `GET /api/artifacts/{filename}` - Retrieve screenshots and HTML artifacts

### Task Management
- `POST /api/tasks/{task_id}/result` - Update task completion status
- `GET /api/workflows` - List available automation workflows

## 🔧 Development

### Local Development Setup

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend development
cd frontend
npm install
npm run dev

# Worker development
cd workers
pip install -r requirements.txt
celery -A celery_app worker --loglevel=info
```

### Code Structure
```
ecommercebot/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── routers/        # API route handlers
│   │   ├── services/       # Business logic
│   │   └── models/         # Database models
├── frontend/               # React frontend
│   ├── src/
│   │   ├── Chat.jsx        # Main chat interface
│   │   └── main.jsx        # App entry point
├── workers/                # Celery workers
│   ├── worker/
│   │   ├── playwright_runner.py    # Browser automation
│   │   ├── workflows.py            # Workflow definitions
│   │   └── botasaurus_adapter.py   # Anti-detection
└── docker-compose.yml      # Service orchestration
```

## 🧪 Testing

### Manual Testing
1. Use the web interface to submit various shopping commands
2. Monitor task progress in Flower dashboard
3. Verify screenshots are captured correctly
4. Test with different user accounts and product categories

### Automated Testing
```bash
# Run backend tests
cd backend && python -m pytest

# Run frontend tests
cd frontend && npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🔒 Security Considerations

- **Credential Handling**: User credentials are processed securely and not stored
- **Proxy Rotation**: Multiple proxy servers prevent IP blocking
- **Rate Limiting**: Built-in delays and throttling to avoid overwhelming target sites
- **SSL/TLS**: All communications encrypted with valid certificates
- **Input Validation**: Comprehensive validation of user inputs and API requests

## 📊 Monitoring & Logging

- **Real-time Task Monitoring**: Flower dashboard for Celery task status
- **Comprehensive Logging**: Structured logging across all services
- **Error Tracking**: Automatic error capture and reporting
- **Performance Metrics**: Response times and success rates tracking

## 🚀 Deployment
Took a subdomain browserautomation.uckdns.org - pointed to -> my ec2 IP Nginx reverse proxy to -> localhost:3000 ( exposed as 3000 with docker 3000) with proper SSL handling for 443 traffic HTTPS support

Backend is not exposed and was handled internally reverse proxy /api/
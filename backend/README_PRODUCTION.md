# Production Deployment - Quick Start

## Files Created

1. **`run.py`** - Production-ready run script with support for multiple WSGI servers
2. **`gunicorn_config.py`** - Gunicorn configuration file
3. **`systemd.service`** - Systemd service file for Linux deployment
4. **`Dockerfile`** - Docker container configuration
5. **`docker-compose.yml`** - Docker Compose configuration
6. **`start.sh`** - Startup script with environment checks
7. **`.env.example`** - Example environment variables file
8. **`requirements_production.txt`** - Production dependencies

## Quick Start

### 1. Setup Environment

```bash
# Copy environment file
cp .env.example .env

# Edit .env and set your API key
nano .env
```

### 2. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements_production.txt

# Install Playwright browsers
playwright install chromium
```

### 3. Run the Server

#### Option A: Using the run script (Recommended)

```bash
# Using Waitress (recommended for production)
export SERVER_TYPE=waitress
python run.py

# Or using Gunicorn
export SERVER_TYPE=gunicorn
python run.py

# Or using the startup script
./start.sh
```

#### Option B: Using Gunicorn directly

```bash
gunicorn --config gunicorn_config.py "flask_app.app:create_app()"
```

#### Option C: Using Docker

```bash
# Build the image
docker build -t browser-agent-api .

# Run the container
docker run -d -p 5000:5000 \
  -e GEMINI_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  --name browser-agent-api \
  browser-agent-api

# Or use Docker Compose
docker-compose up -d
```

## Environment Variables

Required:
- `GEMINI_API_KEY` - Your Google Gemini API key

Optional:
- `HOST` - Host to bind to (default: 0.0.0.0)
- `PORT` - Port to bind to (default: 5000)
- `SERVER_TYPE` - Server type: `flask`, `waitress`, or `gunicorn` (default: flask)
- `SECRET_KEY` - Flask secret key
- `FLASK_ENV` - Flask environment (default: production)
- `WAITRESS_THREADS` - Number of Waitress threads (default: 4)
- `GUNICORN_WORKERS` - Number of Gunicorn workers (default: 4)

## Health Check

```bash
curl http://localhost:5000/health
```

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint
- `POST /api/v1/browser-agent/execute` - Execute browser task

## Production Checklist

- [ ] Set `GEMINI_API_KEY` in environment
- [ ] Set `SECRET_KEY` for Flask sessions
- [ ] Use `SERVER_TYPE=waitress` or `SERVER_TYPE=gunicorn`
- [ ] Configure reverse proxy (Nginx) if needed
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Test health check endpoint

## Troubleshooting

### Port Already in Use
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

### Playwright Browser Issues
```bash
playwright install chromium
```

### Memory Issues
- Reduce number of workers/threads
- Monitor browser memory usage
- Consider using a browser pool

For more details, see `PRODUCTION_DEPLOYMENT.md`.


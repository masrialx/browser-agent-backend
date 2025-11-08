# Production Deployment Guide

This guide explains how to deploy the Browser Agent Flask API in production.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY and other variables
```

### 3. Run the Server

#### Option A: Using Flask Development Server (Not Recommended for Production)

```bash
python run.py
```

#### Option B: Using Waitress (Recommended for Production)

```bash
export SERVER_TYPE=waitress
python run.py
```

#### Option C: Using Gunicorn (Recommended for High Traffic)

```bash
export SERVER_TYPE=gunicorn
python run.py
```

Or use Gunicorn directly:

```bash
gunicorn --config gunicorn_config.py flask_app.app:create_app
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `production` |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `HOST` | Host to bind to | `0.0.0.0` |
| `PORT` | Port to bind to | `5000` |
| `SERVER_TYPE` | Server type: `flask`, `waitress`, or `gunicorn` | `flask` |
| `GEMINI_API_KEY` | Google Gemini API key (required) | - |
| `SECRET_KEY` | Flask secret key | - |
| `WAITRESS_THREADS` | Number of Waitress threads | `4` |
| `GUNICORN_WORKERS` | Number of Gunicorn workers | `4` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Docker Deployment

### Build and Run with Docker

```bash
# Build the image
docker build -t browser-agent-api .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e GEMINI_API_KEY=your_api_key \
  -e SECRET_KEY=your_secret_key \
  --name browser-agent-api \
  browser-agent-api
```

### Using Docker Compose

```bash
# Set environment variables in .env file
export GEMINI_API_KEY=your_api_key
export SECRET_KEY=your_secret_key

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## Systemd Service (Linux)

### 1. Create Service File

Copy `systemd.service` to `/etc/systemd/system/browser-agent-api.service` and update the paths:

```bash
sudo cp systemd.service /etc/systemd/system/browser-agent-api.service
sudo nano /etc/systemd/system/browser-agent-api.service
```

### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable browser-agent-api
sudo systemctl start browser-agent-api
```

### 3. Check Status

```bash
sudo systemctl status browser-agent-api
sudo journalctl -u browser-agent-api -f
```

## Nginx Reverse Proxy

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### SSL with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring and Logging

### Log Files

Logs are written to:
- `app.log` (if writable)
- stdout/stderr (for Docker/systemd)

### Health Check Endpoint

The API includes a health check endpoint:

```bash
curl http://localhost:5000/health
```

### Monitoring with Prometheus

Add Prometheus metrics endpoint (optional):

```python
from prometheus_client import make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware

app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
```

## Performance Tuning

### Waitress Configuration

- Increase `WAITRESS_THREADS` for more concurrent requests
- Default: 4 threads
- Recommended: 4-8 threads per CPU core

### Gunicorn Configuration

- Increase `GUNICORN_WORKERS` for more worker processes
- Formula: `(2 × CPU cores) + 1`
- Update `gunicorn_config.py` for custom settings

### Playwright Configuration

- Playwright browsers are installed in the container
- For production, consider using a headless browser pool
- Monitor memory usage as browsers can be memory-intensive

## Security Considerations

1. **Environment Variables**: Never commit `.env` file to version control
2. **Secret Key**: Use a strong, random secret key in production
3. **API Keys**: Store API keys securely and rotate them regularly
4. **HTTPS**: Always use HTTPS in production (use Nginx with SSL)
5. **Firewall**: Restrict access to the API port
6. **Rate Limiting**: Consider adding rate limiting for API endpoints

## Troubleshooting

### Port Already in Use

```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill the process
sudo kill -9 <PID>
```

### Playwright Browser Issues

```bash
# Reinstall Playwright browsers
playwright install chromium

# Or in Docker
docker exec -it browser-agent-api playwright install chromium
```

### Memory Issues

- Reduce number of workers/threads
- Increase container memory limit
- Monitor browser memory usage

### Logs

```bash
# View application logs
tail -f app.log

# View Docker logs
docker logs -f browser-agent-api

# View systemd logs
sudo journalctl -u browser-agent-api -f
```

## Production Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Configure `GEMINI_API_KEY`
- [ ] Set strong `SECRET_KEY`
- [ ] Use `SERVER_TYPE=waitress` or `SERVER_TYPE=gunicorn`
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up SSL/HTTPS
- [ ] Configure firewall
- [ ] Set up monitoring and logging
- [ ] Test health check endpoint
- [ ] Load test the API
- [ ] Set up backups
- [ ] Configure auto-restart (systemd/Docker)

## Support

For issues or questions, please check the logs and ensure all environment variables are set correctly.


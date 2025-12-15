# WordRare Web Deployment Guide

This guide explains how to deploy the WordRare web application to various hosting platforms.

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
# Install main project dependencies
pip install -r requirements.txt

# Install web-specific dependencies
pip install -r web/requirements.txt
```

### 2. Set Up Database

```bash
# Initialize databases
python scripts/setup_databases.py

# Optional: Run ingestion to populate database
python -m src.ingestion.phrontistery_scraper
python -m src.ingestion.dictionary_enricher
```

### 3. Run Development Server

```bash
cd web
python app.py
```

Visit http://localhost:5000 in your browser.

---

## Production Deployment

### Option 1: Deploy to Heroku

**Prerequisites**: Heroku account and Heroku CLI installed

#### Step 1: Create Required Files

Create `Procfile` in project root:
```
web: gunicorn --chdir web app:app
```

Create `runtime.txt`:
```
python-3.9.18
```

Merge requirements:
```bash
cat requirements.txt web/requirements.txt > requirements-all.txt
mv requirements-all.txt requirements.txt
```

#### Step 2: Deploy

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-wordrare-app

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git add .
git commit -m "Prepare for Heroku deployment"
git push heroku main

# Open app
heroku open
```

#### Step 3: Set Environment Variables

```bash
heroku config:set WORDNIK_API_KEY=your_api_key_here
```

---

### Option 2: Deploy to Railway

**Prerequisites**: Railway account (https://railway.app)

#### Step 1: Connect Repository

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your WordRare repository
4. Railway will auto-detect Python

#### Step 2: Configure

Create `railway.json`:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "cd web && gunicorn app:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### Step 3: Set Environment Variables

In Railway dashboard:
- Add `WORDNIK_API_KEY` variable
- Set `PORT` (Railway provides this automatically)

---

### Option 3: Deploy to Render

**Prerequisites**: Render account (https://render.com)

#### Step 1: Create Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository

#### Step 2: Configure Build Settings

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd web && gunicorn app:app --bind 0.0.0.0:$PORT`
- **Environment**: Python 3

#### Step 3: Set Environment Variables

Add in Render dashboard:
- `WORDNIK_API_KEY`: Your API key
- `PYTHON_VERSION`: 3.9.18

---

### Option 4: Deploy to DigitalOcean App Platform

**Prerequisites**: DigitalOcean account

#### Step 1: Create App

1. Go to https://cloud.digitalocean.com/apps
2. Click "Create App"
3. Choose "GitHub" as source
4. Select your repository

#### Step 2: Configure

Create `.do/app.yaml`:
```yaml
name: wordrare
services:
- name: web
  github:
    repo: your-username/wordrare
    branch: main
  run_command: cd web && gunicorn app:app
  environment_slug: python
  instance_size_slug: basic-xxs
  instance_count: 1
  http_port: 8080
  routes:
  - path: /
  envs:
  - key: WORDNIK_API_KEY
    scope: RUN_TIME
    value: ${WORDNIK_API_KEY}
```

---

### Option 5: Deploy to AWS (Elastic Beanstalk)

**Prerequisites**: AWS account and EB CLI

#### Step 1: Initialize

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.9 wordrare --region us-east-1
```

#### Step 2: Configure

Create `.ebextensions/python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: web/app:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
```

#### Step 3: Deploy

```bash
eb create wordrare-env
eb open
```

---

### Option 6: Deploy with Docker

#### Step 1: Create Dockerfile

Create `Dockerfile` in project root:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt web/requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r web/requirements.txt

# Copy application
COPY . .

# Set up database
RUN python scripts/setup_databases.py

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--chdir", "web", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - WORDNIK_API_KEY=${WORDNIK_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

#### Step 3: Run

```bash
# Build
docker build -t wordrare .

# Run
docker run -p 5000:5000 \
  -e WORDNIK_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  wordrare

# Or with docker-compose
docker-compose up -d
```

#### Deploy to Docker Hub

```bash
# Tag
docker tag wordrare your-username/wordrare:latest

# Push
docker push your-username/wordrare:latest
```

---

### Option 7: Deploy to Vercel (Serverless)

**Note**: Vercel is optimized for serverless, which may require modifications.

Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "web/app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "web/app.py"
    }
  ]
}
```

Deploy:
```bash
npm i -g vercel
vercel
```

---

## Environment Variables

All deployment methods require these environment variables:

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `WORDNIK_API_KEY` | No | Wordnik API key for dictionary enrichment | None |
| `DATABASE_PATH` | No | Path to SQLite database | `data/wordrare.db` |
| `PORT` | No | Server port (auto-set by most platforms) | 5000 |
| `FLASK_ENV` | No | Flask environment | `production` |

---

## Performance Optimization

### 1. Enable Caching

Add to `web/app.py`:
```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/api/forms')
@cache.cached()
def get_forms():
    # ...
```

### 2. Use Production WSGI Server

Replace development server with Gunicorn:
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 web.app:app
```

### 3. Enable GZIP Compression

```python
from flask_compress import Compress
Compress(app)
```

### 4. Database Connection Pooling

Update `src/database/session.py`:
```python
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

---

## Database Considerations

### SQLite (Default)

**Pros**: Simple, no setup required
**Cons**: Single-file, not ideal for high traffic

**Recommendation**: Fine for low-medium traffic (< 1000 req/day)

### PostgreSQL (Production)

For high-traffic deployments, use PostgreSQL:

```python
# Update src/config.py
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:pass@localhost/wordrare'
)
```

Migrate:
```bash
# Export from SQLite
sqlite3 data/wordrare.db .dump > backup.sql

# Import to PostgreSQL
psql wordrare < backup.sql
```

---

## Monitoring & Logging

### Add Logging

Update `web/app.py`:
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    handler = RotatingFileHandler(
        'logs/wordrare.log',
        maxBytes=10000000,
        backupCount=10
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
```

### Health Check Endpoint

Already included at `/api/health`:
```bash
curl http://your-app.com/api/health
```

### Monitor with Uptime Robot

Add your deployed URL to https://uptimerobot.com for monitoring.

---

## Security Best Practices

### 1. Use HTTPS

Most platforms (Heroku, Render, Vercel) provide HTTPS automatically.

For custom servers, use Let's Encrypt:
```bash
certbot --nginx -d yourdomain.com
```

### 2. Set Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### 3. Rate Limiting

```bash
pip install flask-limiter
```

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["100 per hour"]
)

@app.route('/api/generate')
@limiter.limit("10 per minute")
def generate_poem():
    # ...
```

---

## Custom Domain Setup

### Heroku
```bash
heroku domains:add www.yourdomain.com
```

Then add CNAME record in your DNS:
- Host: `www`
- Target: Your Heroku app URL

### Render
1. Go to Settings → Custom Domain
2. Add your domain
3. Update DNS with provided values

### Vercel
```bash
vercel domains add yourdomain.com
```

---

## Troubleshooting

### Issue: "Module not found"
**Solution**: Ensure all dependencies in `requirements.txt`

### Issue: "Database locked"
**Solution**: Use PostgreSQL for multi-user access

### Issue: "Timeout generating poems"
**Solution**: Increase server timeout or reduce `max_iterations`

### Issue: "Out of memory"
**Solution**: Use larger instance or reduce embeddings batch size

---

## Cost Estimation

| Platform | Free Tier | Paid (Basic) | Best For |
|----------|-----------|--------------|----------|
| Heroku | 550 hours/mo | $7/mo | Simple deployment |
| Railway | $5 free credit | $5-20/mo | Modern stack |
| Render | 750 hours/mo | $7/mo | Full control |
| DigitalOcean | $200 credit | $5-12/mo | Scalability |
| Vercel | Unlimited | $20/mo | Serverless |

---

## Recommended Setup

**For Personal/Demo**: Render free tier
**For Production**: Railway or DigitalOcean ($5-10/mo)
**For Scale**: AWS/Docker with PostgreSQL

---

## Next Steps

1. Choose a deployment platform
2. Set up environment variables
3. Deploy application
4. Test all endpoints
5. Set up monitoring
6. Configure custom domain (optional)

For issues, check the logs:
```bash
# Heroku
heroku logs --tail

# Render
View in dashboard

# Docker
docker logs <container-id>
```

---

## Support

For deployment issues:
- Check platform-specific documentation
- Review application logs
- Test endpoints with curl/Postman
- Verify environment variables are set

Happy deploying! 🚀

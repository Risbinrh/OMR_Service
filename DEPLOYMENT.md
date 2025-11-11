# Deployment Guide - OMR Microservice

## Pre-Deployment Checklist

- [ ] Ensure `epoch20.pt` model is in `models/` directory
- [ ] Update `.env` file with production settings
- [ ] Review and update CORS origins in `app/config.py`
- [ ] Set up secrets/API keys if needed
- [ ] Test locally with Docker: `docker-compose up`
- [ ] Create `.env` from `.env.example`

## Deployment Options

### 1. Docker Hub (Recommended)

**Step 1: Build and Tag**
```bash
cd omr-microservice
docker build -t your-username/omr-microservice:latest .
```

**Step 2: Push to Docker Hub**
```bash
docker login
docker push your-username/omr-microservice:latest
```

**Step 3: Deploy anywhere**
```bash
docker pull your-username/omr-microservice:latest
docker run -d -p 8000:8000 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/answer_keys:/app/answer_keys \
  your-username/omr-microservice:latest
```

---

### 2. Render.com (Easy, Free Tier Available)

**Steps:**
1. Push code to GitHub
2. Go to https://render.com
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Select `omr-microservice` folder
6. Render will auto-detect Docker
7. Click "Create Web Service"

**Configuration:**
- Environment: Docker
- Docker Context: `omr-microservice`
- Health Check Path: `/health`
- Port: 8000

**Free Tier Limitations:**
- Sleeps after 15 min inactivity
- 512 MB RAM
- Shared CPU

---

### 3. Railway.app (Easy, $5/month)

**Steps:**
1. Push code to GitHub
2. Go to https://railway.app
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Docker
6. Add environment variables
7. Deploy!

**Configuration:**
Railway reads `deploy/railway.json` automatically

---

### 4. Fly.io (Global Edge Network)

**Steps:**

1. Install Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh  # Linux/Mac
# or
iwr https://fly.io/install.ps1 -useb | iex  # Windows
```

2. Login:
```bash
fly auth login
```

3. Initialize app:
```bash
cd omr-microservice
fly launch
```

4. Deploy:
```bash
fly deploy
```

**Configuration (fly.toml):**
```toml
app = "omr-microservice"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.http_checks]]
    interval = 10000
    grace_period = "5s"
    method = "get"
    path = "/health"
    protocol = "http"
    timeout = 2000
```

---

### 5. Google Cloud Run (Serverless, Pay-per-use)

**Steps:**

1. Install gcloud CLI
2. Authenticate:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

3. Build and deploy:
```bash
cd omr-microservice

# Build with Cloud Build
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/omr-microservice

# Deploy to Cloud Run
gcloud run deploy omr-microservice \
  --image gcr.io/YOUR_PROJECT_ID/omr-microservice \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --port 8000
```

**Pricing:**
- Free tier: 2M requests/month
- Pay only for actual usage
- Auto-scales to zero

---

### 6. AWS (EC2 with Docker)

**Steps:**

1. Launch EC2 instance (Ubuntu 22.04, t3.medium or larger)

2. SSH into instance:
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

3. Install Docker:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker ubuntu
```

4. Clone repository:
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo/omr-microservice
```

5. Create `.env` file:
```bash
cp .env.example .env
nano .env  # Edit configuration
```

6. Start service:
```bash
docker-compose up -d
```

7. Configure security group to allow port 8000

**Access:**
```
http://your-ec2-ip:8000
```

---

### 7. AWS ECS (Container Service)

**Steps:**

1. Create ECR repository:
```bash
aws ecr create-repository --repository-name omr-microservice
```

2. Build and push:
```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com

# Build
docker build -t omr-microservice .

# Tag
docker tag omr-microservice:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/omr-microservice:latest

# Push
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/omr-microservice:latest
```

3. Create ECS cluster and task definition (via AWS Console or CLI)

---

### 8. Azure Container Instances

**Steps:**

1. Create resource group:
```bash
az group create --name omr-microservice-rg --location eastus
```

2. Create container registry:
```bash
az acr create --resource-group omr-microservice-rg \
  --name omrmicroservice --sku Basic
```

3. Build and push:
```bash
az acr build --registry omrmicroservice \
  --image omr-microservice:latest .
```

4. Deploy:
```bash
az container create \
  --resource-group omr-microservice-rg \
  --name omr-api \
  --image omrmicroservice.azurecr.io/omr-microservice:latest \
  --cpu 2 --memory 4 \
  --registry-login-server omrmicroservice.azurecr.io \
  --ports 8000 \
  --dns-name-label omr-microservice \
  --environment-variables HOST=0.0.0.0 PORT=8000
```

---

### 9. Heroku (Simple but Paid)

**Steps:**

1. Install Heroku CLI
2. Login:
```bash
heroku login
```

3. Create app:
```bash
cd omr-microservice
heroku create your-app-name
```

4. Set stack to container:
```bash
heroku stack:set container
```

5. Deploy:
```bash
git push heroku main
```

**Note:** Requires `heroku.yml` file (already included)

---

### 10. DigitalOcean App Platform

**Steps:**

1. Push code to GitHub
2. Go to DigitalOcean → Apps
3. Create App → Connect GitHub
4. Select repository and branch
5. Configure:
   - Type: Web Service
   - Environment: Docker
   - Port: 8000
   - Health Check: `/health`
6. Click "Create Resources"

**Pricing:**
- Starts at $5/month
- Auto-scaling available
- Managed platform

---

## Environment Variables

Required variables for production:

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=False

# Paths
MODEL_PATH=models/epoch20.pt
UPLOAD_DIR=uploads
RESULTS_DIR=results
ANSWER_KEYS_DIR=answer_keys

# CORS (update with your domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: API Authentication
# API_KEY=your_secret_key_here
```

---

## Post-Deployment

### 1. Verify Deployment

```bash
# Health check
curl https://your-domain.com/health

# API docs
open https://your-domain.com/docs
```

### 2. Test Endpoints

```bash
# Test processing
curl -X POST https://your-domain.com/api/v1/process \
  -F "file=@test.jpg" \
  -F "save_debug=true"
```

### 3. Monitor Logs

**Docker:**
```bash
docker logs -f container-name
```

**Cloud Platforms:**
- Use platform's log viewer
- Set up log aggregation (Datadog, LogDNA, etc.)

### 4. Set Up Monitoring

- **Health Checks:** Most platforms support automatic health checks
- **Uptime Monitoring:** UptimeRobot, Pingdom
- **APM:** New Relic, Datadog
- **Error Tracking:** Sentry

---

## Scaling Considerations

### Vertical Scaling
- Increase CPU/RAM for your container
- Recommended: 2 CPU cores, 4GB RAM minimum

### Horizontal Scaling
- Run multiple instances behind a load balancer
- Use managed platforms (Cloud Run, ECS, etc.)

### Database
- For production, consider adding PostgreSQL for answer keys
- Use Redis for caching

---

## Security Best Practices

1. **Enable HTTPS** - Use Let's Encrypt or cloud provider SSL
2. **Add Authentication** - API keys, JWT tokens
3. **Rate Limiting** - Prevent abuse
4. **Input Validation** - Already implemented
5. **CORS Configuration** - Restrict to your domains
6. **Secrets Management** - Use environment variables, not hardcoded
7. **Regular Updates** - Keep dependencies updated

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker logs container-name

# Common issues:
# - Model file missing
# - Port already in use
# - Insufficient memory
```

### Health Check Failing
```bash
# Test locally
curl http://localhost:8000/health

# Check if model loaded correctly
```

### Out of Memory
```bash
# Increase container memory
# Minimum recommended: 2GB
```

---

## Cost Comparison

| Platform | Free Tier | Paid (Starting) | Best For |
|----------|-----------|-----------------|----------|
| Render | Yes (limited) | $7/month | Quick start |
| Railway | $5 credit | $5/month | Simple apps |
| Fly.io | Yes (3 VMs) | Pay-per-use | Global edge |
| Google Cloud Run | 2M requests | Pay-per-use | Serverless |
| AWS EC2 | 1 year (t2.micro) | $15/month | Full control |
| DigitalOcean | No | $5/month | Managed |
| Heroku | No | $7/month | Simple deploy |

---

## Recommended Setup for Production

1. **Platform:** Google Cloud Run or Fly.io
2. **Database:** PostgreSQL (for answer keys)
3. **Storage:** Cloud Storage (for uploads/results)
4. **CDN:** Cloudflare (for API)
5. **Monitoring:** Sentry + UptimeRobot
6. **CI/CD:** GitHub Actions (already configured)

---

## Support

For deployment issues:
1. Check platform documentation
2. Review application logs
3. Verify environment variables
4. Test locally with Docker first

---

**Ready to deploy!** Choose your platform and follow the steps above.

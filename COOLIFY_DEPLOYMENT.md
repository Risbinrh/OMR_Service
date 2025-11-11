# OMR Service - Coolify Deployment Guide

Complete guide for deploying the OMR Detection & Autograding Microservice to Coolify.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Deployment Steps](#detailed-deployment-steps)
- [Configuration](#configuration)
- [Persistent Storage](#persistent-storage)
- [Health Checks](#health-checks)
- [SSL/HTTPS Setup](#sslhttps-setup)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Post-Deployment Testing](#post-deployment-testing)

---

## Overview

**Service Type:** Python FastAPI Microservice
**Port:** 8000
**Database Required:** No (uses JSON file-based storage)
**External Dependencies:** None
**Resource Requirements:**
- **RAM:** 2-4 GB (minimum 2 GB)
- **CPU:** 1-2 cores
- **Disk:** 10 GB (includes model and uploaded files)
- **Model File:** 67.3 MB (YOLOv8)

---

## Prerequisites

### 1. Coolify Server
- Coolify installed and running (v4.0 or later recommended)
- Access to Coolify dashboard
- Server with at least 4 GB RAM and 2 CPU cores

### 2. Git Repository
- Code pushed to a Git repository (GitHub, GitLab, Bitbucket, etc.)
- Repository accessible by Coolify (public or with deploy keys)

### 3. Domain (Optional)
- Custom domain name configured (or use Coolify's generated subdomain)
- DNS configured to point to your Coolify server

### 4. SSL Certificate (Optional but Recommended)
- Let's Encrypt email address for automatic SSL
- Or bring your own SSL certificate

---

## Quick Start

### Option 1: Deploy from GitHub Repository

1. **Create New Application in Coolify**
   - Go to Coolify Dashboard → Applications → New Application
   - Select "Public Repository" or "Private Repository"
   - Enter repository URL: `https://github.com/yourusername/OMR_Service`

2. **Configure Build Settings**
   - Build Pack: **Dockerfile** (auto-detected)
   - Branch: **main** (or your default branch)
   - Port: **8000**
   - Health Check Path: **/health**

3. **Set Environment Variables** (see [Configuration](#configuration))

4. **Configure Volumes** (see [Persistent Storage](#persistent-storage))

5. **Deploy**
   - Click "Deploy" button
   - Monitor build logs
   - Wait for deployment to complete

### Option 2: Deploy with Docker Compose

1. **Create New Application**
   - Select "Docker Compose" option
   - Upload or paste the provided `docker-compose.yml`

2. **Review Configuration**
   - Ensure volumes are properly mapped
   - Verify environment variables

3. **Deploy**

---

## Detailed Deployment Steps

### Step 1: Create New Application

1. Log in to your Coolify dashboard
2. Navigate to **Projects** → Select or create a project
3. Click **+ New** → **Application**
4. Choose deployment method:
   - **Public Repository** (for public GitHub repos)
   - **Private Repository** (requires SSH key or token)
   - **Docker Compose** (using existing compose file)

### Step 2: Repository Configuration

**For Git Repository Deployment:**

1. **Repository URL:**
   ```
   https://github.com/yourusername/OMR_Service.git
   ```
   Or for private repos:
   ```
   git@github.com:yourusername/OMR_Service.git
   ```

2. **Branch:** `main` (or your default branch)

3. **Build Pack:** Select **Dockerfile**
   - Coolify will auto-detect the Dockerfile in the root directory

4. **Docker Image:** Leave empty (will build from Dockerfile)

### Step 3: Application Settings

1. **General Settings:**
   - **Name:** `omr-service` or your preferred name
   - **Description:** OMR Detection & Autograding API
   - **Port:** `8000`
   - **Protocol:** HTTP

2. **Build Settings:**
   - **Dockerfile Location:** `/Dockerfile` (default)
   - **Docker Context:** `/` (root directory)
   - **Build Arguments:** None required

3. **Network Settings:**
   - **Expose Port:** `8000`
   - **Public Port:** 80 or 443 (with SSL)
   - **Health Check Path:** `/health`

### Step 4: Environment Variables

Configure the following environment variables in Coolify:

**Required Variables:**

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000

# Application Paths (use container paths)
MODEL_PATH=/app/models/epoch20.pt
UPLOAD_DIR=/app/uploads
RESULTS_DIR=/app/results
ANSWER_KEYS_DIR=/app/answer_keys
```

**Optional Variables:**

```bash
# Debug Mode (set to False for production)
DEBUG=False
RELOAD=False

# CORS Configuration (restrict in production)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# File Upload Limits
MAX_UPLOAD_SIZE=10485760
```

**To add environment variables in Coolify:**
1. Go to Application → **Environment Variables**
2. Click **+ Add Variable**
3. Enter **Key** and **Value**
4. Mark as **Build Time** or **Runtime** (use Runtime for these vars)
5. Click **Save**

### Step 5: Persistent Storage (Volumes)

Configure persistent volumes to retain data across deployments:

**Required Volumes:**

| Container Path | Host Path | Description |
|----------------|-----------|-------------|
| `/app/uploads` | `/data/omr-service/uploads` | Uploaded OMR images |
| `/app/results` | `/data/omr-service/results` | Processing results (JSON) |
| `/app/answer_keys` | `/data/omr-service/answer_keys` | Stored answer keys |

**To configure volumes in Coolify:**

1. Go to Application → **Storage**
2. Click **+ Add Volume**
3. For each volume:
   - **Source:** `/data/omr-service/uploads` (or your preferred path)
   - **Destination:** `/app/uploads`
   - **Mode:** `rw` (read-write)
   - Click **Save**
4. Repeat for `results` and `answer_keys`

**Alternative: Named Volumes**
```
omr-uploads:/app/uploads
omr-results:/app/results
omr-answer-keys:/app/answer_keys
```

### Step 6: Health Check Configuration

Configure health checks for automatic monitoring and recovery:

1. **Health Check Settings:**
   - **Path:** `/health`
   - **Port:** `8000`
   - **Interval:** 30 seconds
   - **Timeout:** 10 seconds
   - **Retries:** 3
   - **Start Period:** 40 seconds (model loading time)

2. **Expected Response:**
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-11-11T10:30:00",
     "model_loaded": true
   }
   ```

**To configure in Coolify:**
1. Go to Application → **Health Check**
2. Enable health check
3. Set **Path:** `/health`
4. Configure intervals as above
5. Save settings

### Step 7: Resource Limits

Set resource limits to ensure stable performance:

1. **Memory:**
   - **Reservation:** 2 GB
   - **Limit:** 4 GB

2. **CPU:**
   - **Reservation:** 1.0 cores
   - **Limit:** 2.0 cores

**To configure in Coolify:**
1. Go to Application → **Resources**
2. Set memory and CPU limits
3. Save settings

### Step 8: Restart Policy

Configure automatic restart on failure:

1. **Restart Policy:** `unless-stopped`
2. **Max Retries:** 3
3. **Restart Delay:** 10 seconds

### Step 9: Deploy the Application

1. Review all settings
2. Click **Deploy** button
3. Monitor deployment logs in real-time
4. Wait for build to complete (5-10 minutes first time)
5. Wait for health check to pass

**Deployment Stages:**
1. Cloning repository
2. Building Docker image
3. Installing system dependencies
4. Installing Python packages
5. Starting container
6. Health check validation
7. Service ready

---

## Configuration

### Application Configuration File

The service uses Pydantic Settings for configuration management. Settings are loaded from:
1. Environment variables (highest priority)
2. `.env` file (if present)
3. Default values in `app/config.py`

### Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server listen port |
| `DEBUG` | `False` | Enable debug mode |
| `RELOAD` | `False` | Auto-reload on code changes |
| `MODEL_PATH` | `/app/models/epoch20.pt` | YOLOv8 model file path |
| `UPLOAD_DIR` | `/app/uploads` | Upload directory |
| `RESULTS_DIR` | `/app/results` | Results directory |
| `ANSWER_KEYS_DIR` | `/app/answer_keys` | Answer keys directory |
| `CORS_ORIGINS` | `*` | CORS allowed origins |
| `MAX_UPLOAD_SIZE` | `10485760` | Max upload size (bytes) |

### CORS Configuration

**Development (Allow All):**
```bash
CORS_ORIGINS=*
```

**Production (Specific Domains):**
```bash
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://app.yourdomain.com
```

---

## Persistent Storage

### Storage Architecture

The service requires persistent storage for three directories:

1. **Uploads Directory** (`/app/uploads`)
   - Stores uploaded OMR images
   - Images are kept for debugging and audit trail
   - Can be cleaned up periodically

2. **Results Directory** (`/app/results`)
   - Stores JSON processing results
   - One JSON file per processed image
   - Used for result retrieval and analytics

3. **Answer Keys Directory** (`/app/answer_keys`)
   - Stores answer key definitions
   - JSON files with UUID-based naming
   - Critical data - must be backed up

### Backup Strategy

**Recommended Backup Schedule:**
- **Answer Keys:** Daily backups (critical data)
- **Results:** Weekly backups
- **Uploads:** Optional (can be regenerated)

**Backup Commands:**
```bash
# Backup answer keys
cd /data/omr-service
tar -czf answer_keys_backup_$(date +%Y%m%d).tar.gz answer_keys/

# Backup all data
tar -czf omr_full_backup_$(date +%Y%m%d).tar.gz uploads/ results/ answer_keys/
```

### Storage Cleanup

To prevent disk space issues, set up periodic cleanup:

```bash
# Clean uploads older than 30 days
find /data/omr-service/uploads -type f -mtime +30 -delete

# Clean results older than 90 days
find /data/omr-service/results -type f -mtime +90 -delete
```

---

## Health Checks

### Health Check Endpoint

**URL:** `GET /health`

**Response (Healthy):**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-11T10:30:00.123456",
  "model_loaded": true
}
```

**Response (Unhealthy):**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-11-11T10:30:00.123456",
  "model_loaded": false,
  "error": "Model file not found"
}
```

### Monitoring Health

**Via Coolify:**
- Automatic health checks every 30 seconds
- Dashboard shows health status
- Automatic restart on consecutive failures

**Via Command Line:**
```bash
curl https://your-omr-service.com/health
```

**Via External Monitoring:**
- Use UptimeRobot, Pingdom, or similar
- Monitor `/health` endpoint
- Alert on non-200 responses

---

## SSL/HTTPS Setup

### Option 1: Let's Encrypt (Automatic)

1. **In Coolify Dashboard:**
   - Go to Application → **Domains**
   - Add your domain name
   - Enable **HTTPS**
   - Enable **Force HTTPS** (redirect HTTP to HTTPS)
   - Enter **Let's Encrypt Email**
   - Save settings

2. **Coolify will automatically:**
   - Issue SSL certificate
   - Renew certificate before expiry
   - Configure HTTPS redirect

### Option 2: Custom SSL Certificate

1. **Prepare Certificate Files:**
   - SSL Certificate (`.crt` or `.pem`)
   - Private Key (`.key`)
   - CA Bundle (optional)

2. **In Coolify:**
   - Go to Application → **SSL**
   - Upload certificate files
   - Save configuration

### DNS Configuration

Point your domain to Coolify server:

```
A Record:
  Name: omr (or @)
  Value: <coolify-server-ip>
  TTL: 3600

CNAME (Alternative):
  Name: omr
  Value: coolify.yourdomain.com
  TTL: 3600
```

---

## Scaling

### Horizontal Scaling

The OMR Service is stateless and can be horizontally scaled:

1. **In Coolify:**
   - Go to Application → **Scale**
   - Set **Replicas:** 2 or more
   - Coolify will:
     - Create multiple container instances
     - Configure load balancing automatically
     - Distribute requests across instances

2. **Load Balancing:**
   - Coolify uses built-in Traefik load balancer
   - Round-robin distribution by default
   - Automatic health-based routing

3. **Session Affinity:**
   - Not required (service is stateless)
   - Each request is independent

### Vertical Scaling

Increase resources for single instance:

1. **In Coolify:**
   - Go to Application → **Resources**
   - Increase memory limit (e.g., 4 GB → 8 GB)
   - Increase CPU limit (e.g., 2 cores → 4 cores)
   - Redeploy application

### Auto-Scaling (Advanced)

For production workloads, consider:
- CPU-based auto-scaling (scale when CPU > 70%)
- Memory-based auto-scaling
- Queue-based scaling (if implementing job queue)

---

## Monitoring

### Application Logs

**View Logs in Coolify:**
1. Go to Application → **Logs**
2. Select log type:
   - **Build Logs:** Deployment and build process
   - **Application Logs:** Runtime logs from FastAPI
3. Filter by timestamp or search keywords

**Log Levels:**
- `INFO`: Normal operations, requests
- `WARNING`: Non-critical issues
- `ERROR`: Errors requiring attention
- `DEBUG`: Detailed debugging (when DEBUG=True)

### Metrics to Monitor

**System Metrics:**
- CPU usage (should stay below 70%)
- Memory usage (should stay below 80% of limit)
- Disk usage (for persistent volumes)
- Network I/O

**Application Metrics:**
- Request count
- Response times
- Error rates (5xx responses)
- Processing times per image

**Business Metrics:**
- Images processed per day
- Grading operations
- Answer keys created
- Storage usage trends

### External Monitoring Tools

**Recommended:**
- **Uptime Monitoring:** UptimeRobot, Pingdom
- **APM:** New Relic, Datadog (if budget allows)
- **Logs:** Papertrail, Logtail
- **Alerts:** PagerDuty, Opsgenie

---

## Troubleshooting

### Common Issues

#### 1. Container Fails to Start

**Symptoms:**
- Container exits immediately
- Health check never passes

**Diagnosis:**
```bash
# Check logs
docker logs <container-id>

# Check if port is already in use
netstat -tulpn | grep 8000
```

**Solutions:**
- Check environment variables are set correctly
- Verify MODEL_PATH points to existing file
- Ensure required directories exist
- Check for port conflicts

#### 2. Model Not Loading

**Symptoms:**
- Health check returns `model_loaded: false`
- 500 errors on processing endpoints

**Diagnosis:**
```bash
# Check if model file exists
docker exec <container-id> ls -la /app/models/epoch20.pt

# Check file size
docker exec <container-id> du -h /app/models/epoch20.pt
```

**Solutions:**
- Verify `models/epoch20.pt` exists in repository (67.3 MB)
- Check `MODEL_PATH` environment variable
- Ensure model file wasn't corrupted during clone
- Check file permissions

#### 3. High Memory Usage

**Symptoms:**
- Container using > 4 GB RAM
- Out of memory errors
- Container getting killed

**Solutions:**
- Increase memory limit to 6-8 GB
- Enable swap memory
- Reduce concurrent processing
- Implement request queuing

#### 4. Slow Response Times

**Symptoms:**
- Requests taking > 30 seconds
- Timeout errors

**Solutions:**
- Increase CPU allocation
- Scale horizontally (add more instances)
- Optimize image sizes before upload
- Enable caching if applicable

#### 5. Persistent Storage Issues

**Symptoms:**
- Files not persisting across restarts
- Permission errors on file operations

**Solutions:**
- Verify volume mounts are configured correctly
- Check host directory permissions
- Ensure container has write access
- Use named volumes instead of bind mounts

#### 6. SSL/HTTPS Issues

**Symptoms:**
- Certificate errors
- Mixed content warnings

**Solutions:**
- Verify DNS is pointing to correct server
- Check Let's Encrypt email is valid
- Wait for DNS propagation (up to 48 hours)
- Check firewall allows ports 80 and 443

### Debug Mode

Enable debug mode for detailed error messages:

```bash
DEBUG=True
RELOAD=True
```

**Warning:** Do not use debug mode in production!

### Getting Help

1. **Check Application Logs** first
2. **Review Coolify Logs** for deployment issues
3. **GitHub Issues:** Report bugs or ask questions
4. **Coolify Documentation:** https://coolify.io/docs
5. **Coolify Discord:** Join community support

---

## Post-Deployment Testing

### 1. Health Check Test

```bash
curl https://your-omr-service.com/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-11-11T10:30:00.123456",
  "model_loaded": true
}
```

### 2. API Documentation

Visit in browser:
- Swagger UI: `https://your-omr-service.com/docs`
- ReDoc: `https://your-omr-service.com/redoc`

### 3. Process Single Image

```bash
curl -X POST "https://your-omr-service.com/api/v1/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg" \
  -F "debug=true"
```

### 4. Create Answer Key

```bash
curl -X POST "https://your-omr-service.com/api/v1/answer-keys" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_name": "Test Exam",
    "total_questions": 100,
    "answers": ["A", "B", "C", "D", "A", ...],
    "grading_rules": {
      "marks_correct": 1,
      "marks_wrong": 0,
      "marks_unattempted": 0
    }
  }'
```

### 5. List Answer Keys

```bash
curl https://your-omr-service.com/api/v1/answer-keys
```

### 6. Grade Image

```bash
curl -X POST "https://your-omr-service.com/api/v1/grade" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg" \
  -F "answer_key_id=<key-id-from-step-4>"
```

### 7. Performance Test

```bash
# Using Apache Bench
ab -n 100 -c 10 https://your-omr-service.com/health

# Expected: 100% success rate, < 100ms response time
```

---

## Production Checklist

Before going live, verify:

- [ ] SSL/HTTPS is enabled and working
- [ ] CORS_ORIGINS is restricted to specific domains
- [ ] DEBUG and RELOAD are set to False
- [ ] Health checks are passing consistently
- [ ] Persistent volumes are configured and tested
- [ ] Backup strategy is in place
- [ ] Monitoring and alerting is configured
- [ ] Resource limits are appropriate
- [ ] DNS is properly configured
- [ ] API documentation is accessible
- [ ] Test processing with sample images
- [ ] Test answer key creation and grading
- [ ] Review application logs for errors
- [ ] Set up log rotation/retention policy
- [ ] Document any custom configuration
- [ ] Share access with team members

---

## Next Steps

After successful deployment:

1. **Integrate with Frontend:** Use API in your web/mobile app
2. **Set Up Monitoring:** Configure external uptime monitoring
3. **Create Backups:** Schedule regular backups of answer keys
4. **Load Testing:** Test with expected production load
5. **Documentation:** Share API documentation with team
6. **CI/CD:** Set up automatic deployments on git push
7. **Optimize:** Monitor performance and optimize as needed

---

## Support and Resources

- **API Documentation:** `https://your-service.com/docs`
- **Project README:** See `README.md` in repository
- **Deployment Guide:** See `DEPLOYMENT.md` for other platforms
- **Coolify Docs:** https://coolify.io/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **GitHub Issues:** Report issues or request features

---

**Deployment Date:** 2024-11-11
**Guide Version:** 1.0.0
**Service Version:** 1.0.0


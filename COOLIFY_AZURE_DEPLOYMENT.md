# OMR Service - Coolify Deployment on Azure VM

Step-by-step guide to deploy OMR Service to your existing Coolify instance on Azure VM.

## Prerequisites Check

- ✅ Coolify installed and running on Azure VM
- ✅ Access to Coolify dashboard
- ✅ Code pushed to Git repository (GitHub/GitLab)
- ✅ Azure VM has minimum 4GB RAM, 2 CPU cores

---

## Deployment Steps

### Step 1: Access Your Coolify Dashboard

1. Open browser and go to your Coolify URL:
   ```
   http://<your-azure-vm-ip>:8000
   ```
   Or if you've set up a domain:
   ```
   https://coolify.yourdomain.com
   ```

2. Login with your credentials

### Step 2: Create New Application

1. In Coolify Dashboard:
   - Click on **Projects** (left sidebar)
   - Select existing project or click **+ New Project**
   - Click **+ New** → **Application**

2. Choose deployment source:
   - Select **Public Repository** (if GitHub repo is public)
   - Or **Private Repository** (if private - you'll need to add deploy key)

### Step 3: Configure Git Repository

1. **Repository Configuration:**
   ```
   Repository URL: https://github.com/yourusername/OMR_Service.git
   Branch: main
   ```

2. **For Private Repository:**
   - Coolify will show you an SSH public key
   - Go to your GitHub → Settings → Deploy Keys
   - Add Coolify's public key
   - Give it read access

3. Click **Continue**

### Step 4: Build Configuration

1. **Build Pack:** Select **Dockerfile**
   - Coolify will auto-detect the Dockerfile

2. **Port Configuration:**
   ```
   Port: 8000
   ```

3. **Health Check:**
   ```
   Path: /health
   Interval: 30s
   Timeout: 10s
   Retries: 3
   ```

4. Click **Continue**

### Step 5: Set Environment Variables

Click **Environment Variables** and add these:

**Required:**
```bash
HOST=0.0.0.0
PORT=8000
MODEL_PATH=/app/models/epoch20.pt
UPLOAD_DIR=/app/uploads
RESULTS_DIR=/app/results
ANSWER_KEYS_DIR=/app/answer_keys
```

**Production Settings:**
```bash
DEBUG=False
RELOAD=False
CORS_ORIGINS=*
MAX_UPLOAD_SIZE=10485760
```

**Important:** Mark all variables as **Runtime** (not Build Time)

### Step 6: Configure Persistent Storage

Click **Storage** / **Volumes** and add these three volumes:

**Volume 1: Uploads**
```
Name: uploads
Source: /var/lib/coolify/applications/omr-service/uploads
Destination: /app/uploads
Mode: rw (read-write)
```

**Volume 2: Results**
```
Name: results
Source: /var/lib/coolify/applications/omr-service/results
Destination: /app/results
Mode: rw
```

**Volume 3: Answer Keys**
```
Name: answer_keys
Source: /var/lib/coolify/applications/omr-service/answer_keys
Destination: /app/answer_keys
Mode: rw
```

### Step 7: Set Resource Limits

Click **Resources** and configure:

```
Memory Reservation: 2048 MB (2 GB)
Memory Limit: 4096 MB (4 GB)
CPU Reservation: 1.0
CPU Limit: 2.0
```

### Step 8: Configure Domain (Optional)

1. Click **Domains**
2. Add your domain:
   ```
   omr.yourdomain.com
   ```

3. **Enable SSL/HTTPS:**
   - Toggle **HTTPS** to ON
   - Toggle **Force HTTPS** to ON
   - Enter **Let's Encrypt Email**

4. **Update Azure VM Firewall:**
   - Open ports 80 and 443 in Azure NSG
   - Point your domain's DNS to Azure VM IP

### Step 9: Deployment Settings

Click **Deployment** and configure:

```
Restart Policy: unless-stopped
Auto Deploy on Push: ON (optional - for auto-deploy on git push)
```

### Step 10: Deploy!

1. Click **Deploy** button (top right)

2. **Watch Build Logs:**
   - Building Docker image (5-10 minutes first time)
   - Installing dependencies
   - Starting container
   - Health check validation

3. **Wait for Status:**
   - Status should change from "Building" → "Running"
   - Health check should pass (green checkmark)

---

## Post-Deployment Verification

### 1. Check Application Status

In Coolify dashboard:
- Status should show **Running** (green)
- Health check should show **Healthy**
- Logs should show: `Application startup complete`

### 2. Test Health Endpoint

From your local machine or Azure VM:

```bash
# If using domain
curl https://omr.yourdomain.com/health

# If using IP directly
curl http://<azure-vm-ip>:8000/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-11-11T...",
  "model_loaded": true
}
```

### 3. Access API Documentation

Open in browser:
```
https://omr.yourdomain.com/docs
```

You should see Swagger UI with all API endpoints.

### 4. Test Image Processing

```bash
# Upload a test OMR image
curl -X POST "https://omr.yourdomain.com/api/v1/process" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg" \
  -F "debug=true"
```

---

## Troubleshooting

### Issue 1: Build Fails

**Check Build Logs in Coolify:**
- Look for error messages
- Common issues: missing dependencies, wrong Dockerfile path

**Solution:**
```bash
# SSH into Azure VM
ssh user@<azure-vm-ip>

# Check Docker logs
docker logs <container-name>

# Check if model file is present
docker exec <container-name> ls -la /app/models/
```

### Issue 2: Container Keeps Restarting

**Check Health Status:**
- Model file might be missing
- Environment variables might be wrong

**Solution:**
```bash
# Check container logs
docker logs <container-name> --tail 100

# Verify environment variables
docker exec <container-name> env | grep MODEL_PATH
```

### Issue 3: Cannot Access from Outside

**Azure Network Security Group:**

1. Go to Azure Portal
2. Navigate to your VM → Networking
3. Add Inbound Port Rules:
   ```
   Port 80: HTTP (if not using SSL)
   Port 443: HTTPS (for SSL)
   Port 8000: Application (for direct access)
   ```

### Issue 4: Model Not Loading

**Check model file:**
```bash
# SSH into Azure VM
docker exec <container-name> ls -lh /app/models/epoch20.pt

# Should show: 67.3 MB file
```

If missing, the model wasn't included in Docker build. Check:
- Model file is in repository
- `.gitignore` doesn't exclude `models/epoch20.pt`

### Issue 5: Out of Memory

**Azure VM Resources:**
- Check if VM has enough RAM (minimum 4 GB)
- Upgrade VM size if needed:
  - Recommended: Standard_B2s or higher
  - RAM: 4-8 GB
  - CPU: 2-4 cores

**In Coolify:**
- Increase memory limit to 6-8 GB
- Reduce concurrent requests

---

## Azure VM Optimization

### 1. Enable Swap (if RAM < 8 GB)

```bash
# SSH into Azure VM
ssh user@<azure-vm-ip>

# Create swap file (4 GB)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Monitor Resources

```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check Docker containers
docker stats
```

### 3. Set Up Backups

**Backup Answer Keys (Critical):**
```bash
# Create backup script
cat > /home/user/backup-omr.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup answer keys
cd /var/lib/coolify/applications/omr-service/
tar -czf $BACKUP_DIR/answer_keys_$DATE.tar.gz answer_keys/

# Keep only last 7 days
find $BACKUP_DIR -name "answer_keys_*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /home/user/backup-omr.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add line:
0 2 * * * /home/user/backup-omr.sh >> /home/user/backup.log 2>&1
```

---

## DNS Configuration (If Using Domain)

### Update DNS Records

In your domain registrar (GoDaddy, Namecheap, etc.):

```
Type: A
Name: omr (or @)
Value: <your-azure-vm-public-ip>
TTL: 3600
```

### Wait for DNS Propagation

```bash
# Check DNS propagation
nslookup omr.yourdomain.com

# Or use online tool
# https://www.whatsmydns.net/
```

---

## Monitoring Setup

### 1. Uptime Monitoring

Use external service:
- **UptimeRobot** (free): https://uptimerobot.com
- Monitor: `https://omr.yourdomain.com/health`
- Alert on downtime

### 2. Log Monitoring

**View logs in Coolify:**
- Go to Application → Logs
- Filter by error level
- Download logs if needed

**View logs via SSH:**
```bash
# Real-time logs
docker logs -f <container-name>

# Last 100 lines
docker logs --tail 100 <container-name>

# Search for errors
docker logs <container-name> 2>&1 | grep ERROR
```

### 3. Performance Monitoring

```bash
# Monitor container stats
docker stats <container-name>

# Check API response time
curl -w "@curl-format.txt" -o /dev/null -s https://omr.yourdomain.com/health

# Create curl-format.txt
cat > curl-format.txt << 'EOF'
time_total: %{time_total}s
EOF
```

---

## Scaling (When Needed)

### Horizontal Scaling in Coolify

1. Go to Application → **Scale**
2. Set **Replicas: 2** (or more)
3. Coolify will:
   - Create multiple containers
   - Load balance automatically
   - Route to healthy instances only

### Vertical Scaling (Azure VM)

If need more resources:

1. **In Azure Portal:**
   - Stop VM
   - Change VM size (e.g., Standard_B2s → Standard_B4ms)
   - Start VM

2. **Update Coolify limits:**
   - Increase memory/CPU limits
   - Redeploy application

---

## Security Best Practices

### 1. Restrict CORS in Production

Update environment variable:
```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### 2. Enable Firewall

```bash
# On Azure VM
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Coolify (optional)
```

### 3. Regular Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Coolify (when new version available)
# Follow Coolify upgrade docs
```

### 4. API Rate Limiting

Consider adding rate limiting:
- Use Nginx reverse proxy
- Or implement in FastAPI with slowapi

---

## Quick Command Reference

```bash
# SSH to Azure VM
ssh user@<azure-vm-ip>

# View all containers
docker ps -a

# View OMR service logs
docker logs -f omr-microservice

# Restart container (via Coolify or manually)
docker restart omr-microservice

# Check health
curl http://localhost:8000/health

# Check disk usage
df -h /var/lib/coolify/

# Check memory
free -h

# Clean up old images/containers
docker system prune -a
```

---

## Support

**If you face issues:**

1. Check Coolify logs first
2. Check application logs
3. Verify environment variables
4. Check persistent volumes
5. Verify Azure VM resources

**Resources:**
- Coolify Docs: https://coolify.io/docs
- API Docs: `https://your-service.com/docs`
- GitHub Issues: Report problems

---

## Deployment Checklist

- [ ] Coolify dashboard accessible
- [ ] Git repository connected
- [ ] Environment variables configured
- [ ] Persistent volumes created
- [ ] Resource limits set
- [ ] Health check configured
- [ ] Application deployed successfully
- [ ] Health endpoint returns healthy
- [ ] API docs accessible
- [ ] Test image processing works
- [ ] SSL/HTTPS configured (if using domain)
- [ ] Azure firewall/NSG rules updated
- [ ] DNS configured (if using domain)
- [ ] Monitoring set up
- [ ] Backup script configured
- [ ] CORS restricted for production
- [ ] Logs reviewed for errors

---

**Last Updated:** 2024-11-11
**Service Version:** 1.0.0


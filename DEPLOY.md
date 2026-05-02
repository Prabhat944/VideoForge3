# VideoForge3 - Complete Deployment Guide

**Last Updated:** May 2026  
**Version:** 2.0  
**Author:** VideoForge Team

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [EC2 Production Deployment](#ec2-production-deployment)
5. [Third-Party Integrations Setup](#third-party-integrations-setup)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Required Files & Configuration](#required-files--configuration)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Overview

**VideoForge3** is an AI-powered video generation platform that creates YouTube-ready videos with:
- AI script generation (OpenAI GPT-4o-mini)
- Voice synthesis (OpenAI TTS / ElevenLabs)
- Thumbnail generation (DALL-E 3)
- Scene image generation (DALL-E 3)
- Video rendering with FFmpeg
- YouTube upload integration
- Content trending analysis (Reddit, YouTube)

### Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- MongoDB (Database)
- AWS S3 (Media storage)
- FFmpeg (Video rendering)

**Frontend:**
- React 19
- Tailwind CSS
- Radix UI components
- React Router v7

**Infrastructure:**
- Kubernetes (Container orchestration)
- Nginx (Reverse proxy)
- Supervisor (Process management)

---

## Prerequisites

### Required Software

**For Local Development:**
- Python 3.11+
- Node.js 20+
- MongoDB 6.0+
- FFmpeg 5.0+
- Yarn package manager
- Git

**For EC2/Production:**
- Ubuntu 22.04 LTS (recommended)
- Docker & Docker Compose (optional)
- Nginx
- SSL certificates (Let's Encrypt recommended)

### Required Accounts & API Keys

1. **OpenAI** - https://platform.openai.com
   - API Key (for GPT, DALL-E, TTS)
   - $10+ credit recommended

2. **AWS** - https://aws.amazon.com
   - S3 bucket for media storage
   - IAM user with S3 permissions
   - Access Key ID & Secret Key

3. **Google Cloud** - https://console.cloud.google.com
   - OAuth Client for YouTube integration
   - Enable YouTube Data API v3
   - Client ID & Client Secret

4. **ElevenLabs** (Optional) - https://elevenlabs.io
   - API Key for voice synthesis
   - Alternative to OpenAI TTS

5. **Stripe** - https://stripe.com
   - Test API Key for payments
   - Webhook secret

6. **Reddit** (Optional) - https://www.reddit.com/prefs/apps
   - Client ID & Client Secret
   - For trending content analysis

7. **MongoDB** - Local or Atlas
   - Atlas: https://www.mongodb.com/cloud/atlas
   - Connection string

---

## Local Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/VideoForge3.git
cd VideoForge3
```

### Step 2: Backend Setup

#### 2.1 Install Python Dependencies

```bash
cd backend

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2.2 Create Backend .env File

Create `/backend/.env`:

```bash
# Database Configuration
MONGO_URL="mongodb://localhost:27017"
DB_NAME="videoforge_dev"

# CORS Configuration
CORS_ORIGINS="http://localhost:3000"

# JWT Authentication
JWT_SECRET="your-super-secret-jwt-key-change-this"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES="10080"  # 7 days

# OpenAI API (Required)
EMERGENT_LLM_KEY="sk-proj-YOUR_OPENAI_API_KEY_HERE"

# Voice Synthesis
ELEVENLABS_API_KEY="your-elevenlabs-key-optional"

# Payment Integration
STRIPE_API_KEY="sk_test_YOUR_STRIPE_TEST_KEY"

# Google OAuth (YouTube Integration)
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
APP_BASE_URL="http://localhost:8001"
GOOGLE_REDIRECT_URI="http://localhost:8001/api/youtube/callback"

# Reddit API (Optional - for trending analysis)
REDDIT_CLIENT_ID=""
REDDIT_CLIENT_SECRET=""
REDDIT_USER_AGENT="VideoForge/1.0 by VideoForgeBot"

# Media Storage
RENDER_DIR="/app/backend/renders"

# AWS S3 Storage (Optional for local, Required for production)
AWS_S3_BUCKET=""
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
```

#### 2.3 Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html

#### 2.4 Start MongoDB (Local)

**Ubuntu:**
```bash
sudo systemctl start mongod
sudo systemctl enable mongod
```

**macOS:**
```bash
brew services start mongodb-community
```

**Docker:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:6.0
```

#### 2.5 Run Backend

```bash
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Verify:**
```bash
curl http://localhost:8001/api/
# Should return: {"service":"VideoForge AI","status":"ok"}
```

### Step 3: Frontend Setup

#### 3.1 Install Node Dependencies

```bash
cd ../frontend
yarn install
```

#### 3.2 Create Frontend .env File

Create `/frontend/.env`:

```bash
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Development Settings
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=false
```

#### 3.3 Run Frontend

```bash
yarn start
```

**Access:** http://localhost:3000

### Step 4: Test the Application

1. **Register a user:** http://localhost:3000
2. **Create a project**
3. **Generate script** (tests OpenAI integration)
4. **Generate voice** (tests TTS)
5. **Generate thumbnail** (tests DALL-E)
6. **Generate scenes** (tests image generation)
7. **Render video** (tests FFmpeg + S3)

---

## EC2 Production Deployment

### Step 1: Launch EC2 Instance

**Recommended Instance:**
- Instance Type: t3.large or t3.xlarge
- OS: Ubuntu 22.04 LTS
- Storage: 100 GB SSD
- Security Group:
  - Port 22 (SSH)
  - Port 80 (HTTP)
  - Port 443 (HTTPS)
  - Port 8001 (Backend - optional, can be internal)

### Step 2: Initial Server Setup

```bash
# SSH into your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install essential packages
sudo apt-get install -y git curl wget build-essential python3-pip python3-venv nodejs npm ffmpeg nginx certbot python3-certbot-nginx supervisor
```

### Step 3: Install Node.js 20 & Yarn

```bash
# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Yarn
npm install -g yarn
```

### Step 4: Install MongoDB

**Option A: Install Locally on EC2**

```bash
# Import MongoDB public GPG key
curl -fsSL https://www.mongodb.org/static/pgp/server-6.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

**Option B: Use MongoDB Atlas (Recommended)**

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free cluster
3. Get connection string
4. Update `MONGO_URL` in `.env`

### Step 5: Clone and Setup Application

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/VideoForge3.git
cd VideoForge3

# Set permissions
sudo chown -R ubuntu:ubuntu /opt/VideoForge3
```

### Step 6: Setup Backend on EC2

```bash
cd /opt/VideoForge3/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production .env file
nano .env
```

**Production Backend .env:**

```bash
# Database
MONGO_URL="mongodb://localhost:27017"  # Or Atlas connection string
DB_NAME="videoforge_production"

# CORS
CORS_ORIGINS="https://yourdomain.com"

# JWT
JWT_SECRET="production-super-secret-change-this-to-random-string"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES="10080"

# OpenAI
EMERGENT_LLM_KEY="sk-svcacct-YOUR_PRODUCTION_KEY_HERE"

# ElevenLabs
ELEVENLABS_API_KEY="your-elevenlabs-production-key"

# Stripe
STRIPE_API_KEY="sk_live_YOUR_PRODUCTION_STRIPE_KEY"

# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
APP_BASE_URL="https://yourdomain.com"
GOOGLE_REDIRECT_URI="https://yourdomain.com/api/youtube/callback"

# Reddit
REDDIT_CLIENT_ID="your-reddit-client-id"
REDDIT_CLIENT_SECRET="your-reddit-client-secret"
REDDIT_USER_AGENT="VideoForge/1.0 by VideoForgeBot"

# Media Storage
RENDER_DIR="/opt/VideoForge3/backend/renders"

# AWS S3 (REQUIRED for production)
AWS_S3_BUCKET="your-videoforge-media-bucket"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="your-secret-key"
```

### Step 7: Setup Frontend on EC2

```bash
cd /opt/VideoForge3/frontend

# Install dependencies
yarn install

# Create production .env
nano .env
```

**Production Frontend .env:**

```bash
REACT_APP_BACKEND_URL=https://yourdomain.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

```bash
# Build production bundle
yarn build
```

### Step 8: Setup Supervisor (Process Management)

Create `/etc/supervisor/conf.d/videoforge.conf`:

```bash
sudo nano /etc/supervisor/conf.d/videoforge.conf
```

```ini
[program:backend]
command=/opt/VideoForge3/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
directory=/opt/VideoForge3/backend
user=ubuntu
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/videoforge/backend.log
stderr_logfile=/var/log/videoforge/backend.err.log
environment=PATH="/opt/VideoForge3/backend/venv/bin"

[program:mongodb]
command=/usr/bin/mongod --config /etc/mongod.conf
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/videoforge/mongodb.log
stderr_logfile=/var/log/videoforge/mongodb.err.log
```

```bash
# Create log directory
sudo mkdir -p /var/log/videoforge

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Check status
sudo supervisorctl status
```

### Step 9: Setup Nginx

```bash
sudo nano /etc/nginx/sites-available/videoforge
```

```nginx
# Frontend server
server {
    listen 80;
    server_name yourdomain.com;

    root /opt/VideoForge3/frontend/build;
    index index.html;

    # Frontend routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for video rendering
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/videoforge /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 10: Setup SSL with Let's Encrypt

```bash
# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 11: Verify Production Deployment

```bash
# Check backend
curl https://yourdomain.com/api/

# Check frontend
curl https://yourdomain.com/

# Check supervisor processes
sudo supervisorctl status
```

---

## Third-Party Integrations Setup

### 1. OpenAI Setup

**Step 1:** Create account at https://platform.openai.com

**Step 2:** Generate API Key
- Go to API Keys section
- Create new secret key
- Copy and save securely

**Step 3:** Add billing
- Go to Settings → Billing
- Add payment method
- Add $10+ credit

**Step 4:** Update .env
```bash
EMERGENT_LLM_KEY="sk-proj-YOUR_KEY_HERE"
```

**Models Used:**
- `gpt-4o-mini` - Script generation
- `dall-e-3` (gpt-image-1) - Thumbnail & scenes
- `tts-1` / `tts-1-hd` - Voice synthesis

---

### 2. AWS S3 Setup

**Step 1:** Create S3 Bucket

```bash
aws s3 mb s3://your-videoforge-media --region us-east-1
```

Or via AWS Console:
1. Go to S3 service
2. Create bucket
3. Name: `your-videoforge-media`
4. Region: `us-east-1`
5. Block all public access: ✅ Enabled
6. Encryption: ✅ Enable SSE-S3

**Step 2:** Create IAM User

1. Go to IAM → Users → Create user
2. User name: `videoforge-s3-user`
3. Access type: Programmatic access
4. Create and download credentials

**Step 3:** Create IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-videoforge-media",
        "arn:aws:s3:::your-videoforge-media/*"
      ]
    }
  ]
}
```

**Step 4:** Attach Policy to User

1. Go to IAM → Policies → Create policy
2. Paste JSON above
3. Name: `VideoForgeS3Access`
4. Attach to `videoforge-s3-user`

**Step 5:** Update .env

```bash
AWS_S3_BUCKET="your-videoforge-media"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="your-secret-key"
```

---

### 3. Google OAuth (YouTube) Setup

**Step 1:** Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Create new project: "VideoForge"
3. Enable APIs: YouTube Data API v3

**Step 2:** Create OAuth Credentials

1. Go to APIs & Services → Credentials
2. Create OAuth 2.0 Client ID
3. Application type: Web application
4. Authorized redirect URIs:
   - Local: `http://localhost:8001/api/youtube/callback`
   - Production: `https://yourdomain.com/api/youtube/callback`
5. Copy Client ID & Client Secret

**Step 3:** Configure OAuth Consent Screen

1. Go to OAuth consent screen
2. User Type: External
3. Add scopes:
   - `https://www.googleapis.com/auth/youtube.upload`
   - `https://www.googleapis.com/auth/youtube.readonly`

**Step 4:** Update .env

```bash
GOOGLE_CLIENT_ID="123456789-abc.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="GOCSPX-abc123"
APP_BASE_URL="https://yourdomain.com"
GOOGLE_REDIRECT_URI="https://yourdomain.com/api/youtube/callback"
```

---

### 4. Stripe Setup

**Step 1:** Create account at https://stripe.com

**Step 2:** Get API Keys

1. Go to Developers → API keys
2. Copy Test keys for development
3. Copy Live keys for production

**Step 3:** Setup Webhooks (Optional)

1. Go to Developers → Webhooks
2. Add endpoint: `https://yourdomain.com/api/stripe/webhook`
3. Select events:
   - `payment_intent.succeeded`
   - `payment_intent.failed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`

**Step 4:** Update .env

```bash
# Development
STRIPE_API_KEY="sk_test_..."

# Production
STRIPE_API_KEY="sk_live_..."
```

---

### 5. ElevenLabs Setup (Optional)

**Step 1:** Create account at https://elevenlabs.io

**Step 2:** Get API Key

1. Go to Profile → API Key
2. Copy key

**Step 3:** Update .env

```bash
ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

**Note:** ElevenLabs may have rate limits from cloud IPs. OpenAI TTS is recommended as primary.

---

### 6. Reddit API Setup (Optional)

**Step 1:** Create Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Create app (script type)
3. Redirect URI: `http://localhost:8080` (unused)

**Step 2:** Get Credentials

- Copy 14-char client ID (under app name)
- Copy secret

**Step 3:** Update .env

```bash
REDDIT_CLIENT_ID="your-14-char-id"
REDDIT_CLIENT_SECRET="your-secret"
REDDIT_USER_AGENT="VideoForge/1.0 by YourUsername"
```

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, or self-hosted)
- kubectl configured
- Docker registry access
- Helm (optional)

### Step 1: Create Docker Images

**Backend Dockerfile** (`/backend/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 8001

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

**Frontend Dockerfile** (`/frontend/Dockerfile`):

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Build and Push Images:**

```bash
# Build backend
docker build -t your-registry/videoforge-backend:latest ./backend
docker push your-registry/videoforge-backend:latest

# Build frontend
docker build -t your-registry/videoforge-frontend:latest ./frontend
docker push your-registry/videoforge-frontend:latest
```

### Step 2: Create Kubernetes Manifests

**ConfigMap** (`k8s/configmap.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: videoforge-config
data:
  CORS_ORIGINS: "*"
  JWT_ALGORITHM: "HS256"
  JWT_EXPIRE_MINUTES: "10080"
  AWS_S3_REGION: "us-east-1"
  APP_BASE_URL: "https://yourdomain.com"
```

**Secrets** (`k8s/secrets.yaml`):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: videoforge-secrets
type: Opaque
stringData:
  MONGO_URL: "mongodb+srv://user:pass@cluster.mongodb.net/videoforge"
  JWT_SECRET: "your-super-secret-jwt-key"
  EMERGENT_LLM_KEY: "sk-svcacct-YOUR_KEY_HERE"
  ELEVENLABS_API_KEY: "your-elevenlabs-key"
  STRIPE_API_KEY: "sk_live_YOUR_KEY"
  GOOGLE_CLIENT_ID: "your-google-client-id"
  GOOGLE_CLIENT_SECRET: "your-google-client-secret"
  AWS_S3_BUCKET: "your-videoforge-media"
  AWS_ACCESS_KEY_ID: "AKIA..."
  AWS_SECRET_ACCESS_KEY: "your-secret-key"
```

**Backend Deployment** (`k8s/backend-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: videoforge-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: videoforge-backend
  template:
    metadata:
      labels:
        app: videoforge-backend
    spec:
      containers:
      - name: backend
        image: your-registry/videoforge-backend:latest
        ports:
        - containerPort: 8001
        envFrom:
        - configMapRef:
            name: videoforge-config
        - secretRef:
            name: videoforge-secrets
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/
            port: 8001
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: videoforge-backend-service
spec:
  selector:
    app: videoforge-backend
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP
```

**Frontend Deployment** (`k8s/frontend-deployment.yaml`):

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: videoforge-frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: videoforge-frontend
  template:
    metadata:
      labels:
        app: videoforge-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/videoforge-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
---
apiVersion: v1
kind: Service
metadata:
  name: videoforge-frontend-service
spec:
  selector:
    app: videoforge-frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

**Ingress** (`k8s/ingress.yaml`):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: videoforge-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    secretName: videoforge-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: videoforge-backend-service
            port:
              number: 8001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: videoforge-frontend-service
            port:
              number: 80
```

### Step 3: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace videoforge

# Apply manifests
kubectl apply -f k8s/configmap.yaml -n videoforge
kubectl apply -f k8s/secrets.yaml -n videoforge
kubectl apply -f k8s/backend-deployment.yaml -n videoforge
kubectl apply -f k8s/frontend-deployment.yaml -n videoforge
kubectl apply -f k8s/ingress.yaml -n videoforge

# Check status
kubectl get pods -n videoforge
kubectl get services -n videoforge
kubectl get ingress -n videoforge
```

### Step 4: Setup Horizontal Pod Autoscaler (Optional)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: videoforge-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: videoforge-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Required Files & Configuration

### Files Typically in .gitignore

These files are required but not in git. Create them manually:

#### 1. Backend .env File

**Location:** `/backend/.env`

**Template:**
```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="videoforge_db"

# CORS
CORS_ORIGINS="*"

# JWT
JWT_SECRET="generate-random-secret-key-here"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES="10080"

# OpenAI
EMERGENT_LLM_KEY="sk-svcacct-YOUR_KEY"

# ElevenLabs
ELEVENLABS_API_KEY="your-key"

# Stripe
STRIPE_API_KEY="sk_test_your_key"

# Google OAuth
GOOGLE_CLIENT_ID="your-id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="your-secret"
APP_BASE_URL="http://localhost:8001"
GOOGLE_REDIRECT_URI="http://localhost:8001/api/youtube/callback"

# Reddit
REDDIT_CLIENT_ID=""
REDDIT_CLIENT_SECRET=""
REDDIT_USER_AGENT="VideoForge/1.0"

# Media
RENDER_DIR="/app/backend/renders"

# AWS S3
AWS_S3_BUCKET="your-bucket"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="your-secret"
```

#### 2. Frontend .env File

**Location:** `/frontend/.env`

**Template:**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=3000
ENABLE_HEALTH_CHECK=false
```

#### 3. Test Credentials File

**Location:** `/memory/test_credentials.md`

```markdown
# Test Credentials

## Test User
- Email: test@videoforge.ai
- Password: TestPass123!

## Admin User
- Email: admin@videoforge.ai
- Password: AdminPass123!
```

#### 4. Supervisor Configuration

**Location:** `/etc/supervisor/conf.d/videoforge.conf`

```ini
[program:backend]
command=/path/to/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
directory=/path/to/backend
user=ubuntu
autostart=true
autorestart=true
stdout_logfile=/var/log/videoforge/backend.log
stderr_logfile=/var/log/videoforge/backend.err.log

[program:mongodb]
command=/usr/bin/mongod --config /etc/mongod.conf
autostart=true
autorestart=true
stdout_logfile=/var/log/videoforge/mongodb.log
```

#### 5. Nginx Configuration

**Location:** `/etc/nginx/sites-available/videoforge`

See EC2 deployment section for full configuration.

---

## Troubleshooting

### Common Issues

#### 1. Budget Exceeded Error

**Error:**
```
AI budget exceeded. Please add balance to your Universal Key
```

**Solution:**
- Check OpenAI account balance
- Verify correct API key in .env
- Restart backend after changing key

#### 2. S3 Upload Fails

**Error:**
```
Failed to upload to S3: Access Denied
```

**Solution:**
- Verify IAM permissions
- Check S3 bucket policy
- Confirm AWS credentials in .env

#### 3. MongoDB Connection Failed

**Error:**
```
ServerSelectionTimeoutError: localhost:27017
```

**Solution:**
- Ensure MongoDB is running: `sudo systemctl status mongod`
- Check MONGO_URL in .env
- Verify network connectivity

#### 4. YouTube OAuth Not Working

**Error:**
```
redirect_uri_mismatch
```

**Solution:**
- Add correct redirect URI in Google Cloud Console
- Update GOOGLE_REDIRECT_URI in .env
- Ensure APP_BASE_URL matches domain

#### 5. Video Rendering Fails

**Error:**
```
FileNotFoundError: voice.mp3
```

**Solution:**
- Check S3 configuration
- Verify media files exist in S3
- Check storage_service.py logs

#### 6. Frontend Not Connecting to Backend

**Error:**
```
Network Error: ERR_CONNECTION_REFUSED
```

**Solution:**
- Verify backend is running: `curl http://localhost:8001/api/`
- Check REACT_APP_BACKEND_URL in frontend .env
- Verify CORS_ORIGINS in backend .env

### Debug Commands

```bash
# Check backend logs
tail -f /var/log/supervisor/backend.log

# Check frontend logs
tail -f /var/log/supervisor/frontend.log

# Check MongoDB status
sudo systemctl status mongod
mongosh --eval "db.adminCommand('ping')"

# Check S3 access
aws s3 ls s3://your-bucket

# Test OpenAI API
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"

# Check supervisor processes
sudo supervisorctl status
```

---

## Monitoring & Maintenance

### Application Monitoring

#### 1. Log Monitoring

```bash
# Backend logs
tail -f /var/log/videoforge/backend.log

# Monitor errors
grep ERROR /var/log/videoforge/backend.err.log

# Monitor API requests
grep "POST /api/" /var/log/videoforge/backend.log
```

#### 2. System Resources

```bash
# CPU & Memory
htop

# Disk usage
df -h

# MongoDB disk usage
du -sh /var/lib/mongodb

# S3 usage
aws s3 ls s3://your-bucket --recursive --summarize
```

#### 3. API Performance

```bash
# Test response time
time curl http://localhost:8001/api/

# Check active connections
netstat -an | grep 8001 | wc -l
```

### Maintenance Tasks

#### Daily

- Monitor error logs
- Check API response times
- Verify S3 uploads

#### Weekly

- Review OpenAI API usage and costs
- Check MongoDB disk usage
- Review failed video renders

#### Monthly

- Update Python dependencies: `pip list --outdated`
- Update Node dependencies: `yarn outdated`
- Review and optimize S3 storage costs
- Rotate API keys if needed

### Backup Strategy

#### Database Backups

```bash
# MongoDB backup
mongodump --out /backups/mongodb-$(date +%Y%m%d)

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups/mongodb"
DATE=$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
mongodump --out $BACKUP_DIR/$DATE
# Keep last 7 days
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} \;
```

Add to crontab:
```bash
0 2 * * * /path/to/backup-script.sh
```

#### S3 Versioning

Enable versioning on S3 bucket for automatic backup:

```bash
aws s3api put-bucket-versioning \
  --bucket your-bucket \
  --versioning-configuration Status=Enabled
```

---

## Security Best Practices

### 1. Environment Variables

- Never commit .env files to git
- Use different keys for dev/staging/production
- Rotate API keys every 90 days

### 2. Database Security

- Use strong MongoDB passwords
- Enable MongoDB authentication
- Restrict MongoDB network access
- Regular backups

### 3. API Security

- Use HTTPS in production
- Implement rate limiting
- Validate all user inputs
- Keep dependencies updated

### 4. AWS Security

- Use IAM roles with minimal permissions
- Enable S3 encryption
- Monitor CloudWatch for suspicious activity
- Enable MFA on AWS account

---

## Performance Optimization

### Backend Optimization

```python
# Use async operations
async def generate_script(...):
    async with httpx.AsyncClient() as client:
        response = await client.post(...)

# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
def get_voice_configs():
    return db.voices.find({}).to_list(100)

# Use connection pooling
motor_client = AsyncIOMotorClient(
    MONGO_URL,
    maxPoolSize=50,
    minPoolSize=10
)
```

### Frontend Optimization

```javascript
// Code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Wizard = lazy(() => import('./pages/Wizard'));

// Image optimization
<img 
  src={thumbnail} 
  loading="lazy" 
  alt="Thumbnail"
/>

// Memoization
const MemoizedComponent = React.memo(ExpensiveComponent);
```

### Database Optimization

```javascript
// Create indexes
db.projects.createIndex({ user_id: 1, created_at: -1 });
db.projects.createIndex({ status: 1 });
db.users.createIndex({ email: 1 }, { unique: true });

// Use projections
db.projects.find(
  { user_id: userId },
  { title: 1, status: 1, created_at: 1 }
);
```

---

## Support & Resources

### Documentation

- FastAPI: https://fastapi.tiangolo.com
- React: https://react.dev
- MongoDB: https://docs.mongodb.com
- AWS S3: https://docs.aws.amazon.com/s3

### API Documentation

- OpenAI: https://platform.openai.com/docs
- ElevenLabs: https://docs.elevenlabs.io
- YouTube API: https://developers.google.com/youtube/v3
- Stripe: https://stripe.com/docs/api

### Community

- GitHub Issues: https://github.com/YOUR_USERNAME/VideoForge3/issues
- Discord: [Your Discord Link]
- Email: support@videoforge.ai

---

## License

MIT License - See LICENSE file for details

---

## Contributors

- [Your Name] - Initial work
- [Contributors] - See CONTRIBUTORS.md

---

**Last Updated:** May 2, 2026  
**Version:** 2.0.0  
**Maintained by:** VideoForge Team

For questions or issues, please open a GitHub issue or contact support@videoforge.ai

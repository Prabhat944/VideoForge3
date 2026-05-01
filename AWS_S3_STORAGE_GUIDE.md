# AWS S3 Storage Implementation Guide

## Overview

VideoForge3 now supports **AWS S3** for persistent media storage in production Kubernetes deployments. This solves the ephemeral filesystem issue in containerized environments.

---

## Storage Strategy

### Development (Local):
- Uses local filesystem: `/app/backend/media/`
- Fast, no AWS costs
- S3 configuration not required

### Production (Kubernetes + S3):
- **Primary**: AWS S3 bucket (persistent, scalable)
- **Cache**: Local filesystem (ephemeral, fast access)
- **Fallback**: MongoDB base64 (for renders when files unavailable)

---

## How It Works

### 1. **File Upload Strategy** (Dual Storage)

When a media file is generated:
```python
# Example: Voice generation
voice_bytes = generate_voice(...)

# 1. Upload to S3 (if configured)
if USE_S3:
    s3.put_object(Bucket=bucket, Key="media/voices/project-id/voice.mp3", Body=voice_bytes)

# 2. Save to local filesystem (cache/development)
local_path.write_bytes(voice_bytes)

# 3. Store base64 in MongoDB (ultimate fallback for renders)
db.projects.update({"audio_b64": base64.b64encode(voice_bytes)})
```

### 2. **File Read Strategy** (Cascading Fallback)

When a file is needed for rendering:
```python
def read_bytes(rel_path):
    # 1. Try S3 first (if configured) - PRODUCTION PRIMARY
    if USE_S3:
        try:
            return s3.get_object(Bucket=bucket, Key=key)['Body'].read()
        except:
            pass
    
    # 2. Try local filesystem - CACHE/DEVELOPMENT
    if local_path.exists():
        return local_path.read_bytes()
    
    # 3. FileNotFoundError raised
    # Pipeline code then falls back to MongoDB base64
    raise FileNotFoundError(rel_path)
```

---

## Configuration

### Environment Variables

Add to `/app/backend/.env`:

```bash
# AWS S3 Storage (Optional - for production)
AWS_S3_BUCKET="your-bucket-name"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."
```

### Configuration Detection

```python
USE_S3 = bool(AWS_S3_BUCKET and AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)

if USE_S3:
    # S3 storage enabled
    logging.info(f"S3 storage enabled: bucket={AWS_S3_BUCKET}")
else:
    # Local filesystem only
    logging.info("S3 not configured, using local filesystem")
```

---

## AWS S3 Setup

### Step 1: Create S3 Bucket

```bash
# Via AWS CLI
aws s3 mb s3://videoforge-media-prod --region us-east-1

# Via AWS Console
# 1. Go to S3 → Create bucket
# 2. Name: videoforge-media-prod
# 3. Region: us-east-1 (or your preferred region)
# 4. Block public access: ENABLED (recommended)
# 5. Versioning: Optional
# 6. Encryption: Optional (recommended: SSE-S3)
```

### Step 2: Create IAM User

```bash
# 1. Go to IAM → Users → Add user
# 2. Name: videoforge-app-user
# 3. Access type: Programmatic access
# 4. Create and download credentials
```

### Step 3: Attach IAM Policy

Create custom policy or use this:

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
        "arn:aws:s3:::videoforge-media-prod",
        "arn:aws:s3:::videoforge-media-prod/*"
      ]
    }
  ]
}
```

Attach to `videoforge-app-user`.

### Step 4: Configure Application

Add to backend `.env`:

```bash
AWS_S3_BUCKET="videoforge-media-prod"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."
```

---

## S3 Bucket Structure

```
videoforge-media-prod/
├── media/
│   ├── voices/
│   │   └── {project-id}/
│   │       └── voice.mp3
│   ├── thumbnails/
│   │   └── {project-id}/
│   │       └── thumb.png
│   └── scenes/
│       └── {project-id}/
│           ├── scene_0.png
│           ├── scene_1.png
│           └── ...
```

---

## Code Changes

### Modified File: `/app/backend/storage_service.py`

**Key Functions:**

#### 1. Upload Functions
```python
def save_voice(project_id: str, audio_bytes: bytes) -> str:
    rel_path = f"voices/{project_id}/voice.mp3"
    
    # Upload to S3 if configured
    if USE_S3:
        _upload_to_s3(rel_path, audio_bytes, "audio/mpeg")
    
    # Also save locally (cache)
    local_path.write_bytes(audio_bytes)
    
    return rel_path
```

#### 2. Download Functions
```python
def read_bytes(rel_path: str) -> bytes:
    # Try S3 first
    if USE_S3:
        s3_bytes = _download_from_s3(rel_path)
        if s3_bytes:
            return s3_bytes
    
    # Fall back to local filesystem
    if local_path.exists():
        return local_path.read_bytes()
    
    # Not found
    raise FileNotFoundError(rel_path)
```

#### 3. Cleanup Functions
```python
def cleanup_project(project_id: str):
    # Delete from S3
    if USE_S3:
        s3.delete_objects(prefix=f"media/.../{{project_id}}/")
    
    # Delete from local filesystem
    shutil.rmtree(local_dir, ignore_errors=True)
```

---

## Deployment Workflow

### Local Development

```bash
# .env (no S3 configuration)
AWS_S3_BUCKET=""

# Storage behavior:
# - Saves to /app/backend/media/
# - Reads from /app/backend/media/
# - No S3 access needed
```

### Production Deployment

```bash
# .env (with S3 configuration)
AWS_S3_BUCKET="videoforge-media-prod"
AWS_S3_REGION="us-east-1"
AWS_ACCESS_KEY_ID="AKIA..."
AWS_SECRET_ACCESS_KEY="..."

# Storage behavior:
# - Saves to S3 + local cache
# - Reads from S3 first, then local cache
# - Files persist across container restarts
```

---

## Benefits

### ✅ **Production Ready**
- Persistent storage in stateless containers
- No data loss on container restart/redeploy

### ✅ **Scalable**
- S3 handles unlimited file storage
- No MongoDB document size limits (16MB BSON limit)

### ✅ **Performance**
- Local filesystem cache for fast reads
- S3 as persistent backend

### ✅ **Cost Effective**
- S3 storage: ~$0.023/GB/month
- No need for persistent volumes in Kubernetes

### ✅ **Backwards Compatible**
- Works without S3 (local filesystem)
- Graceful fallback to MongoDB base64 if file missing

### ✅ **CDN Ready**
- Can add CloudFront CDN in front of S3
- Fast global media delivery

---

## Monitoring

### Check S3 Usage

```bash
# List files
aws s3 ls s3://videoforge-media-prod/media/ --recursive

# Get bucket size
aws s3 ls s3://videoforge-media-prod --recursive --summarize
```

### Check Application Logs

```bash
# Look for S3 initialization
grep "S3 storage" /var/log/supervisor/backend.out.log

# Look for S3 operations
grep "Uploaded to S3\|Downloaded from S3" /var/log/supervisor/backend.out.log
```

---

## Cost Estimation

### Example Project:
- Voice: 100 KB
- Thumbnail: 200 KB
- 6 Scenes: 6 × 200 KB = 1.2 MB
- **Total per project: ~1.5 MB**

### S3 Costs:
- Storage: $0.023/GB/month
- 1,000 projects = 1.5 GB = **$0.03/month**
- 10,000 projects = 15 GB = **$0.35/month**
- 100,000 projects = 150 GB = **$3.45/month**

**Very cost effective!**

---

## Troubleshooting

### Issue: "S3 storage not configured"

**Cause**: Missing AWS credentials in .env

**Solution**: Add all 4 required variables:
```bash
AWS_S3_BUCKET="..."
AWS_S3_REGION="..."
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
```

### Issue: "Failed to upload to S3"

**Cause**: Incorrect IAM permissions

**Solution**: Verify IAM policy includes `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`

### Issue: "Access Denied" errors

**Cause**: Bucket policy or IAM permissions issue

**Solution**: 
1. Check bucket policy (should not block IAM user)
2. Verify IAM user has correct permissions
3. Verify credentials are correct

### Issue: Files not persisting after restart

**Cause**: S3 not configured or failing silently

**Solution**:
1. Check backend logs for S3 initialization message
2. Verify all 4 env variables are set
3. Test S3 access manually with AWS CLI

---

## Testing

### Test S3 Configuration

```python
# Test upload
import boto3
s3 = boto3.client('s3', 
    region_name='us-east-1',
    aws_access_key_id='AKIA...',
    aws_secret_access_key='...'
)

# Test write
s3.put_object(
    Bucket='videoforge-media-prod',
    Key='test/hello.txt',
    Body=b'Hello S3!'
)

# Test read
obj = s3.get_object(Bucket='videoforge-media-prod', Key='test/hello.txt')
print(obj['Body'].read())  # Should print: b'Hello S3!'

# Test delete
s3.delete_object(Bucket='videoforge-media-prod', Key='test/hello.txt')
```

---

## Security Best Practices

### ✅ **DO:**
- Use IAM users with minimal permissions
- Enable bucket encryption (SSE-S3 or SSE-KMS)
- Block public access to bucket
- Rotate access keys regularly
- Use environment variables for credentials (never hardcode)

### ❌ **DON'T:**
- Don't make bucket public
- Don't commit AWS credentials to git
- Don't use root AWS account credentials
- Don't give broader permissions than needed

---

## Files Modified

1. **`/app/backend/storage_service.py`** - Complete rewrite with S3 support
2. **`/app/backend/.env`** - Added S3 configuration variables

---

## Deployment Checklist

- [ ] Create S3 bucket in AWS
- [ ] Create IAM user with S3 permissions
- [ ] Generate and save access keys
- [ ] Add S3 credentials to backend `.env`
- [ ] Test S3 access (upload/download)
- [ ] Deploy to production
- [ ] Verify S3 storage initialization in logs
- [ ] Test creating project with voice/thumbnail/scenes
- [ ] Verify files uploaded to S3
- [ ] Restart container and verify files persist

---

**Status**: 🟢 **S3 STORAGE READY**

Your VideoForge3 application now has production-grade persistent storage! 🎉

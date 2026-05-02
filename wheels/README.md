# Python Wheel Files for VideoForge3

## Overview

This directory contains all Python wheel (.whl) files required for VideoForge3 backend installation.

**Total Files:** 126 wheel packages  
**Total Size:** ~135 MB (compressed: 132 MB)  
**Python Version:** 3.11  
**Architecture:** Linux ARM64 (aarch64) / Universal

---

## What's Included

All dependencies from `requirements.txt`:

### Core Framework
- `fastapi==0.110.1` - Web framework
- `uvicorn==0.25.0` - ASGI server
- `starlette==0.37.2` - ASGI toolkit

### Database
- `motor==3.3.1` - Async MongoDB driver
- `pymongo==4.5.0` - MongoDB Python driver

### AI & ML Libraries
- `openai==1.99.9` - OpenAI API client
- `litellm==1.80.0` - LLM proxy
- `emergentintegrations==0.1.0` - Emergent integrations
- `google-generativeai==0.8.6` - Google AI
- `tiktoken==0.12.0` - Token counter
- `tokenizers==0.22.2` - Hugging Face tokenizers

### AWS Integration
- `boto3==1.42.86` - AWS SDK
- `botocore==1.42.86` - AWS core
- `s3transfer==0.16.0` - S3 file transfer

### Authentication & Security
- `PyJWT==2.12.1` - JWT tokens
- `python-jose==3.5.0` - JWT implementation
- `passlib==1.7.4` - Password hashing
- `bcrypt==4.1.3` - Bcrypt hashing
- `cryptography==46.0.7` - Cryptographic recipes

### Google OAuth & YouTube
- `google-auth==2.49.1` - Google authentication
- `google-auth-oauthlib==1.3.1` - OAuth flow
- `google-api-python-client==2.194.0` - Google APIs
- `google-auth-httplib2==0.3.1` - HTTP library

### Payment Processing
- `stripe==15.0.1` - Stripe API client

### Data Processing
- `pandas==3.0.2` - Data analysis
- `numpy==2.4.4` - Numerical computing
- `pillow==12.2.0` - Image processing
- `lxml==6.1.0` - XML/HTML parser

### HTTP & Networking
- `httpx==0.28.1` - HTTP client
- `aiohttp==3.13.5` - Async HTTP client
- `requests==2.33.1` - HTTP library
- `requests-oauthlib==2.0.0` - OAuth for requests

### Development Tools
- `black==26.3.1` - Code formatter
- `flake8==7.3.0` - Linter
- `mypy==1.20.0` - Type checker
- `pytest==9.0.3` - Testing framework
- `isort==8.0.1` - Import sorter

### Utilities
- `python-dotenv==1.2.2` - Environment variables
- `python-multipart==0.0.24` - Multipart form data
- `pydantic==2.12.5` - Data validation
- `PyYAML==6.0.3` - YAML parser
- `rich==14.3.3` - Terminal formatting
- `tqdm==4.67.3` - Progress bars
- `pytrends==4.9.2` - Google Trends API

---

## Installation Methods

### Method 1: Install from Wheels Directory

```bash
# Install all packages from wheels
pip install /app/wheels/*.whl

# Or install specific package
pip install /app/wheels/fastapi-0.110.1-py3-none-any.whl
```

### Method 2: Install from requirements.txt with local wheels

```bash
# Use wheels as source
pip install --no-index --find-links=/app/wheels -r requirements.txt
```

### Method 3: Offline Installation (No Internet)

```bash
# Copy wheels to offline machine
scp python-wheels.tar.gz user@offline-server:/tmp/

# On offline machine
cd /tmp
tar -xzf python-wheels.tar.gz
pip install --no-index --find-links=. /app/backend/requirements.txt
```

### Method 4: Install from Compressed Archive

```bash
# Extract archive
cd /app
tar -xzf python-wheels.tar.gz -C wheels/

# Install from extracted wheels
pip install --no-index --find-links=/app/wheels -r backend/requirements.txt
```

---

## Usage Scenarios

### Scenario 1: Air-Gapped / Offline Server

For servers without internet access:

```bash
# On machine with internet:
cd /app/wheels
tar -czf python-wheels.tar.gz *.whl

# Transfer to offline server
scp python-wheels.tar.gz user@offline-server:/opt/videoforge/

# On offline server:
cd /opt/videoforge
tar -xzf python-wheels.tar.gz
pip install --no-index --find-links=. -r requirements.txt
```

### Scenario 2: Faster Deployment

Pre-downloaded wheels speed up deployment:

```bash
# Include wheels in Docker image
COPY wheels/ /tmp/wheels/
RUN pip install --no-index --find-links=/tmp/wheels -r requirements.txt
```

### Scenario 3: Network-Restricted Environment

When PyPI is blocked but local files are allowed:

```bash
# Copy wheels to project
cp /app/wheels/*.whl /opt/videoforge/backend/wheels/

# Install locally
cd /opt/videoforge/backend
pip install --no-index --find-links=wheels -r requirements.txt
```

### Scenario 4: Version Lock

Ensure exact versions are used:

```bash
# Install specific versions from wheels
pip install --no-index --find-links=/app/wheels \
  fastapi==0.110.1 \
  uvicorn==0.25.0 \
  motor==3.3.1
```

---

## Wheel Files List

### Complete List (126 packages):

```
aiohappyeyeballs-2.6.1-py3-none-any.whl
aiohttp-3.13.5-cp311-cp311-manylinux2014_aarch64.whl
aiosignal-1.4.0-py3-none-any.whl
annotated_doc-0.0.4-py3-none-any.whl
annotated_types-0.7.0-py3-none-any.whl
anyio-4.13.0-py3-none-any.whl
attrs-26.1.0-py3-none-any.whl
bcrypt-4.1.3-cp39-abi3-manylinux_2_28_aarch64.whl
black-26.3.1-py3-none-any.whl
boto3-1.42.86-py3-none-any.whl
botocore-1.42.86-py3-none-any.whl
certifi-2026.2.25-py3-none-any.whl
cffi-2.0.0-cp311-cp311-manylinux2014_aarch64.whl
charset_normalizer-3.4.7-cp311-cp311-manylinux2014_aarch64.whl
click-8.3.2-py3-none-any.whl
cryptography-46.0.7-cp311-abi3-manylinux_2_34_aarch64.whl
distro-1.9.0-py3-none-any.whl
dnspython-2.8.0-py3-none-any.whl
ecdsa-0.19.2-py2.py3-none-any.whl
email_validator-2.3.0-py3-none-any.whl
emergentintegrations-0.1.0-py3-none-any.whl
fastapi-0.110.1-py3-none-any.whl
fastuuid-0.14.0-py3-none-any.whl
filelock-3.25.2-py3-none-any.whl
flake8-7.3.0-py2.py3-none-any.whl
frozenlist-1.8.0-cp311-cp311-manylinux2014_aarch64.whl
fsspec-2026.3.0-py3-none-any.whl
google_ai_generativelanguage-0.6.15-py3-none-any.whl
google_api_core-2.30.2-py3-none-any.whl
google_api_python_client-2.194.0-py3-none-any.whl
google_auth-2.49.1-py2.py3-none-any.whl
google_auth_httplib2-0.3.1-py2.py3-none-any.whl
google_auth_oauthlib-1.3.1-py2.py3-none-any.whl
google_genai-1.71.0-py3-none-any.whl
google_generativeai-0.8.6-py3-none-any.whl
googleapis_common_protos-1.74.0-py2.py3-none-any.whl
grpcio-1.80.0-cp311-cp311-manylinux2014_aarch64.whl
grpcio_status-1.71.2-py3-none-any.whl
h11-0.16.0-py3-none-any.whl
hf_xet-1.4.3-py3-none-any.whl
httpcore-1.0.9-py3-none-any.whl
httplib2-0.31.2-py3-none-any.whl
httpx-0.28.1-py3-none-any.whl
huggingface_hub-1.9.2-py3-none-any.whl
idna-3.11-py3-none-any.whl
importlib_metadata-9.0.0-py3-none-any.whl
iniconfig-2.3.0-py3-none-any.whl
isort-8.0.1-py3-none-any.whl
Jinja2-3.1.6-py3-none-any.whl
jiter-0.13.0-cp311-cp311-manylinux2014_aarch64.whl
jmespath-1.1.0-py3-none-any.whl
jq-1.11.0-py3-none-any.whl
jsonschema-4.26.0-py3-none-any.whl
jsonschema_specifications-2025.9.1-py3-none-any.whl
librt-0.8.1-py3-none-any.whl
litellm-1.80.0-py3-none-any.whl
lxml-6.1.0-cp311-cp311-manylinux2014_aarch64.whl
markdown_it_py-4.0.0-py3-none-any.whl
MarkupSafe-3.0.3-cp311-cp311-manylinux2014_aarch64.whl
mccabe-0.7.0-py2.py3-none-any.whl
mdurl-0.1.2-py3-none-any.whl
motor-3.3.1-py3-none-any.whl
multidict-6.7.1-cp311-cp311-manylinux2014_aarch64.whl
mypy-1.20.0-py3-none-any.whl
mypy_extensions-1.1.0-py3-none-any.whl
numpy-2.4.4-cp311-cp311-manylinux2014_aarch64.whl
oauthlib-3.3.1-py3-none-any.whl
openai-1.99.9-py3-none-any.whl
packaging-26.0-py3-none-any.whl
pandas-3.0.2-cp311-cp311-manylinux2014_aarch64.whl
passlib-1.7.4-py2.py3-none-any.whl
pathspec-1.0.4-py3-none-any.whl
pillow-12.2.0-cp311-cp311-manylinux2014_aarch64.whl
platformdirs-4.9.6-py3-none-any.whl
pluggy-1.6.0-py3-none-any.whl
propcache-0.4.1-cp311-cp311-manylinux2014_aarch64.whl
proto_plus-1.27.2-py3-none-any.whl
protobuf-5.29.6-cp310-abi3-manylinux2014_aarch64.whl
pyasn1-0.6.3-py3-none-any.whl
pyasn1_modules-0.4.2-py3-none-any.whl
pycodestyle-2.14.0-py2.py3-none-any.whl
pycparser-3.0-py3-none-any.whl
pydantic-2.12.5-py3-none-any.whl
pydantic_core-2.41.5-cp311-cp311-manylinux2014_aarch64.whl
pyflakes-3.4.0-py2.py3-none-any.whl
Pygments-2.20.0-py3-none-any.whl
PyJWT-2.12.1-py3-none-any.whl
pymongo-4.5.0-cp311-cp311-manylinux2014_aarch64.whl
pyparsing-3.3.2-py3-none-any.whl
pytest-9.0.3-py3-none-any.whl
python_dateutil-2.9.0.post0-py2.py3-none-any.whl
python_dotenv-1.2.2-py3-none-any.whl
python_jose-3.5.0-py2.py3-none-any.whl
python_multipart-0.0.24-py3-none-any.whl
pytokens-0.4.1-py3-none-any.whl
pytrends-4.9.2-py3-none-any.whl
PyYAML-6.0.3-cp311-cp311-manylinux2014_aarch64.whl
referencing-0.37.0-py3-none-any.whl
regex-2026.4.4-cp311-cp311-manylinux2014_aarch64.whl
requests-2.33.1-py3-none-any.whl
requests_oauthlib-2.0.0-py2.py3-none-any.whl
rich-14.3.3-py3-none-any.whl
rpds_py-0.30.0-cp311-cp311-manylinux2014_aarch64.whl
rsa-4.9.1-py3-none-any.whl
s3transfer-0.16.0-py3-none-any.whl
s5cmd-0.2.0-py3-none-manylinux_2_17_aarch64.whl
shellingham-1.5.4-py2.py3-none-any.whl
six-1.17.0-py2.py3-none-any.whl
sniffio-1.3.1-py3-none-any.whl
starlette-0.37.2-py3-none-any.whl
stripe-15.0.1-py3-none-any.whl
tenacity-9.1.4-py3-none-any.whl
tiktoken-0.12.0-cp311-cp311-manylinux_2_28_aarch64.whl
tokenizers-0.22.2-cp39-abi3-manylinux2014_aarch64.whl
tqdm-4.67.3-py3-none-any.whl
typer-0.24.1-py3-none-any.whl
typing_extensions-4.15.0-py3-none-any.whl
typing_inspection-0.4.2-py3-none-any.whl
tzdata-2026.1-py2.py3-none-any.whl
uritemplate-4.2.0-py3-none-any.whl
urllib3-2.6.3-py3-none-any.whl
uvicorn-0.25.0-py3-none-any.whl
watchfiles-1.1.1-cp311-cp311-manylinux2014_aarch64.whl
websockets-16.0-cp311-cp311-manylinux2014_aarch64.whl
yarl-1.23.0-cp311-cp311-manylinux2014_aarch64.whl
zipp-3.23.0-py3-none-any.whl
```

---

## Platform Compatibility

### Supported Platforms:
- **Linux ARM64** (aarch64) - Primary architecture
- **Universal Python packages** - Cross-platform

### Python Version:
- **Python 3.11** (cp311) - Required
- Some packages support Python 3.9+ (cp39-abi3)

### Operating Systems:
- Ubuntu 22.04+ ✅
- Debian 11+ ✅
- RHEL 8+ ✅
- Amazon Linux 2023 ✅
- Docker containers ✅

---

## Verification

### Check Installed Packages

```bash
# List all installed packages
pip list

# Check specific package
pip show fastapi

# Verify versions match requirements
pip freeze | grep fastapi
```

### Test Installation

```python
# Test imports
import fastapi
import motor
import openai
import boto3
import stripe

print("All packages imported successfully!")
```

### Compare with requirements.txt

```bash
# Generate installed packages list
pip freeze > installed.txt

# Compare with requirements
diff requirements.txt installed.txt
```

---

## Troubleshooting

### Issue 1: Architecture Mismatch

**Error:**
```
ERROR: fastapi-0.110.1-cp311-cp311-manylinux_x86_64.whl is not a supported wheel
```

**Solution:**
Download wheels for your architecture:
```bash
pip download -r requirements.txt --platform manylinux_2_17_x86_64
```

### Issue 2: Python Version Mismatch

**Error:**
```
ERROR: Package requires Python >=3.11
```

**Solution:**
Upgrade Python or use compatible wheels:
```bash
python3.11 -m pip install --no-index --find-links=wheels -r requirements.txt
```

### Issue 3: Missing Dependencies

**Error:**
```
ERROR: Could not find a version that satisfies the requirement
```

**Solution:**
Download all dependencies:
```bash
pip download -r requirements.txt --dest wheels --no-deps=False
```

### Issue 4: Corrupted Wheel

**Error:**
```
ERROR: Invalid wheel filename
```

**Solution:**
Re-download the specific package:
```bash
pip download package-name==version --dest wheels
```

---

## Building Custom Wheels

### For Different Platform

```bash
# For x86_64 Linux
pip download -r requirements.txt \
  --platform manylinux_2_17_x86_64 \
  --platform manylinux2014_x86_64 \
  --dest wheels-x86_64

# For macOS
pip download -r requirements.txt \
  --platform macosx_10_9_x86_64 \
  --platform macosx_11_0_arm64 \
  --dest wheels-macos

# For Windows
pip download -r requirements.txt \
  --platform win_amd64 \
  --dest wheels-windows
```

### For Different Python Version

```bash
# For Python 3.10
pip download -r requirements.txt \
  --python-version 3.10 \
  --dest wheels-py310

# For Python 3.12
pip download -r requirements.txt \
  --python-version 3.12 \
  --dest wheels-py312
```

---

## Storage & Distribution

### Compress for Distribution

```bash
# Create tarball
tar -czf python-wheels-$(date +%Y%m%d).tar.gz wheels/

# Create zip
zip -r python-wheels-$(date +%Y%m%d).zip wheels/
```

### Upload to Cloud Storage

```bash
# AWS S3
aws s3 cp python-wheels.tar.gz s3://your-bucket/dependencies/

# Download from S3
aws s3 cp s3://your-bucket/dependencies/python-wheels.tar.gz .
```

### Setup Local PyPI Server

```bash
# Install pypiserver
pip install pypiserver

# Run local PyPI server
pypi-server run -p 8080 /app/wheels

# Install from local server
pip install --index-url http://localhost:8080/simple/ fastapi
```

---

## Maintenance

### Update Wheels

```bash
# Download latest versions
pip download -r requirements.txt --dest wheels-new --upgrade

# Compare versions
ls wheels/ > old-versions.txt
ls wheels-new/ > new-versions.txt
diff old-versions.txt new-versions.txt
```

### Clean Old Wheels

```bash
# Remove old versions
cd /app/wheels
find . -name "*.whl" -mtime +90 -delete

# Keep only latest version of each package
# (manual cleanup recommended)
```

### Verify Integrity

```bash
# Check file integrity
cd /app/wheels
sha256sum *.whl > checksums.txt

# Verify checksums
sha256sum -c checksums.txt
```

---

## Best Practices

1. **Version Pinning**: Use exact versions in requirements.txt
2. **Regular Updates**: Update wheels monthly for security patches
3. **Backup**: Keep wheels in version control or artifact storage
4. **Testing**: Test wheels in staging before production
5. **Documentation**: Maintain changelog of wheel updates
6. **Security**: Scan wheels for vulnerabilities
7. **Cleanup**: Remove unused old versions

---

## Resources

- **pip documentation**: https://pip.pypa.io/
- **Python Packaging**: https://packaging.python.org/
- **PyPI**: https://pypi.org/

---

## Support

For issues with wheel files:
1. Check pip version: `pip --version` (should be 23.0+)
2. Check Python version: `python --version` (should be 3.11+)
3. Verify platform: `python -c "import platform; print(platform.machine())"`
4. Re-download wheels if corrupted

---

**Generated:** May 2, 2026  
**Python:** 3.11  
**Platform:** Linux ARM64 (aarch64)  
**Total Size:** 135 MB (126 packages)

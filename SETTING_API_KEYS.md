# Where to Set API Keys

This guide explains exactly where to set API keys for different deployment scenarios.

## Deployment Scenarios

### 1. Local Development (.env file)

**Location:** Create a `.env` file in the project root directory

**Steps:**
1. Create file: `travel-ai-agent/.env`
2. Add your API keys (see example below)
3. The `.env` file is already in `.gitignore` for security

**Example .env file:**
```bash
# AI Services
OPENAI_API_KEY=sk-your-openai-key-here
PINECONE_API_KEY=your-pinecone-key-here
PINECONE_ENVIRONMENT=us-east-1-aws

# Payment
STRIPE_API_KEY=sk_test_your-stripe-key-here

# Authentication
JWT_SECRET=your-generated-secret-here

# External APIs
AMADEUS_API_KEY=your-amadeus-key
AMADEUS_SECRET=your-amadeus-secret
BOOKING_API_KEY=your-booking-key
WEATHER_API_KEY=your-openweather-key

# Notifications
SENDGRID_API_KEY=SG.your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Databases (local)
DATABASE_URL=postgresql://travel:travel123@localhost:5432/travel_db
REDIS_URL=redis://localhost:6379

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**How to use:**
```bash
# Backend will automatically load from .env
cd backend
python main.py
```

---

### 2. Render Deployment (Render Dashboard)

**Location:** Render.com web dashboard

**Steps:**
1. Go to https://dashboard.render.com/
2. Select your service (travel-ai-backend)
3. Click "Environment" tab
4. Add each environment variable one by one
5. Click "Save Changes"
6. Redeploy the service

**Render Dashboard Setup:**

For **Backend Service** (travel-ai-backend):
- `OPENAI_API_KEY` → Your OpenAI key
- `PINECONE_API_KEY` → Your Pinecone key
- `PINECONE_ENVIRONMENT` → `us-east-1-aws`
- `STRIPE_API_KEY` → Your Stripe key
- `JWT_SECRET` → Your generated secret
- `DATABASE_URL` → Render provides this automatically
- `REDIS_URL` → Add Redis from marketplace, Render provides URL

For **Frontend Service** (travel-ai-frontend):
- `NEXT_PUBLIC_API_URL` → `https://travel-ai-backend.onrender.com`

**Render Database:**
- Render automatically provides `DATABASE_URL` for PostgreSQL
- No need to set it manually

**Render Redis:**
1. Go to Render dashboard
2. Click "New +" → "Redis"
3. Create Redis instance
4. Render provides `REDIS_URL` automatically
5. Add this URL to your backend service environment variables

---

### 3. Kubernetes Deployment (k8s/secrets.yaml)

**Location:** `k8s/secrets.yaml` file

**Steps:**
1. Open file: `k8s/secrets.yaml`
2. Replace placeholder values with your actual keys
3. Apply to Kubernetes cluster

**Example k8s/secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: travel-secrets
  namespace: travel-ai
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-actual-openai-key"
  PINECONE_API_KEY: "your-actual-pinecone-key"
  PINECONE_ENVIRONMENT: "us-east-1-aws"
  STRIPE_API_KEY: "sk_test_your-actual-stripe-key"
  JWT_SECRET: "your-actual-generated-secret"
  AMADEUS_API_KEY: "your-actual-amadeus-key"
  AMADEUS_SECRET: "your-actual-amadeus-secret"
  BOOKING_API_KEY: "your-actual-booking-key"
  WEATHER_API_KEY: "your-actual-weather-key"
  SENDGRID_API_KEY: "SG.your-actual-sendgrid-key"
  TWILIO_ACCOUNT_SID: "your-actual-twilio-sid"
  TWILIO_AUTH_TOKEN: "your-actual-twilio-token"
  TWILIO_PHONE_NUMBER: "+1234567890"
```

**Apply to Kubernetes:**
```bash
kubectl apply -f k8s/secrets.yaml
```

**Alternative: Using kubectl create secret**
```bash
kubectl create secret generic travel-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  --from-literal=PINECONE_API_KEY=your-key \
  --from-literal=JWT_SECRET=your-secret \
  -n travel-ai
```

---

### 4. Docker Compose (docker-compose.yml)

**Location:** Environment variables in `docker-compose.yml` or `.env` file

**Option A: In docker-compose.yml**
```yaml
services:
  backend:
    environment:
      - OPENAI_API_KEY=sk-your-key
      - PINECONE_API_KEY=your-key
      - JWT_SECRET=your-secret
```

**Option B: Using .env file (recommended)**
1. Create `.env` file in project root
2. Docker Compose automatically loads it
3. Reference variables in docker-compose.yml:
```yaml
services:
  backend:
    env_file:
      - .env
```

---

## Quick Reference

| Deployment Method | Where to Set Keys |
|-------------------|-------------------|
| Local Development | `.env` file in project root |
| Render | Render Dashboard → Environment tab |
| Kubernetes | `k8s/secrets.yaml` or kubectl command |
| Docker Compose | `.env` file or docker-compose.yml |

---

## Security Best Practices

1. **Never commit .env file to git** - It's already in `.gitignore`
2. **Never commit k8s/secrets.yaml with real keys** - Use placeholder values
3. **Use different keys for dev/prod** - Don't share keys
4. **Rotate keys regularly** - Especially for production
5. **Limit key permissions** - Only grant necessary access

---

## Minimum Keys for Testing

If you're just testing/researching, you only need to set these:

**For Local Development (.env):**
```bash
OPENAI_API_KEY=sk-your-key
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-east-1-aws
JWT_SECRET=your-generated-secret
```

**For Render Dashboard:**
- `OPENAI_API_KEY`
- `PINECONE_API_KEY`
- `PINECONE_ENVIRONMENT` = `us-east-1-aws`
- `JWT_SECRET`

**For Kubernetes (k8s/secrets.yaml):**
```yaml
stringData:
  OPENAI_API_KEY: "sk-your-key"
  PINECONE_API_KEY: "your-key"
  PINECONE_ENVIRONMENT: "us-east-1-aws"
  JWT_SECRET: "your-secret"
```

---

## Next Steps

1. **Get your free keys** (see `FREE_TIER_GUIDE.md`)
2. **Choose deployment method** (Local, Render, or Kubernetes)
3. **Set keys in appropriate location** (see above)
4. **Deploy the application**
5. **Test the features**

---

## Troubleshooting

### Keys not working?
- Check for typos in key values
- Ensure keys have correct permissions
- Verify keys are active (not expired)
- Check service dashboards for key status

### Environment variables not loading?
- Ensure .env file is in project root
- Check .env file has correct format (KEY=value)
- For Docker, ensure env_file is referenced
- For Kubernetes, ensure secrets are applied

### Render deployment issues?
- Check Render dashboard for service logs
- Verify environment variables are set correctly
- Ensure database and Redis are created
- Check for any build errors

### Kubernetes issues?
- Verify secrets are created: `kubectl get secrets -n travel-ai`
- Check secret values: `kubectl get secret travel-secrets -n travel-ai -o yaml`
- Verify pods are running: `kubectl get pods -n travel-ai`
- Check pod logs: `kubectl logs <pod-name> -n travel-ai`

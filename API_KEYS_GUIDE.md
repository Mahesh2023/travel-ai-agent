# API Keys Guide

This guide lists all required API keys and how to obtain them.

## Required API Keys

### 1. OpenAI API Key
**Purpose:** AI/LLM services (GPT-4, embeddings)

**How to get:**
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

**Cost:** Pay-as-you-go (approx. $0.03/1K tokens for GPT-4)

**Documentation:** https://platform.openai.com/docs

---

### 2. Pinecone API Key
**Purpose:** Vector database for RAG system

**How to get:**
1. Go to https://www.pinecone.io/
2. Sign up for free account
3. Create a project
4. Go to API Keys section
5. Copy the API key

**Environment variable:** `PINECONE_ENVIRONMENT` (e.g., `us-east-1-aws`)

**Cost:** Free tier available (1 index, 5K vectors)

**Documentation:** https://docs.pinecone.io/

---

### 3. Stripe API Key
**Purpose:** Payment processing

**How to get:**
1. Go to https://stripe.com/
2. Sign up for account
3. Go to Developers → API keys
4. Copy the "Publishable key" and "Secret key"
5. Use the Secret key for backend

**Cost:** Transaction fees (2.9% + 30¢ per transaction)

**Documentation:** https://stripe.com/docs/api

---

### 4. Amadeus API Key & Secret
**Purpose:** Flight booking integration

**How to get:**
1. Go to https://developers.amadeus.com/
2. Sign up for developer account
3. Create an application
4. Get API Key and Secret from dashboard

**Cost:** Free test tier available

**Documentation:** https://developers.amadeus.com/

---

### 5. Booking.com API Key
**Purpose:** Hotel booking integration

**How to get:**
1. Go to https://partners.booking.com/
2. Apply for partner access
3. Get API credentials after approval

**Cost:** Varies by partnership level

**Documentation:** https://developers.booking.com/

---

### 6. OpenWeatherMap API Key
**Purpose:** Weather forecasts

**How to get:**
1. Go to https://openweathermap.org/api
2. Sign up for free account
3. Go to API keys section
4. Copy your API key

**Cost:** Free tier available (1,000 calls/day)

**Documentation:** https://openweathermap.org/api

---

### 7. SendGrid API Key
**Purpose:** Email notifications

**How to get:**
1. Go to https://sendgrid.com/
2. Sign up for free account
3. Go to Settings → API Keys
4. Create API key with "Mail Send" permissions
5. Copy the key

**Cost:** Free tier available (100 emails/day)

**Documentation:** https://docs.sendgrid.com/

---

### 8. Twilio API Credentials
**Purpose:** SMS notifications

**How to get:**
1. Go to https://www.twilio.com/
2. Sign up for free account
3. Go to Console → Settings → API Keys
4. Get Account SID and Auth Token
5. Get a phone number from Numbers → Buy a Number

**Environment variables:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

**Cost:** Pay-as-you-go (approx. $0.0075/SMS)

**Documentation:** https://www.twilio.com/docs

---

### 9. JWT Secret
**Purpose:** Authentication token signing

**How to generate:**
```bash
# Generate a secure random string
openssl rand -hex 32
```

Or use an online generator like https://generate-random.org/api-key-generator

**Cost:** Free (self-generated)

---

### 10. Database URL
**Purpose:** PostgreSQL connection

**For Render deployment:**
- Render provides this automatically in the dashboard
- Format: `postgresql://user:password@host:port/database`

**For local development:**
```bash
# Install PostgreSQL locally
# Then use:
DATABASE_URL=postgresql://travel:travel123@localhost:5432/travel_db
```

**Cost:** Free tier available on Render

---

### 11. Redis URL
**Purpose:** Caching and session storage

**For Render deployment:**
- Add Redis from Render marketplace
- Render provides the URL automatically

**For local development:**
```bash
# Install Redis locally
# Then use:
REDIS_URL=redis://localhost:6379
```

**Cost:** Free tier available on Render

---

## Optional API Keys (For Full Microservices)

### Cassandra Contact Points
**Purpose:** Inventory database

**For production:** Use managed Cassandra (DataStax Astra)
**For local:** Install Cassandra locally

### ClickHouse Credentials
**Purpose:** Analytics database

**For production:** Use managed ClickHouse
**For local:** Install ClickHouse locally

### Elasticsearch URL
**Purpose:** Search engine

**For production:** Use managed Elasticsearch (Elastic Cloud)
**For local:** Install Elasticsearch locally

---

## Environment Variables File

Create a `.env` file in the root directory:

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

# Databases
DATABASE_URL=postgresql://travel:travel123@localhost:5432/travel_db
REDIS_URL=redis://localhost:6379
```

---

## Quick Start for Testing

If you want to test the platform quickly, you only need these **minimum required keys**:

1. **OpenAI API Key** - For AI features
2. **Pinecone API Key** - For RAG/knowledge base
3. **JWT Secret** - For authentication (generate with openssl)

The rest can be added later when you're ready to integrate external services.

---

## Security Best Practices

1. **Never commit API keys to git** - They're already in `.gitignore`
2. **Use environment variables** - Never hardcode keys in code
3. **Rotate keys regularly** - Especially for production
4. **Use separate keys for dev/prod** - Don't share keys
5. **Monitor usage** - Set up alerts for unusual activity
6. **Set spending limits** - On OpenAI, Stripe, etc.

---

## Cost Estimates (Monthly at Scale)

| Service | Cost at 100M users |
|---------|-------------------|
| OpenAI | $400,000 |
| Pinecone | $50,000 |
| Stripe | Transaction fees only |
| Amadeus | Per-call pricing |
| SendGrid | $10,000 |
| Twilio | $5,000 |
| **Total AI/API** | **~$465,000** |

---

## Support

If you have issues getting any API key:
- Check the service's documentation
- Contact the service's support
- Review the service's pricing page

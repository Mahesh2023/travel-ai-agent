# Free Tier Guide for Research & Testing

This guide explains how to use all services with free tiers for research and testing purposes.

## Free Tier Availability

| Service | Free Tier | Limitations | Good for Research? |
|---------|-----------|-------------|-------------------|
| OpenAI | $5 free credit | Limited tokens | ✅ Yes (limited) |
| Pinecone | Free tier | 1 index, 5K vectors | ✅ Yes |
| Stripe | Test mode | No real payments | ✅ Yes |
| Amadeus | Test tier | Limited calls | ✅ Yes |
| Booking.com | No free tier | Requires partnership | ❌ No |
| OpenWeatherMap | Free tier | 1,000 calls/day | ✅ Yes |
| SendGrid | Free tier | 100 emails/day | ✅ Yes |
| Twilio | Free trial | Trial credits | ✅ Yes |
| JWT Secret | Self-generated | Unlimited | ✅ Yes |
| PostgreSQL | Free on Render | 1GB storage | ✅ Yes |
| Redis | Free on Render | 25MB storage | ✅ Yes |

## Minimum Required for Research

For basic research and testing, you only need **3 free services**:

### 1. OpenAI (Free $5 Credit)
- **Sign up:** https://platform.openai.com/
- **Free credit:** $5 for new accounts
- **What you get:** ~166K GPT-4 tokens or ~1.6M GPT-3.5 tokens
- **Research use:** Test AI agents, RAG system, chat features
- **Limitation:** Will run out after testing, need to add payment method

### 2. Pinecone (Free Tier)
- **Sign up:** https://www.pinecone.io/
- **Free tier:** 1 index, 5K vectors, 1 project
- **What you get:** Vector database for RAG
- **Research use:** Test knowledge base, semantic search
- **Limitation:** Only 5K vectors (enough for testing)

### 3. PostgreSQL (Free on Render)
- **Sign up:** https://render.com/
- **Free tier:** 1GB storage
- **What you get:** Database for users, bookings
- **Research use:** Test data models, CRUD operations
- **Limitation:** 1GB storage (enough for testing)

## Optional Free Services for Testing

### 4. OpenWeatherMap (Free Tier)
- **Sign up:** https://openweathermap.org/api
- **Free tier:** 1,000 calls/day
- **Research use:** Test weather integration
- **Limitation:** 1,000 calls/day (plenty for testing)

### 5. SendGrid (Free Tier)
- **Sign up:** https://sendgrid.com/
- **Free tier:** 100 emails/day
- **Research use:** Test email notifications
- **Limitation:** 100 emails/day (plenty for testing)

### 6. Stripe (Test Mode)
- **Sign up:** https://stripe.com/
- **Test mode:** No charges, test cards only
- **Research use:** Test payment flow
- **Limitation:** No real payments (perfect for testing)

### 7. Amadeus (Test Tier)
- **Sign up:** https://developers.amadeus.com/
- **Test tier:** Limited API calls
- **Research use:** Test flight search
- **Limitation:** Limited calls (enough for testing)

### 8. Twilio (Free Trial)
- **Sign up:** https://www.twilio.com/
- **Free trial:** Trial credits
- **Research use:** Test SMS notifications
- **Limitation:** Trial credits (enough for testing)

## Services Without Free Tiers

### Booking.com
- **Status:** No free tier available
- **Alternative:** Use demo mode in MCP service
- **Research use:** Mock hotel data for testing
- **Recommendation:** Skip for research, use demo data

## Research-Only Environment Setup

### Step 1: Get Free OpenAI Key
1. Go to https://platform.openai.com/
2. Sign up (you get $5 free credit)
3. Create API key
4. Set environment variable: `OPENAI_API_KEY=sk-...`

### Step 2: Get Free Pinecone Key
1. Go to https://www.pinecone.io/
2. Sign up (free tier)
3. Create project and index
4. Get API key and environment
5. Set environment variables:
   - `PINECONE_API_KEY=...`
   - `PINECONE_ENVIRONMENT=us-east-1-aws`

### Step 3: Generate JWT Secret
```bash
openssl rand -hex 32
```
Set: `JWT_SECRET=...`

### Step 4: Deploy to Render (Free)
1. Connect GitHub repo to Render
2. Render provides free PostgreSQL and Redis
3. Set environment variables in Render dashboard
4. Deploy

### Step 5: Test with Demo Data
- Booking.com: Use demo mode (no API key needed)
- Other services: Add free tier keys when ready

## Research Environment .env File

```bash
# Essential (Free)
OPENAI_API_KEY=sk-your-free-key
PINECONE_API_KEY=your-free-key
PINECONE_ENVIRONMENT=us-east-1-aws
JWT_SECRET=your-generated-secret

# Optional Free Services
STRIPE_API_KEY=sk_test_your-test-key
AMADEUS_API_KEY=your-test-key
AMADEUS_SECRET=your-test-secret
WEATHER_API_KEY=your-free-key
SENDGRID_API_KEY=SG.your-free-key
TWILIO_ACCOUNT_SID=your-trial-sid
TWILIO_AUTH_TOKEN=your-trial-token
TWILIO_PHONE_NUMBER=+1234567890

# Infrastructure (Render provides)
DATABASE_URL=postgresql://... (from Render)
REDIS_URL=redis://... (from Render)

# Skip for research
BOOKING_API_KEY= (use demo mode)
```

## What You Can Test with Free Tiers

### ✅ Can Test (Free):
- AI agent orchestration
- RAG knowledge base (limited to 5K vectors)
- User authentication
- Trip planning with AI
- Basic search functionality
- Payment flow (test mode only)
- Weather integration
- Email notifications (100/day)
- SMS notifications (trial credits)
- Database operations
- Caching strategies

### ❌ Cannot Test (Requires Paid):
- Full-scale search (need more vectors)
- Real flight bookings (need production Amadeus)
- Real hotel bookings (need Booking.com partnership)
- Production payments (need production Stripe)
- High-volume notifications (need paid tiers)
- Production-scale analytics

## Research Limitations

### OpenAI
- $5 free credit will run out after ~166K GPT-4 tokens
- After free credit, need to add payment method
- Can switch to GPT-3.5 for cheaper testing

### Pinecone
- Limited to 5K vectors on free tier
- Enough for testing with small dataset
- Cannot test full-scale knowledge base

### Render
- Free tier spins down after 15 minutes inactivity
- Cold start time (~30 seconds)
- 1GB database limit
- 25MB Redis limit

## Cost Estimate for Extended Research

If you want to extend beyond free tiers for more research:

| Service | Monthly Cost (Research) |
|---------|------------------------|
| OpenAI | $20 (GPT-3.5) |
| Pinecone | $70 (Starter tier) |
| Render | $7 (Starter tier) |
| SendGrid | $15 (Basic tier) |
| **Total** | **~$112/month** |

## Research Recommendations

### For Initial Research (Free):
1. Use OpenAI $5 credit for AI features
2. Use Pinecone free tier for RAG (5K vectors)
3. Use Render free tier for deployment
4. Use demo mode for Booking.com
5. Add optional free services as needed

### For Extended Research ($112/month):
1. Upgrade OpenAI to GPT-3.5 for more tokens
2. Upgrade Pinecone for more vectors
3. Upgrade Render for better performance
4. Add more free tier services

### For Production ($1.7M/month):
1. Use full microservices architecture
2. Deploy to Kubernetes
3. Use paid tiers for all services
4. Multi-region deployment

## Next Steps

1. **Get free keys:** OpenAI, Pinecone
2. **Generate secret:** JWT secret
3. **Deploy to Render:** Free tier
4. **Test basic features:** AI agents, RAG, auth
5. **Add optional services:** As needed for research
6. **Document findings:** Research notes

## Support

For questions about free tiers:
- Check each service's pricing page
- Review service documentation
- Contact service support if needed

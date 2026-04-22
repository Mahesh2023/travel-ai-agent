# Render Deployment Guide

## Important Note

The Travel AI Agent Platform has been built with a **world-class microservices architecture** designed for **100 million users**. This architecture includes:

- 10+ microservices
- Kubernetes orchestration
- Distributed databases (PostgreSQL, Cassandra, Elasticsearch, ClickHouse)
- Message queues (Kafka)
- Vector databases (Pinecone)
- Global multi-region deployment

**Render.com does not support this level of infrastructure.** Render is designed for simpler applications and cannot handle:
- Kubernetes deployments
- Multiple database types (Cassandra, Elasticsearch, ClickHouse)
- Message queues (Kafka)
- Complex microservices orchestration
- Multi-region deployments

## Deployment Options

### Option 1: Kubernetes (Recommended for Production)

For the full microservices architecture with 100M user scalability:

**Providers:**
- AWS EKS (Elastic Kubernetes Service)
- Google GKE (Google Kubernetes Engine)
- Azure AKS (Azure Kubernetes Service)

**Steps:**
1. Create a Kubernetes cluster
2. Follow the deployment guide in `DEPLOYMENT.md`
3. Apply Kubernetes manifests from `k8s/` directory
4. Configure your domain and SSL

**Cost:** ~$1.7M/month at 100M users scale

### Option 2: Render.com (Simplified Monolithic)

For testing/demo purposes only (limited scalability):

**Limitations:**
- Monolithic backend only
- Single PostgreSQL database
- No Cassandra, Elasticsearch, Kafka, or ClickHouse
- Limited to ~10K users
- Not suitable for production

**Steps:**
1. Connect your GitHub repository to Render
2. Render will automatically detect `render.yaml`
3. Add environment variables in Render dashboard
4. Deploy

**Environment Variables Required:**
```
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=...
REDIS_URL=redis://...
JWT_SECRET=...
STRIPE_API_KEY=sk_...
```

## Architecture Comparison

| Feature | Kubernetes (Full) | Render (Simplified) |
|---------|------------------|---------------------|
| Microservices | 10+ services | 1 monolithic service |
| Databases | PostgreSQL, Cassandra, Elasticsearch, ClickHouse | PostgreSQL only |
| Message Queue | Kafka | None |
| Vector DB | Pinecone | Pinecone (external) |
| Scalability | 100M users | ~10K users |
| Auto-scaling | Yes (HPA) | Limited |
| Multi-region | Yes | No |
| Cost | $1.7M/month | ~$50/month |

## Recommendation

**For Production:** Use Kubernetes with the full microservices architecture. This is the only way to achieve the 100M user scale with the performance, reliability, and features outlined in the architecture.

**For Testing/Demo:** Use Render.com with the simplified monolithic version. This allows you to test basic functionality without setting up a full Kubernetes cluster.

## Quick Start with Render

If you want to deploy to Render for testing:

1. **Push to GitHub** (already done)
2. **Go to** https://render.com
3. **Click "New +"** → "Web Service"
4. **Connect** your GitHub repository
5. **Render will detect** `render.yaml` automatically
6. **Add environment variables** in the Render dashboard
7. **Click "Deploy Web Service"**

The deployment will create:
- Backend service (Python/FastAPI)
- Frontend service (Next.js)
- PostgreSQL database

## Next Steps

For production deployment:
1. Choose a Kubernetes provider (AWS, GCP, Azure)
2. Create a Kubernetes cluster
3. Follow `DEPLOYMENT.md` for detailed instructions
4. Review `SCALING_GUIDE.md` for scaling strategies
5. Set up monitoring and alerting

## Support

For questions about the architecture or deployment:
- Review `ARCHITECTURE.md` for system design
- Review `DEPLOYMENT.md` for Kubernetes deployment
- Review `SCALING_GUIDE.md` for scaling strategies

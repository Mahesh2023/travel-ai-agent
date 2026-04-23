# Travel AI Agent - Kubernetes Deployment for Millions of Users
# Following teloscopy security patterns with horizontal scaling

## Architecture Overview

This Kubernetes deployment scales the Travel AI Agent to handle millions of users with:
- Horizontal Pod Autoscaler (3-100 replicas)
- Redis for distributed rate limiting and session management
- PostgreSQL for persistence
- Security features from teloscopy (CSP, CSRF, rate limiting, consent system)

## Components

1. **travel-agent** - Main application pods (scales 3-100 replicas)
2. **redis** - Distributed caching and rate limiting
3. **postgres** - Persistent data storage

## Deployment Steps

```bash
# Create namespace
kubectl apply -f k8s-simple/namespace.yaml

# Create secrets (update values first)
kubectl apply -f k8s-simple/secrets.yaml

# Create configmap
kubectl apply -f k8s-simple/configmap.yaml

# Deploy Redis
kubectl apply -f k8s-simple/redis.yaml

# Deploy PostgreSQL
kubectl apply -f k8s-simple/postgres.yaml

# Deploy Travel Agent
kubectl apply -f k8s-simple/travel-agent.yaml

# Deploy HPA
kubectl apply -f k8s-simple/hpa.yaml
```

## Scaling Configuration

- **Min replicas**: 3 (for high availability)
- **Max replicas**: 100 (for millions of users)
- **CPU threshold**: 70% utilization
- **Memory threshold**: 80% utilization
- **Scale up**: Up to 100% every 30 seconds
- **Scale down**: Down to 50% every 60 seconds after 5min stabilization

## Security Features Implemented

1. **Security Headers** (from teloscopy):
   - Content-Security-Policy
   - X-Frame-Options: DENY
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection
   - Strict-Transport-Security (HTTPS)
   - Referrer-Policy

2. **CSRF Protection** (from teloscopy):
   - Validates X-Requested-With header
   - Exempts legal endpoints
   - JSON content type bypass

3. **Rate Limiting** (from teloscopy):
   - Sliding window algorithm
   - Redis-backed for distributed deployment
   - Configurable per endpoint

4. **Consent System** (from teloscopy):
   - HMAC-signed tokens
   - 24-hour TTL
   - Purpose-based consent
   - Withdrawal support

5. **Request ID Tracking** (from teloscopy):
   - Unique ID per request
   - Performance logging
   - Error correlation

## Monitoring

```bash
# Check pod status
kubectl get pods -n travel-agent-simple

# Check HPA status
kubectl get hpa -n travel-agent-simple

# Check service status
kubectl get svc -n travel-agent-simple

# View logs
kubectl logs -f deployment/travel-agent -n travel-agent-simple
```

## Capacity Planning

**For 1 million users:**
- 10-20 replicas (based on typical load)
- 5-10 GB total memory
- 2.5-5 GB total CPU

**For 10 million users:**
- 50-100 replicas
- 25-50 GB total memory
- 12.5-25 GB total CPU

## Production Recommendations

1. **Replace in-memory rate limiter with Redis**
2. **Use managed Redis service (AWS ElastiCache, Google Memorystore)**
3. **Use managed PostgreSQL (AWS RDS, Google Cloud SQL)**
4. **Add CDN for static assets**
5. **Implement database connection pooling**
6. **Add monitoring (Prometheus, Grafana)**
7. **Add logging aggregation (ELK, CloudWatch)**
8. **Implement circuit breakers for external APIs**
9. **Add database read replicas**
10. **Implement session affinity for stateful operations

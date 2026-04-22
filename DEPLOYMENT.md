# Deployment Guide

## Prerequisites

- Kubernetes cluster (AWS EKS, GKE, or Azure AKS)
- kubectl configured
- Docker installed
- Domain name configured

## Environment Variables

Create a `.env` file in the root directory:

```bash
# Database
DATABASE_URL=postgresql://travel:travel123@postgres:5432/travel_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# Elasticsearch
ELASTICSEARCH_URL=http://elasticsearch:9200

# Cassandra
CASSANDRA_CONTACT_POINTS=cassandra

# Kafka
KAFKA_BROKERS=kafka:9092

# AI Services
OPENAI_API_KEY=your-openai-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-pinecone-env

# Payment
STRIPE_API_KEY=your-stripe-key

# Authentication
JWT_SECRET=your-jwt-secret

# External APIs
AMADEUS_API_KEY=your-amadeus-key
AMADEUS_SECRET=your-amadeus-secret
BOOKING_API_KEY=your-booking-key
WEATHER_API_KEY=your-weather-key

# Notifications
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-phone
```

## Local Development with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### 2. Create ConfigMap and Secrets

```bash
kubectl apply -f k8s/configmap.yaml

# Update secrets.yaml with your actual values
kubectl apply -f k8s/secrets.yaml
```

### 3. Deploy Infrastructure

```bash
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/elasticsearch.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/cassandra.yaml
```

### 4. Deploy Services

```bash
kubectl apply -f k8s/gateway.yaml
kubectl apply -f k8s/search-service.yaml
kubectl apply -f k8s/booking-service.yaml
kubectl apply -f k8s/inventory-service.yaml
kubectl apply -f k8s/payment-service.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/rag-service.yaml
kubectl apply -f k8s/mcp-service.yaml
kubectl apply -f k8s/notification-service.yaml
kubectl apply -f k8s/frontend.yaml
```

### 5. Deploy Monitoring

```bash
kubectl apply -f k8s/monitoring.yaml
```

### 6. Verify Deployment

```bash
# Check pod status
kubectl get pods -n travel-ai

# Check services
kubectl get svc -n travel-ai

# View logs
kubectl logs -f deployment/api-gateway -n travel-ai
```

## Accessing Services

- **Frontend**: `http://<load-balancer-ip>:3000`
- **API Gateway**: `http://<load-balancer-ip>:8080`
- **Grafana**: `http://<load-balancer-ip>:3000` (monitoring namespace)
- **Prometheus**: `http://<prometheus-service-ip>:9090`

## Scaling

### Manual Scaling

```bash
# Scale a specific deployment
kubectl scale deployment/search-service --replicas=10 -n travel-ai

# Scale all services
kubectl scale deployment --all --replicas=10 -n travel-ai
```

### Auto-scaling

The HPA (Horizontal Pod Autoscaler) is configured to automatically scale services based on CPU and memory usage. You can adjust the thresholds:

```bash
# Edit HPA
kubectl edit hpa search-service-hpa -n travel-ai
```

## Monitoring

### Prometheus

Access Prometheus at `http://<prometheus-service-ip>:9090`

### Grafana

1. Access Grafana at `http://<grafana-service-ip>:3000`
2. Login with username: `admin`, password: `admin`
3. Add Prometheus as a data source
4. Import dashboards from the `dashboards` directory

## Troubleshooting

### Check Pod Logs

```bash
kubectl logs <pod-name> -n travel-ai
```

### Check Service Connectivity

```bash
kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- sh
# Inside the pod
curl http://api-gateway:8080/health
```

### Restart Services

```bash
kubectl rollout restart deployment/<deployment-name> -n travel-ai
```

### Database Issues

```bash
# Connect to PostgreSQL
kubectl exec -it postgres-0 -n travel-ai -- psql -U travel -d travel_db

# Connect to Cassandra
kubectl exec -it cassandra-0 -n travel-ai -- cqlsh
```

## CI/CD

The CI/CD pipeline is configured in `.github/workflows/ci-cd.yml`. It:

1. Runs tests on every push
2. Builds and pushes Docker images on main branch
3. Deploys to Kubernetes on main branch

To enable CI/CD, configure the following secrets in GitHub:

- `KUBE_CONFIG`: Base64-encoded kubeconfig file
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

## Rollback

```bash
# Check rollout history
kubectl rollout history deployment/api-gateway -n travel-ai

# Rollback to previous version
kubectl rollout undo deployment/api-gateway -n travel-ai

# Rollback to specific revision
kubectl rollout undo deployment/api-gateway --to-revision=2 -n travel-ai
```

## Backup and Restore

### Database Backup

```bash
# PostgreSQL
kubectl exec postgres-0 -n travel-ai -- pg_dump -U travel travel_db > backup.sql

# Cassandra
kubectl exec cassandra-0 -n travel-ai -- nodetool snapshot
```

### Restore

```bash
# PostgreSQL
kubectl exec -i postgres-0 -n travel-ai -- psql -U travel travel_db < backup.sql
```

## Security

### Update Secrets

```bash
# Update secret
kubectl create secret generic travel-secrets --from-literal=OPENAI_API_KEY=new-key --dry-run=client -o yaml | kubectl apply -f -n travel-ai

# Restart services to pick up new secrets
kubectl rollout restart deployment --all -n travel-ai
```

### Enable Network Policies

```bash
kubectl apply -f k8s/network-policies.yaml
```

## Performance Tuning

### Database Connection Pooling

Adjust connection pool sizes in service configurations based on load.

### Cache Configuration

Increase Redis memory limit for higher cache hit rates.

### Elasticsearch

Adjust JVM heap size based on available memory:
```yaml
- name: "ES_JAVA_OPTS"
  value: "-Xms4g -Xmx4g"
```

## Production Checklist

- [ ] Enable HTTPS with TLS certificates
- [ ] Configure domain name and DNS
- [ ] Set up monitoring alerts
- [ ] Configure log aggregation (ELK stack)
- [ ] Enable network policies
- [ ] Configure backup strategy
- [ ] Set up disaster recovery
- [ ] Enable rate limiting
- [ ] Configure WAF rules
- [ ] Enable audit logging
- [ ] Set up secrets rotation
- [ ] Configure CDN for static assets
- [ ] Enable multi-region deployment

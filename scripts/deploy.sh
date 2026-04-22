#!/bin/bash

# Travel AI Agent Platform - Deployment Script

set -e

NAMESPACE="travel-ai"

echo "🚀 Deploying Travel AI Agent Platform to Kubernetes..."

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply config and secrets
echo "🔧 Applying configuration..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml

# Deploy infrastructure
echo "🏗️  Deploying infrastructure..."
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/elasticsearch.yaml
kubectl apply -f k8s/kafka.yaml
kubectl apply -f k8s/cassandra.yaml

# Wait for infrastructure to be ready
echo "⏳ Waiting for infrastructure to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=elasticsearch -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=kafka -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=ready pod -l app=cassandra -n $NAMESPACE --timeout=300s

# Deploy services
echo "🔌 Deploying microservices..."
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

# Deploy monitoring
echo "📊 Deploying monitoring..."
kubectl apply -f k8s/monitoring.yaml

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=available deployment/api-gateway -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/search-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/booking-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/inventory-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/payment-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/user-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/rag-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/mcp-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/notification-service -n $NAMESPACE --timeout=300s
kubectl wait --for=condition=available deployment/frontend -n $NAMESPACE --timeout=300s

echo "✅ Deployment complete!"
echo ""
echo "📋 Service URLs:"
kubectl get svc -n $NAMESPACE
echo ""
echo "🔍 Check pod status:"
kubectl get pods -n $NAMESPACE

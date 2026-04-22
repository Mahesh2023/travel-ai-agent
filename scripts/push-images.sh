#!/bin/bash

# Push Docker images to registry

set -e

REGISTRY="ghcr.io/travel-ai"
VERSION="latest"

echo "📤 Pushing Docker images to ${REGISTRY}..."

# Push all images
docker push ${REGISTRY}/gateway:${VERSION}
docker push ${REGISTRY}/search-service:${VERSION}
docker push ${REGISTRY}/booking-service:${VERSION}
docker push ${REGISTRY}/inventory-service:${VERSION}
docker push ${REGISTRY}/payment-service:${VERSION}
docker push ${REGISTRY}/user-service:${VERSION}
docker push ${REGISTRY}/rag-service:${VERSION}
docker push ${REGISTRY}/mcp-service:${VERSION}
docker push ${REGISTRY}/notification-service:${VERSION}
docker push ${REGISTRY}/frontend:${VERSION}

echo "✅ All images pushed successfully!"

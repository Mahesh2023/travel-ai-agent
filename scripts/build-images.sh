#!/bin/bash

# Build Docker images for all services

set -e

REGISTRY="ghcr.io/travel-ai"
VERSION="latest"

echo "🔨 Building Docker images..."

# Build gateway
echo "Building gateway..."
docker build -f backend/Dockerfile.gateway -t ${REGISTRY}/gateway:${VERSION} ./backend

# Build search service
echo "Building search service..."
docker build -f backend/Dockerfile.search -t ${REGISTRY}/search-service:${VERSION} ./backend

# Build booking service
echo "Building booking service..."
docker build -f backend/Dockerfile.booking -t ${REGISTRY}/booking-service:${VERSION} ./backend

# Build inventory service
echo "Building inventory service..."
docker build -f backend/Dockerfile.inventory -t ${REGISTRY}/inventory-service:${VERSION} ./backend

# Build payment service
echo "Building payment service..."
docker build -f backend/Dockerfile.payment -t ${REGISTRY}/payment-service:${VERSION} ./backend

# Build user service
echo "Building user service..."
docker build -f backend/Dockerfile.user -t ${REGISTRY}/user-service:${VERSION} ./backend

# Build RAG service
echo "Building RAG service..."
docker build -f backend/Dockerfile.rag -t ${REGISTRY}/rag-service:${VERSION} ./backend

# Build MCP service
echo "Building MCP service..."
docker build -f backend/Dockerfile.mcp -t ${REGISTRY}/mcp-service:${VERSION} ./backend

# Build notification service
echo "Building notification service..."
docker build -f backend/Dockerfile.notification -t ${REGISTRY}/notification-service:${VERSION} ./backend

# Build frontend
echo "Building frontend..."
docker build -f frontend/Dockerfile -t ${REGISTRY}/frontend:${VERSION} ./frontend

echo "✅ All images built successfully!"

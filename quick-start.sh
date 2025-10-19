#!/bin/bash

echo "MASINA-DOCK QUICK START"
echo ""
echo "Pulling pre-built Docker image..."
docker-compose pull
echo ""
echo "Starting application..."
docker-compose up -d
echo ""
echo "Waiting for application to start..."
sleep 5
echo ""
echo "APPLICATION STARTED!"
echo "Access at: http://localhost:5000"
echo ""
docker-compose ps

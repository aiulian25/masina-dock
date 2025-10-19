#!/bin/bash

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/docker-images"

mkdir -p "$BACKUP_DIR"

echo "Backing up Docker image..."
echo ""

IMAGE_NAME="masina-dock_masina-dock"
IMAGE_FILE="$BACKUP_DIR/masina-dock-image-$TIMESTAMP.tar"

docker save -o "$IMAGE_FILE" "$IMAGE_NAME" 2>/dev/null || docker save -o "$IMAGE_FILE" masina-dock:latest

if [ -f "$IMAGE_FILE" ]; then
    echo "Compressing image..."
    gzip "$IMAGE_FILE"
    IMAGE_FILE="$IMAGE_FILE.gz"
    
    SIZE=$(du -h "$IMAGE_FILE" | cut -f1)
    echo ""
    echo "Docker image backup completed!"
    echo "File: $IMAGE_FILE"
    echo "Size: $SIZE"
    echo ""
    echo "To restore this image:"
    echo "  gunzip -c $IMAGE_FILE | docker load"
else
    echo "Error: Could not save Docker image"
    exit 1
fi

#!/bin/bash

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="backups/backup-$TIMESTAMP"

echo "=========================================="
echo "MASINA-DOCK COMPLETE BACKUP SYSTEM"
echo "=========================================="
echo "Timestamp: $TIMESTAMP"
echo ""

mkdir -p "$BACKUP_DIR"

echo "STEP 1: Backing up database..."
docker-compose exec -T masina-dock cp /app/backend/vehicles.db /app/backend/vehicles_backup.db 2>/dev/null || true
docker cp masina-dock:/app/backend/vehicles.db "$BACKUP_DIR/vehicles.db" 2>/dev/null || true
cp backend/vehicles.db "$BACKUP_DIR/vehicles.db" 2>/dev/null || true
echo "  Database backed up"

echo ""
echo "STEP 2: Backing up uploads folder..."
cp -r uploads "$BACKUP_DIR/" 2>/dev/null || true
UPLOAD_COUNT=$(find uploads -type f 2>/dev/null | wc -l)
echo "  $UPLOAD_COUNT files backed up"

echo ""
echo "STEP 3: Backing up configuration files..."
cp docker-compose.yml "$BACKUP_DIR/"
cp Dockerfile "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/" 2>/dev/null || true
cp README.md "$BACKUP_DIR/" 2>/dev/null || true
echo "  Configuration files backed up"

echo ""
echo "STEP 4: Backing up application files..."
cp -r backend "$BACKUP_DIR/"
cp -r frontend "$BACKUP_DIR/"
echo "  Application files backed up"

echo ""
echo "STEP 5: Backing up Docker image..."
IMAGE_NAME="masina-dock_masina-dock"
IMAGE_FILE="$BACKUP_DIR/docker-image-masina-dock.tar"
echo "  Saving Docker image: $IMAGE_NAME"
docker save -o "$IMAGE_FILE" "$IMAGE_NAME" 2>/dev/null || docker save -o "$IMAGE_FILE" masina-dock:latest 2>/dev/null || echo "  Warning: Could not save Docker image"
if [ -f "$IMAGE_FILE" ]; then
    IMAGE_SIZE=$(du -h "$IMAGE_FILE" | cut -f1)
    echo "  Docker image saved: $IMAGE_SIZE"
fi

echo ""
echo "STEP 6: Backing up Docker volumes..."
docker run --rm -v masina-dock_masina-data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar czf /backup/docker-volumes.tar.gz -C /data . 2>/dev/null || echo "  No volumes to backup"

echo ""
echo "STEP 7: Creating compressed archive..."
cd backups
tar -czf "masina-dock-complete-$TIMESTAMP.tar.gz" "backup-$TIMESTAMP" --exclude='*.tar'
cd ..

echo ""
echo "STEP 8: Creating Docker image compressed backup..."
if [ -f "$IMAGE_FILE" ]; then
    gzip "$IMAGE_FILE"
    echo "  Docker image compressed"
fi

ARCHIVE_SIZE=$(du -h "backups/masina-dock-complete-$TIMESTAMP.tar.gz" | cut -f1)

echo ""
echo "=========================================="
echo "BACKUP COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
echo "Backup details:"
echo "  Directory:      $BACKUP_DIR"
echo "  Archive:        backups/masina-dock-complete-$TIMESTAMP.tar.gz"
echo "  Archive size:   $ARCHIVE_SIZE"
if [ -f "$BACKUP_DIR/docker-image-masina-dock.tar.gz" ]; then
    IMAGE_BACKUP_SIZE=$(du -h "$BACKUP_DIR/docker-image-masina-dock.tar.gz" | cut -f1)
    echo "  Docker image:   $IMAGE_BACKUP_SIZE"
fi
echo ""
echo "What was backed up:"
echo "  - Database (vehicles.db)"
echo "  - Uploaded files (uploads/)"
echo "  - Configuration files"
echo "  - Application source code"
echo "  - Docker image"
echo "  - Docker volumes"
echo ""
echo "To restore from this backup:"
echo "  ./restore-complete.sh $TIMESTAMP"
echo ""

ls -lh "backups/masina-dock-complete-$TIMESTAMP.tar.gz"

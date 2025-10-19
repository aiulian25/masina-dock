#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: ./restore-complete.sh TIMESTAMP"
    echo ""
    echo "Available backups:"
    ls -1 backups/masina-dock-complete-*.tar.gz 2>/dev/null | sed 's/backups\/masina-dock-complete-/  /' | sed 's/.tar.gz//'
    exit 1
fi

TIMESTAMP=$1
BACKUP_ARCHIVE="backups/masina-dock-complete-$TIMESTAMP.tar.gz"
BACKUP_DIR="backups/backup-$TIMESTAMP"

if [ ! -f "$BACKUP_ARCHIVE" ]; then
    echo "Error: Backup file not found: $BACKUP_ARCHIVE"
    exit 1
fi

echo "=========================================="
echo "MASINA-DOCK COMPLETE RESTORE"
echo "=========================================="
echo "Restoring from backup: $TIMESTAMP"
echo ""
echo "WARNING: This will overwrite all current data!"
echo ""
read -p "Type 'RESTORE' to continue: " confirm
if [ "$confirm" != "RESTORE" ]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "STEP 1: Stopping Docker containers..."
docker-compose down

echo ""
echo "STEP 2: Extracting backup archive..."
tar -xzf "$BACKUP_ARCHIVE" -C backups/

echo ""
echo "STEP 3: Restoring database..."
cp "$BACKUP_DIR/vehicles.db" backend/vehicles.db
echo "  Database restored"

echo ""
echo "STEP 4: Restoring uploads..."
rm -rf uploads
cp -r "$BACKUP_DIR/uploads" .
echo "  Uploads restored"

echo ""
echo "STEP 5: Restoring configuration files..."
cp "$BACKUP_DIR/docker-compose.yml" .
cp "$BACKUP_DIR/Dockerfile" .
cp "$BACKUP_DIR/.env" . 2>/dev/null || true
echo "  Configuration restored"

echo ""
echo "STEP 6: Restoring application files..."
rm -rf backend frontend
cp -r "$BACKUP_DIR/backend" .
cp -r "$BACKUP_DIR/frontend" .
echo "  Application files restored"

echo ""
echo "STEP 7: Restoring Docker image..."
if [ -f "$BACKUP_DIR/docker-image-masina-dock.tar.gz" ]; then
    echo "  Loading Docker image..."
    gunzip -c "$BACKUP_DIR/docker-image-masina-dock.tar.gz" | docker load
    echo "  Docker image restored"
else
    echo "  No Docker image found, will rebuild..."
fi

echo ""
echo "STEP 8: Restoring Docker volumes..."
if [ -f "$BACKUP_DIR/docker-volumes.tar.gz" ]; then
    docker volume create masina-dock_masina-data 2>/dev/null || true
    docker run --rm -v masina-dock_masina-data:/data -v "$PWD/$BACKUP_DIR":/backup alpine tar xzf /backup/docker-volumes.tar.gz -C /data
    echo "  Volumes restored"
fi

echo ""
echo "STEP 9: Starting application..."
docker-compose up -d --build

echo ""
echo "Waiting for application to start..."
sleep 10

echo ""
echo "=========================================="
echo "RESTORE COMPLETED SUCCESSFULLY!"
echo "=========================================="
echo ""
docker-compose ps
echo ""
echo "Application should be available at: http://localhost:5000"

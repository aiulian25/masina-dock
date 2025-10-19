#!/bin/bash

echo "=========================================="
echo "MASINA-DOCK BACKUP LIST"
echo "=========================================="
echo ""

echo "Complete backups:"
ls -lh backups/masina-dock-complete-*.tar.gz 2>/dev/null | awk '{print "  " $9 "  (" $5 ")"}'
echo ""

echo "Docker image backups:"
ls -lh backups/docker-images/*.tar.gz 2>/dev/null | awk '{print "  " $9 "  (" $5 ")"}'
echo ""

echo "Backup directories:"
ls -d backups/backup-* 2>/dev/null | awk '{print "  " $1}'
echo ""

TOTAL_SIZE=$(du -sh backups 2>/dev/null | cut -f1)
echo "Total backup storage used: $TOTAL_SIZE"

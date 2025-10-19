#!/bin/bash
set -e

echo "Starting Masina-Dock initialization..."

# Create directories
mkdir -p /app/data /app/uploads/attachments

# Set permissions so database can be written
chmod -R 777 /app/data /app/uploads

# Initialize database
echo "Initializing database..."
cd /app/backend
python init_db.py

# Set database file permissions
if [ -f /app/data/masina_dock.db ]; then
    chmod 666 /app/data/masina_dock.db
    echo "Database initialized successfully"
else
    echo "Warning: Database file not found after initialization"
fi

# Start application
echo "Starting Gunicorn server..."
exec gunicorn --reload --bind 0.0.0.0:5000 --workers 4 --timeout 120 --access-logfile - --error-logfile - app:app

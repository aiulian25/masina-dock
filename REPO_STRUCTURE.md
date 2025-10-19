# Repository Structure

## Essential Files (on GitHub)

### Application Core
- backend/ - Flask application code
- frontend/ - Web interface (HTML, CSS, JS)
- uploads/ - File upload directory

### Docker Configuration
- docker-compose.yml - Production deployment
- docker-compose.build.yml - Build from source
- Dockerfile - Docker image definition

### Scripts
- backup-complete.sh - Complete system backup
- restore-complete.sh - Restore from backup
- backup-docker-image-only.sh - Docker image backup
- list-backups.sh - List all backups
- backup.sh - Database backup
- restore.sh - Database restore
- setup-auto-backup.sh - Automated backup setup
- quick-start.sh - Quick installation script
- init-fresh-install.sh - Initialize directories
- push-to-ghcr.sh - Push to GitHub Container Registry
- setup-ghcr-deployment.sh - GHCR deployment setup

### Documentation
- README.md - Main documentation
- INSTALL.md - Installation guide
- .gitignore - Git ignore rules

### Screenshots
- screenshots/ - Application screenshots

## Excluded Files (local only)

### Build Artifacts
- AppDir/, AppImage/ - AppImage build files
- appimagetool-x86_64.AppImage - AppImage tool
- *.AppImage - Built AppImage files
- deb-build/ - Debian package build

### Development
- venv/ - Python virtual environment
- data/ - Local data directory
- backups/ - Local backup files

### Security
- security-reports/ - Security scan reports
- trivy-report.json - Trivy scan results

### Other
- templates/ - Unused template directory
- README - Duplicate readme file

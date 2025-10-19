#!/bin/bash

set -e

APP_NAME="masina-dock"
APP_VERSION="1.0.0"
ARCH="amd64"
BUILD_DIR="deb-build"

echo "Building DEB package for ${APP_NAME} ${APP_VERSION}..."

mkdir -p ${BUILD_DIR}/DEBIAN
mkdir -p ${BUILD_DIR}/opt/${APP_NAME}
mkdir -p ${BUILD_DIR}/usr/share/applications
mkdir -p ${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps
mkdir -p ${BUILD_DIR}/usr/bin

cat > ${BUILD_DIR}/DEBIAN/control << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Masina-Dock Developer <dev@masina-dock.local>
Description: Vehicle Maintenance Records and Fuel Mileage Tracker
 A comprehensive vehicle maintenance and fuel economy tracking application.
 Features include service record management, fuel economy tracking, maintenance
 reminders, and expense analytics with support for multiple vehicles.
Depends: python3 (>= 3.9), python3-pip
EOF

cat > ${BUILD_DIR}/DEBIAN/postinst << 'EOF'
#!/bin/bash
cd /opt/masina-dock
pip3 install -r backend/requirements.txt --target=/opt/masina-dock/pylibs
chmod +x /usr/bin/masina-dock
echo "Masina-Dock installed successfully!"
echo "Run 'masina-dock' to start the application"
EOF

chmod +x ${BUILD_DIR}/DEBIAN/postinst

cp -r backend ${BUILD_DIR}/opt/${APP_NAME}/
cp -r frontend ${BUILD_DIR}/opt/${APP_NAME}/

cat > ${BUILD_DIR}/usr/share/applications/${APP_NAME}.desktop << EOF
[Desktop Entry]
Type=Application
Name=Masina-Dock
Comment=Vehicle Maintenance Tracker
Exec=/usr/bin/masina-dock
Icon=masina-dock
Categories=Utility;
Terminal=false
EOF

cp frontend/static/images/logo.svg ${BUILD_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.svg

cat > ${BUILD_DIR}/usr/bin/${APP_NAME} << 'EOF'
#!/bin/bash
cd /opt/masina-dock
PYTHONPATH=/opt/masina-dock/pylibs:$PYTHONPATH python3 backend/app.py
EOF

chmod +x ${BUILD_DIR}/usr/bin/${APP_NAME}

dpkg-deb --build ${BUILD_DIR} ${APP_NAME}_${APP_VERSION}_${ARCH}.deb

echo "DEB package built successfully: ${APP_NAME}_${APP_VERSION}_${ARCH}.deb"
echo "To install: sudo dpkg -i ${APP_NAME}_${APP_VERSION}_${ARCH}.deb"

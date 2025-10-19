#!/bin/bash

set -e

APP_NAME="masina-dock"
APP_VERSION="1.0.0"
ARCH="x86_64"

echo "Building AppImage for ${APP_NAME} ${APP_VERSION}..."

mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/lib
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

cp -r backend AppDir/
cp -r frontend AppDir/
cp AppImage/AppRun AppDir/
cp AppImage/masina-dock.desktop AppDir/usr/share/applications/
cp frontend/static/images/logo.svg AppDir/usr/share/icons/hicolor/256x256/apps/masina-dock.svg

chmod +x AppDir/AppRun

python3 -m venv AppDir/usr
source AppDir/usr/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
deactivate

wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-${ARCH}.AppImage
chmod +x appimagetool-${ARCH}.AppImage

./appimagetool-${ARCH}.AppImage AppDir ${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage

echo "AppImage built successfully: ${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo "To run: ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

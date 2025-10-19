#!/bin/bash

echo "=========================================="
echo "PUSH DOCKER IMAGE TO GITHUB REGISTRY"
echo "=========================================="
echo ""

GITHUB_USERNAME="aiulian25"
IMAGE_NAME="masina-dock"
VERSION="latest"

echo "Step 1: Login to GitHub Container Registry"
echo "You need a Personal Access Token with 'write:packages' scope"
echo ""
read -p "Enter your GitHub Personal Access Token: " GITHUB_TOKEN

echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin

if [ $? -ne 0 ]; then
    echo "Login failed. Please check your token."
    exit 1
fi

echo ""
echo "Step 2: Tag the Docker image"
docker tag masina-dock_masina-dock "ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$VERSION"
docker tag masina-dock_masina-dock "ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$(date +%Y%m%d)"

echo ""
echo "Step 3: Push to GitHub Container Registry"
docker push "ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$VERSION"
docker push "ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$(date +%Y%m%d)"

echo ""
echo "=========================================="
echo "DOCKER IMAGE PUBLISHED!"
echo "=========================================="
echo ""
echo "Your Docker image is now available at:"
echo "  ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$VERSION"
echo ""
echo "To use this image on another machine:"
echo "  docker pull ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$VERSION"
echo "  docker run -p 5000:5000 ghcr.io/$GITHUB_USERNAME/$IMAGE_NAME:$VERSION"
echo ""
echo "Make the package public:"
echo "1. Go to https://github.com/users/$GITHUB_USERNAME/packages/container/$IMAGE_NAME/settings"
echo "2. Scroll to 'Danger Zone'"
echo "3. Click 'Change visibility' and select 'Public'"

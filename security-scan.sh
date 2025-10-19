#!/bin/bash

echo "Masina-Dock Security Scan"
echo "========================="
echo ""

# Get image name
IMAGE_NAME="masina-dock_masina-dock:latest"

echo "Scanning Docker image: ${IMAGE_NAME}"
echo ""

# Check if Trivy is installed
if ! command -v trivy &> /dev/null; then
    echo "Trivy is not installed. Please install it first."
    exit 1
fi

# Create reports directory
mkdir -p security-reports

# Scan for HIGH and CRITICAL vulnerabilities
echo "Scanning for HIGH and CRITICAL vulnerabilities..."
trivy image --severity HIGH,CRITICAL --format table ${IMAGE_NAME} | tee security-reports/critical-scan.txt

echo ""
echo "Scanning for all vulnerabilities..."
trivy image --format table ${IMAGE_NAME} | tee security-reports/full-scan.txt

echo ""
echo "Generating JSON report..."
trivy image --format json --output security-reports/vulnerability-report.json ${IMAGE_NAME}

echo ""
echo "Scanning configuration files..."
trivy config . --format table | tee security-reports/config-scan.txt

echo ""
echo "Security scan complete!"
echo "Reports saved in: security-reports/"
echo ""
echo "Summary:"
grep "Total:" security-reports/critical-scan.txt || echo "No summary available"

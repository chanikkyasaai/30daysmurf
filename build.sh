#!/bin/bash
# Build script for Render.com deployment

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p static/generated_images
mkdir -p uploads

echo "Build completed successfully!"

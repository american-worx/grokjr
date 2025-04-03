#!/bin/bash

echo "Setting up Grok Jr. environment..."

# Check for Python and pip
if ! command -v python3 &> /dev/null; then
    echo "Python3 not found. Please install Python3 and try again."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "pip3 not found. Please install pip3 and try again."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check for system dependencies
echo "Checking for system dependencies..."

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for Nvidia drivers (for RTX 3050)
if ! command -v nvidia-smi &> /dev/null; then
    echo "Nvidia drivers not found. Please install Nvidia drivers: https://www.nvidia.com/Download/index.aspx"
    exit 1
fi

# Create speech directory if it doesn't exist
mkdir -p speech

# Placeholder for model download (gemma-3-1b-it)
echo "Model download will be implemented in a later milestone."

# Placeholder for database initialization (SQLite, Qdrant)
echo "Database initialization will be implemented in Task 4."

echo "Setup complete! You can now run Grok Jr."
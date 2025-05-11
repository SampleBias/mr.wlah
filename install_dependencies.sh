#!/bin/bash

# Mr. Wlah - Dependencies Installation Script

echo "Installing Mr. Wlah dependencies..."

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Install google-genai with -q flag (quiet mode)
echo "Installing Google Genai package..."
pip install -q -U google-genai

# Install all other dependencies from requirements.txt
echo "Installing remaining dependencies..."
pip install -U -r requirements.txt

echo "Installation complete!" 
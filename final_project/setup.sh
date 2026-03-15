#!/bin/bash

echo "=================================================="
echo "E-Commerce Recommendation System - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=================================================="
echo "Setup complete!"
echo "=================================================="
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open index.html in your browser"
echo ""
echo "Demo login credentials:"
echo "  Username: demo"
echo "  Password: demo123"
echo ""
echo "=================================================="

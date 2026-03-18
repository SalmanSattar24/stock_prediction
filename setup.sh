#!/bin/bash
# Quick Setup Script for Stock Signal System
# This script helps you get up and running quickly

set -e

echo "======================================"
echo "Stock Signal System - Quick Setup"
echo "======================================"
echo ""

# Check Python is installed
if ! command -v python &> /dev/null; then
    echo "❌ Python is not installed"
    exit 1
fi

python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python $python_version found"
echo ""

# Step 1: Create virtual environment (optional but recommended)
if [ ! -d "venv" ]; then
    echo "1️⃣  Creating virtual environment..."
    python -m venv venv
    echo "✓ Virtual environment created"
    echo "→ Activate with: source venv/bin/activate (Mac/Linux) or venv\Scripts\activate (Windows)"
fi
echo ""

# Step 2: Install dependencies
echo "2️⃣  Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Step 3: Create .env file
echo "3️⃣  Setting up API keys..."
if [ ! -f ".env" ]; then
    echo "Creating .env file template..."
    python config.py --setup
else
    echo ".env file already exists"
fi
echo "✓ Configuration ready"
echo ""

# Step 4: Validate setup
echo "4️⃣  Validating configuration..."
python config.py --validate
echo ""

echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Read SETUP_INSTRUCTIONS.md for Reddit setup"
echo "3. Run: python test_system.py"
echo "4. Check SYSTEM_GUIDE.md for usage examples"
echo ""
echo "Need help?"
echo "• SETUP_INSTRUCTIONS.md - API key configuration"
echo "• SYSTEM_GUIDE.md - System overview and examples"
echo "• IMPLEMENTATION_SUMMARY.md - What was built"

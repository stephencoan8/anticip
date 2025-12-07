#!/bin/bash

# Installation and Setup Script for Anticip Security Updates
# Run this script to apply all security and performance fixes

echo "🔒 Anticip Security & Performance Update Installation"
echo "======================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create logs directory
echo ""
echo "📁 Creating logs directory..."
mkdir -p logs
echo "✓ Logs directory created"

# Install/upgrade dependencies
echo ""
echo "📦 Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Error installing dependencies"
    exit 1
fi

# Check for .env file
echo ""
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "🔑 IMPORTANT: You must set your SECRET_KEY in .env"
    echo "   Generate one with:"
    echo "   python3 -c 'import secrets; print(secrets.token_hex(32))'"
    echo ""
    echo "   Then edit .env and paste the generated key"
else
    echo "✓ .env file exists"
    
    # Check if SECRET_KEY is set
    if grep -q "SECRET_KEY=your_secret_key_here" .env; then
        echo ""
        echo "⚠️  WARNING: SECRET_KEY is still set to default value!"
        echo "   Generate a new one with:"
        echo "   python3 -c 'import secrets; print(secrets.token_hex(32))'"
        echo ""
    else
        echo "✓ SECRET_KEY appears to be configured"
    fi
fi

# Summary
echo ""
echo "======================================================"
echo "✅ Installation Complete!"
echo ""
echo "📋 Next Steps:"
echo "   1. Verify your .env file has a proper SECRET_KEY"
echo "   2. Update other environment variables as needed"
echo "   3. Test locally: python3 wsgi.py"
echo "   4. Or with Gunicorn: gunicorn --workers=2 --bind=0.0.0.0:5004 wsgi:app"
echo ""
echo "🔍 Check IMPLEMENTATION_SUMMARY.md for full details"
echo "======================================================"

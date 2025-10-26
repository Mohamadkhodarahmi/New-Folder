#!/bin/bash

# Setup script for Trading Signal Bot
echo "🤖 Trading Signal Bot - Setup"
echo "=============================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1)
echo "✓ Found Python: $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create config file if it doesn't exist
if [ ! -f "config.env" ]; then
    echo ""
    echo "⚙️  Creating configuration file..."
    cp config.env.example config.env
    echo "✓ config.env created"
    echo "⚠️  Please edit config.env and add your Telegram bot token!"
else
    echo ""
    echo "✓ config.env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.env and add your TELEGRAM_BOT_TOKEN"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python main.py"
echo ""


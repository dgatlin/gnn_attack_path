#!/bin/bash

# Setup script for GNN Attack Path Demo environment

echo "🛡️  GNN Attack Path Demo - Environment Setup"
echo "============================================="

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Copy env.example to .env
echo "📋 Copying env.example to .env..."
cp env.example .env

echo "✅ Environment file created: .env"
echo ""
echo "🔑 Next steps:"
echo "1. Edit .env file and add your OpenAI API key:"
echo "   OPENAI_API_KEY=your_actual_api_key_here"
echo ""
echo "2. Get your API key from: https://platform.openai.com/api-keys"
echo ""
echo "3. Start the demo:"
echo "   python test_api.py && cd ui && npm start"
echo ""
echo "📝 Note: .env file is gitignored and will not be committed to the repository"

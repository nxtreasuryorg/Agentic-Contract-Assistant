#!/bin/bash

# Automated Mermaid PNG Generator Script for Contract-Agent
# This script generates PNG files from all Mermaid diagrams

echo "🚀 Starting Mermaid PNG Generation for Contract-Agent"

# Define directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIAGRAMS_DIR="$SCRIPT_DIR"  # Current directory (docs/diagrams)
PNG_DIR="$SCRIPT_DIR/../png"  # ../png from diagrams directory

# Create PNG directory if it doesn't exist
mkdir -p "$PNG_DIR"
echo "📁 PNG output directory: $PNG_DIR"

# Check if Mermaid CLI is available
if command -v mmdc >/dev/null 2>&1; then
    echo "✅ Mermaid CLI detected"
    CLI_AVAILABLE=true
else
    echo "❌ Mermaid CLI not found"
    echo "💡 Install with: npm install -g @mermaid-js/mermaid-cli"
    CLI_AVAILABLE=false
fi

# Define diagram files
declare -a DIAGRAMS=(
    "01_high_level_architecture.mmd:High-Level System Architecture"
    "02_actor_critic_workflow.mmd:Actor-Critic Workflow"
    "03_chunked_processing.mmd:Chunked Processing Workflow"
    "04_class_diagram.mmd:Class Diagram"
    "05_data_flow.mmd:Data Flow Diagram"
    "06_state_machine.mmd:Job State Machine"
    "07_feedback_loop.mmd:Actor-Critic Feedback Loop"
)

SUCCESS_COUNT=0
TOTAL_COUNT=${#DIAGRAMS[@]}

# Generate PNGs
for diagram_info in "${DIAGRAMS[@]}"; do
    IFS=':' read -r mmd_file diagram_name <<< "$diagram_info"
    
    mermaid_path="$DIAGRAMS_DIR/$mmd_file"
    png_filename="${mmd_file%.mmd}.png"
    png_path="$PNG_DIR/$png_filename"
    
    echo ""
    echo "📊 Processing: $diagram_name"
    
    if [[ ! -f "$mermaid_path" ]]; then
        echo "❌ Mermaid file not found: $mermaid_path"
        continue
    fi
    
    if [[ "$CLI_AVAILABLE" == true ]]; then
        # Use Mermaid CLI
        if mmdc -i "$mermaid_path" -o "$png_path" -w 1400 -H 1000 --backgroundColor white >/dev/null 2>&1; then
            echo "✅ Generated: $png_filename"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        else
            echo "❌ Failed to generate: $png_filename"
        fi
    else
        echo "⚠️  Skipping $png_filename (CLI not available)"
    fi
done

echo ""
echo "🎯 Generation Complete!"
echo "✅ Successfully generated: $SUCCESS_COUNT/$TOTAL_COUNT diagrams"
echo "📁 PNG files saved to: $PNG_DIR"

if [[ $SUCCESS_COUNT -lt $TOTAL_COUNT ]]; then
    echo ""
    echo "💡 Alternative generation methods:"
    echo "1. Install Mermaid CLI: npm install -g @mermaid-js/mermaid-cli"
    echo "2. Run Python script: python3 generate_mermaid_pngs.py"
    echo "3. Manual generation at: https://mermaid.live/"
    echo "4. Use VS Code Mermaid extension"
fi

# List generated files
if [[ $SUCCESS_COUNT -gt 0 ]]; then
    echo ""
    echo "📋 Generated PNG files:"
    ls -la "$PNG_DIR"/*.png 2>/dev/null || echo "No PNG files found"
fi

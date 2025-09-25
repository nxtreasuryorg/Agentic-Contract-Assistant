# Automated PNG Generation Instructions

I've created **3 different scripts** to automatically generate PNG files from all Mermaid diagrams and save them to `/home/ec2-user/cb/Contract-Agent/docs/png/`.

## 🚀 Quick Start Options

### Option 1: Bash Script (Recommended if you have Node.js/npm)
```bash
# First, install Mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Then run the script from diagrams directory
cd /home/ec2-user/cb/Contract-Agent/docs/diagrams
./generate_pngs.sh
```

### Option 2: Python Script (Web automation approach)
```bash
# Install required Python packages
pip install selenium webdriver-manager

# Run the Python script from diagrams directory
cd /home/ec2-user/cb/Contract-Agent/docs/diagrams
python3 generate_mermaid_pngs.py
```

### Option 3: Node.js Script (Browser automation)
```bash
# Install required Node.js packages
npm install puppeteer

# Run the Node.js script from diagrams directory
cd /home/ec2-user/cb/Contract-Agent/docs/diagrams
node generate_pngs.js
```

## 📁 What Gets Generated

All scripts will create PNG files in `/home/ec2-user/cb/Contract-Agent/docs/png/`:

- `01_high_level_architecture.png` - System overview
- `02_actor_critic_workflow.png` - Single document processing
- `03_chunked_processing.png` - Large document processing  
- `04_class_diagram.png` - Component relationships
- `05_data_flow.png` - End-to-end data flow
- `06_state_machine.png` - Job lifecycle states
- `07_feedback_loop.png` - Actor-critic refinement process

## 🎯 Script Comparison

| Method | Pros | Cons | Requirements |
|--------|------|------|--------------|
| **Bash + CLI** | Fast, reliable, high quality | Needs Node.js/npm | `@mermaid-js/mermaid-cli` |
| **Python + Selenium** | Cross-platform, no CLI needed | Slower, needs browser driver | `selenium`, `webdriver-manager` |
| **Node.js + Puppeteer** | Good control, handles modern web | Needs Node.js environment | `puppeteer` |

## 🔧 Troubleshooting

### If Mermaid CLI fails:
```bash
# Check if installed
mmdc --version

# If not installed
npm install -g @mermaid-js/mermaid-cli

# If permission issues
sudo npm install -g @mermaid-js/mermaid-cli
```

### If Python script fails:
```bash
# Install missing packages
pip install selenium webdriver-manager

# For Ubuntu/Debian systems, may need:
sudo apt-get install chromium-browser chromium-chromedriver
```

### If Node.js script fails:
```bash
# Install puppeteer
npm install puppeteer

# If puppeteer install fails
npm install puppeteer --unsafe-perm=true --allow-root
```

## 📊 Expected Output

When successful, you'll see:
```
🚀 Starting Mermaid PNG Generation for Contract-Agent
📁 PNG output directory: /home/ec2-user/cb/Contract-Agent/docs/png
📊 Processing: High-Level System Architecture
✅ Generated: 01_high_level_architecture.png
📊 Processing: Actor-Critic Workflow
✅ Generated: 02_actor_critic_workflow.png
...
🎯 Generation Complete!
✅ Successfully generated: 7/7 diagrams
```

The PNG files will be saved with:
- **High resolution** (1400x1000px)
- **Clean white background**  
- **Professional quality** for presentations/documentation

## 🏃‍♂️ Fastest Method

**For immediate results:**
1. Run: `npm install -g @mermaid-js/mermaid-cli`
2. Run: `cd /home/ec2-user/cb/Contract-Agent/docs/diagrams`
3. Run: `./generate_pngs.sh`
4. Check: `ls -la ../png/`

This will generate all 7 PNG files in under 30 seconds!

#!/usr/bin/env node

/**
 * Automated Mermaid PNG Generator for Contract-Agent Documentation
 * This script generates PNG files from all Mermaid diagrams using Puppeteer
 */

const fs = require('fs');
const path = require('path');
const puppeteer = require('puppeteer');

// Configuration
const DIAGRAMS_DIR = __dirname;  // Current directory (docs/diagrams)
const PNG_DIR = path.join(__dirname, '..', 'png');  // ../png from diagrams directory
const MERMAID_LIVE_URL = 'https://mermaid.live/';

// Diagram files to process
const DIAGRAMS = [
    { file: '01_high_level_architecture.mmd', name: 'High-Level System Architecture' },
    { file: '02_actor_critic_workflow.mmd', name: 'Actor-Critic Workflow' },
    { file: '03_chunked_processing.mmd', name: 'Chunked Processing Workflow' },
    { file: '04_class_diagram.mmd', name: 'Class Diagram' },
    { file: '05_data_flow.mmd', name: 'Data Flow Diagram' },
    { file: '06_state_machine.mmd', name: 'Job State Machine' },
    { file: '07_feedback_loop.mmd', name: 'Actor-Critic Feedback Loop' }
];

async function ensureDirectory(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        console.log(`📁 Created directory: ${dirPath}`);
    }
}

async function generatePNG(browser, mermaidCode, outputPath, diagramName) {
    console.log(`🔄 Generating ${diagramName}...`);
    
    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1400, height: 1000 });
        
        // Navigate to Mermaid Live
        await page.goto(MERMAID_LIVE_URL, { waitUntil: 'networkidle0' });
        
        // Wait for the editor to load
        await page.waitForSelector('.cm-content', { timeout: 10000 });
        
        // Clear existing content and input new diagram
        await page.click('.cm-content');
        await page.keyboard.down('Control');
        await page.keyboard.press('KeyA');
        await page.keyboard.up('Control');
        await page.keyboard.press('Delete');
        
        // Wait a bit and then type the mermaid code
        await page.waitForTimeout(1000);
        await page.type('.cm-content', mermaidCode);
        
        // Wait for diagram to render
        await page.waitForSelector('svg', { timeout: 15000 });
        await page.waitForTimeout(2000);
        
        // Find and click download button
        const downloadButton = await page.waitForSelector('button[title*="download"], [data-testid="download"]', { timeout: 5000 });
        await downloadButton.click();
        
        // Wait for PNG option and click it
        await page.waitForTimeout(1000);
        const pngOption = await page.waitForSelector('button:contains("PNG"), div:contains("PNG")', { timeout: 5000 });
        await pngOption.click();
        
        // Wait for download to complete
        await page.waitForTimeout(3000);
        
        await page.close();
        console.log(`✅ Generated: ${diagramName}`);
        return true;
        
    } catch (error) {
        console.error(`❌ Failed to generate ${diagramName}: ${error.message}`);
        return false;
    }
}

async function main() {
    console.log('🚀 Starting Mermaid PNG Generation for Contract-Agent');
    
    // Ensure directories exist
    await ensureDirectory(PNG_DIR);
    
    let browser;
    try {
        // Launch browser
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
        });
        
        let successCount = 0;
        
        for (const diagram of DIAGRAMS) {
            const mermaidPath = path.join(DIAGRAMS_DIR, diagram.file);
            const pngPath = path.join(PNG_DIR, diagram.file.replace('.mmd', '.png'));
            
            // Check if mermaid file exists
            if (!fs.existsSync(mermaidPath)) {
                console.error(`❌ Mermaid file not found: ${mermaidPath}`);
                continue;
            }
            
            // Read mermaid content
            const mermaidCode = fs.readFileSync(mermaidPath, 'utf8');
            
            // Generate PNG
            const success = await generatePNG(browser, mermaidCode, pngPath, diagram.name);
            if (success) {
                successCount++;
            }
        }
        
        console.log('\n🎯 Generation Complete!');
        console.log(`✅ Successfully generated: ${successCount}/${DIAGRAMS.length} diagrams`);
        console.log(`📁 PNG files saved to: ${PNG_DIR}`);
        
    } catch (error) {
        console.error('❌ Error during generation:', error.message);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Check if puppeteer is available
try {
    require.resolve('puppeteer');
    main().catch(console.error);
} catch (error) {
    console.error('❌ Puppeteer not found. Install with: npm install puppeteer');
    console.log('💡 Alternative: Use the Python script or bash script instead');
}

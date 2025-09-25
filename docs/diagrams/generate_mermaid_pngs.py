#!/usr/bin/env python3
"""
Automated Mermaid PNG Generator for Contract-Agent Documentation

This script automatically generates PNG files from all Mermaid diagrams
and saves them to docs/png/ folder.
"""

import os
import time
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def setup_chrome_driver():
    """Setup Chrome driver with headless options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1400,1000")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Chrome driver setup failed: {e}")
        return None

def generate_png_with_mermaid_live(mermaid_code, output_path, diagram_name):
    """Generate PNG using Mermaid Live Editor"""
    driver = setup_chrome_driver()
    if not driver:
        return False
    
    try:
        print(f"🔄 Generating {diagram_name}...")
        
        # Navigate to Mermaid Live
        driver.get("https://mermaid.live/")
        time.sleep(3)
        
        # Find and clear the editor
        try:
            # Try different possible selectors for the editor
            editor_selectors = [
                ".cm-content",
                ".cm-editor .cm-content",
                "div[contenteditable='true']",
                ".monaco-editor textarea",
                ".cm-focused"
            ]
            
            editor = None
            for selector in editor_selectors:
                try:
                    editor = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print(f"✅ Found editor with selector: {selector}")
                    break
                except:
                    continue
            
            if not editor:
                print("❌ Could not find editor element")
                return False
            
            # Clear existing content and input new diagram
            editor.click()
            editor.send_keys(Keys.CONTROL + "a")
            time.sleep(0.5)
            editor.send_keys(Keys.DELETE)
            time.sleep(1)
            editor.send_keys(mermaid_code)
            time.sleep(3)
            
            # Wait for diagram to render
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "svg"))
            )
            
            # Find and click download button
            download_selectors = [
                "[data-testid='download']",
                "button[title*='download']", 
                "button[title*='Download']",
                ".download-btn",
                "button:contains('Download')",
                "[aria-label*='download']"
            ]
            
            download_btn = None
            for selector in download_selectors:
                try:
                    download_btn = driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not download_btn:
                print("❌ Could not find download button")
                return False
            
            download_btn.click()
            time.sleep(2)
            
            # Look for PNG option
            try:
                png_option = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'PNG')] | //div[contains(text(), 'PNG')]"))
                )
                png_option.click()
                time.sleep(2)
                print(f"✅ {diagram_name} PNG generated successfully")
                return True
                
            except Exception as e:
                print(f"❌ Could not find PNG option: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Error interacting with editor: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error generating {diagram_name}: {e}")
        return False
    finally:
        driver.quit()

def generate_png_with_cli(mermaid_file, output_path):
    """Generate PNG using Mermaid CLI (if available)"""
    try:
        cmd = f"mmdc -i {mermaid_file} -o {output_path} -w 1400 -H 1000"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Generated {output_path}")
            return True
        else:
            print(f"❌ CLI generation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Mermaid CLI not available: {e}")
        return False

def check_mermaid_cli():
    """Check if Mermaid CLI is available"""
    try:
        result = subprocess.run("mmdc --version", shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def main():
    """Main function to generate all Mermaid PNGs"""
    print("🚀 Starting Mermaid PNG Generation for Contract-Agent")
    
    # Define paths
    script_dir = Path(__file__).parent
    diagrams_dir = script_dir  # Current directory (docs/diagrams)
    png_dir = script_dir.parent / "png"  # ../png from diagrams directory
    
    # Create PNG directory if it doesn't exist
    png_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 PNG output directory: {png_dir}")
    
    # Define all diagram files
    diagram_files = [
        ("01_high_level_architecture.mmd", "High-Level System Architecture"),
        ("02_actor_critic_workflow.mmd", "Actor-Critic Workflow"),
        ("03_chunked_processing.mmd", "Chunked Processing Workflow"),
        ("04_class_diagram.mmd", "Class Diagram"),
        ("05_data_flow.mmd", "Data Flow Diagram"),
        ("06_state_machine.mmd", "Job State Machine"),
        ("07_feedback_loop.mmd", "Actor-Critic Feedback Loop")
    ]
    
    # Check if Mermaid CLI is available
    has_cli = check_mermaid_cli()
    if has_cli:
        print("✅ Mermaid CLI detected - using CLI method")
        method = "cli"
    else:
        print("⚠️  Mermaid CLI not found - using web automation method")
        print("💡 To install CLI: npm install -g @mermaid-js/mermaid-cli")
        method = "web"
    
    success_count = 0
    total_count = len(diagram_files)
    
    for mmd_file, diagram_name in diagram_files:
        mermaid_path = diagrams_dir / mmd_file
        png_filename = mmd_file.replace('.mmd', '.png')
        png_path = png_dir / png_filename
        
        if not mermaid_path.exists():
            print(f"❌ Mermaid file not found: {mermaid_path}")
            continue
        
        # Read mermaid content
        with open(mermaid_path, 'r', encoding='utf-8') as f:
            mermaid_code = f.read()
        
        print(f"\n📊 Processing: {diagram_name}")
        
        success = False
        if method == "cli":
            success = generate_png_with_cli(mermaid_path, png_path)
        else:
            success = generate_png_with_mermaid_live(mermaid_code, png_path, diagram_name)
        
        if success:
            success_count += 1
            print(f"✅ Saved: {png_path}")
        else:
            print(f"❌ Failed to generate: {png_filename}")
    
    print(f"\n🎯 Generation Complete!")
    print(f"✅ Successfully generated: {success_count}/{total_count} diagrams")
    print(f"📁 PNG files saved to: {png_dir}")
    
    if success_count < total_count:
        print("\n💡 Alternative methods if some failed:")
        print("1. Install Mermaid CLI: npm install -g @mermaid-js/mermaid-cli")
        print("2. Manual generation at: https://mermaid.live/")
        print("3. Use VS Code Mermaid extension")

if __name__ == "__main__":
    main()

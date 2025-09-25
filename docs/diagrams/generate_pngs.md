# Generate PNG Files from Mermaid Diagrams

I've created 7 individual Mermaid diagram files (.mmd) that you can use to generate PNG files.

## Files Created:
1. `01_high_level_architecture.mmd` - System overview
2. `02_actor_critic_workflow.mmd` - Single document processing
3. `03_chunked_processing.mmd` - Large document processing  
4. `04_class_diagram.mmd` - Component relationships
5. `05_data_flow.mmd` - End-to-end data flow
6. `06_state_machine.mmd` - Job lifecycle states
7. `07_feedback_loop.mmd` - Actor-critic refinement process

## Method 1: Using Mermaid Live Editor (Recommended)

**For each .mmd file:**

1. **Open https://mermaid.live/**
2. **Clear the editor content**
3. **Copy the entire content from one .mmd file**  
4. **Paste it into the editor**
5. **Click the download button (📥) in the top toolbar**
6. **Select "PNG" format**
7. **Save with descriptive filename** (e.g., `high_level_architecture.png`)

## Method 2: Using Mermaid CLI (If you have Node.js)

```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate PNG for each diagram
mmdc -i 01_high_level_architecture.mmd -o 01_high_level_architecture.png
mmdc -i 02_actor_critic_workflow.mmd -o 02_actor_critic_workflow.png
mmdc -i 03_chunked_processing.mmd -o 03_chunked_processing.png
mmdc -i 04_class_diagram.mmd -o 04_class_diagram.png
mmdc -i 05_data_flow.mmd -o 05_data_flow.png
mmdc -i 06_state_machine.mmd -o 06_state_machine.png
mmdc -i 07_feedback_loop.mmd -o 07_feedback_loop.png
```

## Method 3: Using VS Code Extension

1. **Install "Mermaid Markdown Syntax Highlighting" extension**
2. **Open each .mmd file**
3. **Right-click → "Mermaid: Export Diagram"**
4. **Choose PNG format**

## Recommended PNG Settings:
- **Width**: 1200-1400px (for good quality)
- **Format**: PNG (best for documentation)
- **Theme**: Default or Forest (professional look)

## Expected Results:
Each diagram should render clearly showing:
- **Architecture flows** with proper connections
- **Sequence interactions** with timeline
- **Class relationships** with clear hierarchies  
- **State transitions** with proper labels
- **Data flow** with decision points

## Troubleshooting:
- If a diagram doesn't render, check the console for syntax errors
- Ensure proper indentation for subgraphs
- Verify all node references are correctly spelled
- Check that arrows use correct syntax (`-->`, `->>`, `-->>`)

## File Organization:
Save PNG files as:
```
docs/diagrams/png/
├── 01_high_level_architecture.png
├── 02_actor_critic_workflow.png  
├── 03_chunked_processing.png
├── 04_class_diagram.png
├── 05_data_flow.png
├── 06_state_machine.png
└── 07_feedback_loop.png
```

This gives you all the Mermaid diagrams ready to generate PNG files using https://mermaid.js.org/ as requested!

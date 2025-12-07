# Complete Toto Automation System - Usage Guide

## 🎯 Overview

This system provides complete end-to-end automation for toto betting, including:
- **Navigation**: Automatic navigation to toto website and round selection
- **Form Filling**: Automated form filling with CSV betting data
- **Cart Management**: Adding bets to cart and handling confirmations
- **GUI Interface**: User-friendly interface for easy operation

## 🚀 Quick Start

### Option 1: Complete Workflow (Recommended)
This is the easiest way to run the complete automation:

1. **Start the GUI**:
   ```bash
   python3 enhanced_gui_automation.py
   ```

2. **Load your CSV file**:
   - Click "Browse" next to "CSV File"
   - Select your betting data CSV file

3. **Run Complete Workflow**:
   - Click the **"Complete Workflow"** button
   - Confirm the automation steps
   - The system will automatically:
     - Navigate to toto website
     - Detect and select the latest round
     - Fill all betting forms
     - Add everything to cart

### Option 2: Step-by-Step Manual Control

1. **Start the GUI**: `python3 enhanced_gui_automation.py`

2. **Load CSV file**: Select your betting data

3. **Navigate to Toto Site**:
   - Click **"Auto Navigation"** for automatic navigation, OR
   - Use manual steps:
     - Click **"Detect"** to find available rounds
     - Select a round from the dropdown
     - Click **"Select"** to choose the round
     - Click **"Start Voting Prediction"** (automatically goes to single voting page)

4. **Process Betting Data**:
   - Use the original automation system to fill forms

## 📊 CSV Data Format

Your CSV file should contain betting data with:
- **13 columns**: One for each game
- **Rows**: Each row represents one betting set
- **Values**: 
  - `0` = Draw (引き分け)
  - `1` = Home Win (ホーム勝ち)  
  - `2` = Away Win (アウェイ勝ち)

Example CSV:
```csv
1,0,2,1,1,0,2,0,1,2,1,0,2
2,1,0,2,0,1,2,1,0,2,0,1,2
0,2,1,0,2,1,0,2,1,0,2,1,0
```

## 🎮 GUI Interface Guide

### Main Tab
- **Automation Mode**: Choose between Basic, Record, or Execute mode
- **File Selection**: Select CSV and action files
- **Toto Round Selection**: 
  - **Detect**: Find available rounds on the page
  - **Select**: Choose a specific round
  - **Start Voting Prediction**: Click "今すぐ投票予想する" and automatically click "シングル" (goes directly to single voting page)
  - **Click Single**: Manual single button click (usually not needed)
  - **Auto Navigation**: Complete automatic navigation (includes all steps)
- **Complete Workflow**: One-click complete automation

### Control Buttons
- **Start Automation**: Original automation system
- **Complete Workflow**: New one-click complete automation
- **Stop**: Stop any running automation

### Status Indicators
- **Round Status**: Shows current round selection status
- **Status Bar**: Shows current operation status
- **Logs**: Real-time logging information

## 🔧 Command Line Usage

### Complete Workflow Script
```bash
# Run complete automation with CSV file
python3 complete_toto_automation.py

# Edit the script to specify your CSV file path
```

### Original Enhanced Automation
```bash
# Basic mode
python3 enhanced_automation.py --mode basic --csv your_data.csv

# With specific URL
python3 enhanced_automation.py --mode basic --csv your_data.csv --url "https://www.toto-dream.com/toto/index.html"
```

## 🎯 Automation Flow

### Complete Workflow Process:
1. **System Initialization**
   - Setup WebDriver (Chrome/Edge browser)
   - Initialize navigation and form filling components

2. **Data Loading**
   - Load and validate CSV betting data
   - Split data into batches (10 sets per batch)

3. **Initial Navigation & Round Selection**
   - Navigate to `https://www.toto-dream.com/toto/index.html`
   - Detect available rounds (第xxxx回)
   - Select round (latest by default, or user-specified)
   - Click "今すぐ投票予想する" button (automatically clicks "シングル")

4. **Batch Processing Loop**
   - **Batch 1**: Process on current single voting page
   - **Batch 2+**: For each additional batch:
     - Click round link on voting addition page (第xxxx回)
     - Click "シングル" button to return to voting page
     - Fill voting form with 13 games × 10 sets
     - Submit form (add to cart)
     - Handle confirmation dialogs
     - Continue to next batch

5. **Completion**
   - Display summary statistics
   - All items added to cart for checkout

## ⚙️ Configuration

### Browser Settings
- **Default Browser**: Edge (can be changed in config.py)
- **Headless Mode**: Disabled by default (browser window visible)
- **Timeout**: 20 seconds for page operations

### Form Settings
- **Max Sets per Batch**: 10 sets
- **Max Games per Set**: 13 games
- **Valid Values**: 0, 1, 2

### URL Settings
- **Start URL**: `https://www.toto-dream.com/toto/index.html`

## 🐛 Troubleshooting

### Common Issues

1. **"No rounds detected"**
   - Check internet connection
   - Verify the toto website is accessible
   - Try refreshing the page manually

2. **"Failed to fill form"**
   - Check CSV file format (13 columns, values 0/1/2)
   - Ensure you're on the correct voting page
   - Try manually navigating to voting page first

3. **"Browser crashed"**
   - Close all browser windows
   - Restart the application
   - Check system resources

4. **"CSV file not found"**
   - Verify file path is correct
   - Check file permissions
   - Use absolute file path

### Log Files
- Check logs in the GUI "Logs" tab
- Log files are saved in the `logs/` directory
- Enable DEBUG level for detailed troubleshooting

## 📝 Tips & Best Practices

1. **Before Running**:
   - Close other browser windows
   - Ensure stable internet connection
   - Verify CSV data format

2. **During Automation**:
   - Don't interfere with the browser window
   - Monitor the logs for any issues
   - Keep the GUI window visible

3. **After Completion**:
   - Check cart contents before checkout
   - Verify all batches were processed
   - Save logs for future reference

## 🔄 Updates & Maintenance

The system includes automatic features for:
- Round detection with multiple patterns
- Enhanced error handling and retry logic
- Detailed logging and status reporting
- GUI status updates and user feedback

## 📞 Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify your CSV data format
3. Ensure the toto website is accessible
4. Try running in non-headless mode to see what's happening

## 🎉 Success!

When automation completes successfully, you'll see:
- ✅ All batches processed
- 🛒 Items added to cart
- 💳 Ready for checkout
- 📊 Summary statistics

The system is now ready for you to proceed to checkout on the toto website!
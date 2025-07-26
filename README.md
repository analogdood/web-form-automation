# Web Form Automation System

A Python-based automation system for filling web forms with data from CSV files. This system uses Selenium WebDriver to interact with web pages and automatically fill checkbox forms based on CSV input data.

## Features

- 🔄 **Batch Processing**: Automatically splits large datasets into manageable batches
- 🎯 **Smart Element Detection**: Multiple selector strategies for reliable element finding
- 🛡️ **Error Handling**: Comprehensive error handling with detailed logging
- 📊 **Data Validation**: CSV data validation before processing
- 🌐 **Multi-Browser Support**: Chrome, Firefox, and Edge support
- 📱 **Headless Mode**: Option to run without GUI for server environments
- 🔍 **Alert Handling**: Automatic browser alert dialog handling
- 📝 **Detailed Logging**: File and console logging with configurable levels

## Requirements

- Python 3.8+
- Chrome, Firefox, or Edge browser
- Internet connection (for WebDriver downloads)

## Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## CSV Data Format

The system expects CSV files with the following structure:
- Each row represents one set of data
- Each row must contain exactly 13 columns
- Values must be 0, 1, or 2 only
- No headers required

### Example CSV:
```csv
1,2,1,2,1,2,2,1,2,2,0,0,0
2,0,2,1,1,1,1,1,0,2,2,1,0
0,1,2,0,1,2,1,0,2,1,0,2,1
```

### Value Meanings:
- `0` = Left option/checkbox
- `1` = Center option/checkbox  
- `2` = Right option/checkbox

## Usage

### Command Line Interface

Basic usage:
```bash
python voting_automation.py --csv sample_data.csv
```

With URL navigation:
```bash
python voting_automation.py --csv data.csv --url "https://example.com/form"
```

Headless mode (no browser window):
```bash
python voting_automation.py --csv data.csv --headless
```

Custom browser and settings:
```bash
python voting_automation.py --csv data.csv --browser firefox --timeout 15 --log-level DEBUG
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--csv` | Path to CSV file (required) | - |
| `--url` | Target URL to navigate to | None |
| `--headless` | Run browser in headless mode | False |
| `--timeout` | WebDriver timeout in seconds | 10 |
| `--browser` | Browser to use (chrome/firefox/edge) | chrome |
| `--log-level` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |

### Programmatic Usage

```python
from voting_automation import VotingAutomationSystem

# Create automation instance
automation = VotingAutomationSystem(
    csv_path="data.csv",
    url="https://example.com/form",
    headless=False,
    timeout=10
)

# Run automation
success = automation.run_automation()

if success:
    print("Automation completed successfully!")
else:
    print("Automation failed!")
```

## How It Works

### 1. Data Processing
- Loads CSV file and validates format
- Splits data into batches (max 10 sets per batch)
- Validates each value is 0, 1, or 2

### 2. Form Interaction
- Navigates to target URL (if provided)
- Finds checkboxes using intelligent naming patterns:
  - Games 1-10: `chkbox_{game}_{set}_{value}`
  - Game 11: `chkbox_1_{set}_{value}`
  - Game 12: `chkbox_2_{set}_{value}`
- Fills forms batch by batch
- Handles form submission and navigation

### 3. Error Recovery
- Multiple selector strategies for element finding
- JavaScript click fallback for non-interactive elements
- Automatic alert dialog handling
- Detailed error logging and reporting

## Configuration

### Custom Configuration

Edit `config.py` to customize:

```python
class Config:
    # WebDriver settings
    WEBDRIVER_TIMEOUT = 10
    HEADLESS_MODE = False
    
    # Form processing
    MAX_SETS_PER_BATCH = 10
    MAX_GAMES_PER_SET = 13
    
    # Retry settings
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1
```

### Element Selectors

Customize element selectors in `config.py`:

```python
SELECTORS = {
    'submit_button': [
        "input[type='submit']",
        "button[type='submit']",
        "button:contains('送信')",
        ".submit-btn"
    ],
    'next_button': [
        "a:contains('次へ')",
        "button:contains('次へ')",
        ".next-btn"
    ]
}
```

## Project Structure

```
├── voting_automation.py    # Main automation system
├── config.py              # Configuration settings
├── data_handler.py        # CSV data processing
├── webdriver_manager.py   # WebDriver management
├── form_filler.py         # Form interaction logic
├── requirements.txt       # Python dependencies
├── sample_data.csv        # Sample CSV data
└── README.md             # This file
```

## Logging

Logs are written to:
- Console (real-time output)
- `logs/automation.log` (persistent file)

Log levels:
- `DEBUG`: Detailed debugging information
- `INFO`: General progress information
- `WARNING`: Warning messages
- `ERROR`: Error messages

## Troubleshooting

### Common Issues

**WebDriver not found:**
```bash
# Install webdriver-manager to auto-download drivers
pip install webdriver-manager
```

**Element not found:**
- Check CSS selectors in `config.py`
- Use `--log-level DEBUG` for detailed element search logs
- Take screenshots with `automation.take_screenshot()`

**Form submission fails:**
- Verify form selectors match target website
- Check for JavaScript-required interactions
- Ensure proper page load timing

**CSV validation errors:**
- Verify file has exactly 13 columns
- Check all values are 0, 1, or 2
- Remove any headers from CSV file

### Debug Mode

Run with debug logging:
```bash
python voting_automation.py --csv data.csv --log-level DEBUG
```

Take screenshots for debugging:
```python
automation.take_screenshot("debug_screenshot.png")
```

## Browser Compatibility

| Browser | Status | Notes |
|---------|--------|--------|
| Chrome | ✅ Fully Supported | Recommended |
| Firefox | ✅ Fully Supported | - |
| Edge | ✅ Fully Supported | Windows only |

## Security Considerations

- Only use with websites you have permission to automate
- Be mindful of rate limiting and server load
- Consider using delays between operations
- Review website terms of service before automation

## License

This project is for educational and legitimate automation purposes only.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Test with sample data first
4. Verify website compatibility
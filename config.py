"""
Configuration file for Web Form Automation System
"""

import os

class Config:
    # WebDriver settings
    WEBDRIVER_TIMEOUT = 20
    IMPLICIT_WAIT = 5
    PAGE_LOAD_TIMEOUT = 60
    HEADLESS_MODE = False
    
    # Browser settings
    BROWSER = "edge"  # chrome, firefox, edge
    WINDOW_SIZE = (1920, 1080)
    
    # URL settings
    START_URL = "https://www.toto-dream.com/toto/index.html"
    
    # Form processing settings - 13 games × 10 sets (trusting user input over debug)
    MAX_SETS_PER_BATCH = 10  # 10 sets (0-9)
    MAX_GAMES_PER_SET = 13   # 13 games (0-12) - user confirms 13 games exist
    RETRY_ATTEMPTS = 3
    RETRY_DELAY = 1
    
    # Checkbox naming patterns
    CHECKBOX_PATTERNS = {
        'standard': 'chkbox_{game}_{set}_{value}',
        'game_11': 'chkbox_1_{set}_{value}',
        'game_12': 'chkbox_2_{set}_{value}',
        'game_13': 'chkbox_{game}_{set}_{value}'  # Same as standard pattern
    }
    
    # Element selectors (fallback options)
    SELECTORS = {
        'submit_button': [
            "input[type='submit']",
            "button[type='submit']",
            "button:contains('送信')",
            "input[value*='送信']",
            ".submit-btn",
            "#submit"
        ],
        'cart_button': [
            ".kounyu_cart_multiline_base",
            "span:contains('購入カートに追加')",
            "*[class*='kounyu_cart']:not([class*='header']):not([class*='nav'])",
            "input[value*='カートに追加']:not([class*='header'])",
            "input[value*='購入カートに追加']:not([class*='header'])",
            "input[value*='追加']:not([class*='header'])",
            "button:contains('カートに追加'):not([class*='header'])",
            "button:contains('購入カートに追加'):not([class*='header'])",
            "button:contains('追加'):not([class*='header'])",
            "span:contains('カート'):not([class*='header'])",
            "span:contains('追加'):not([class*='header'])",
            "div:contains('購入カートに追加')",
            "a:contains('購入カートに追加'):not([class*='header'])",
            "input[type='submit'][value*='カート']",
            "input[type='button'][value*='カート']",
            "input[type='submit'][value*='追加']",
            "input[type='button'][value*='追加']",
            "button[type='submit']:contains('カート')",
            "button[type='button']:contains('カート')",
            "*[onclick*='addShoppingCartTotoSingle']",
            "*[onclick*='doCurt']",
            "*[onclick*='cart']:not([class*='header'])",
            "*[onclick*='Cart']:not([class*='header'])",
            "*[onclick*='add']:not([class*='header'])",
            "*[onclick*='Add']:not([class*='header'])",
            "*[class*='cart']:not([class*='header']):not([class*='nav'])",
            "*[class*='add']:not([class*='header'])",
            "*[id*='cart']:not([class*='header'])",
            "*[id*='add']:not([class*='header'])",
            "*[name*='cart']",
            "*[name*='add']"
        ],
        'next_button': [
            "a:contains('次へ')",
            "button:contains('次へ')",
            "input[value*='次へ']",
            ".next-btn",
            "#next"
        ],
        'confirm_checkbox': [
            "input[name='confirm']",
            "input[id='confirm']",
            "input[type='checkbox']:contains('確認')"
        ]
    }
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "automation.log"
    
    # CSV settings
    CSV_ENCODING = "utf-8"
    EXPECTED_COLUMNS = 13
    VALID_VALUES = [0, 1, 2]
    
    @classmethod
    def get_chrome_options(cls):
        """Chrome WebDriver options"""
        from selenium.webdriver.chrome.options import Options
        options = Options()
        
        if cls.HEADLESS_MODE:
            options.add_argument("--headless")
        
        options.add_argument(f"--window-size={cls.WINDOW_SIZE[0]},{cls.WINDOW_SIZE[1]}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        
        return options
    
    @classmethod
    def get_firefox_options(cls):
        """Firefox WebDriver options"""
        from selenium.webdriver.firefox.options import Options
        options = Options()
        
        if cls.HEADLESS_MODE:
            options.add_argument("--headless")
        
        return options
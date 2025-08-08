import os
import time
import json
from bs4 import BeautifulSoup
from datetime import datetime
from PIL import Image
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import text
from config import engine, api_key, PromptManager, session
import chromedriver_autoinstaller
import openai
import time


# Configuration
URLS = [
    ("Agent_CNBC", "https://www.cnbc.com"),
    ("Agent_CNN_Money", "https://money.cnn.com"),
    ("Agent_Bloomberg", "https://www.bloomberg.com"),
    ("Agent_Fox_Business", "https://www.foxbusiness.com"),
    ("Agent_Yahoo_Finance", "https://finance.yahoo.com")
]
SCREENSHOT_DIR = "screenshots"
RUN_TIMESTAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
RUN_DIR = os.path.join(SCREENSHOT_DIR, RUN_TIMESTAMP)
os.makedirs(RUN_DIR, exist_ok=True)

# Automatically install correct ChromeDriver version
chromedriver_autoinstaller.install()

# Setup Selenium WebDriver for Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)

# PromptManager instance
prompt_manager = PromptManager(client=openai, session=session, run_id=RUN_TIMESTAMP)

def get_openai_summary(agent_name, html_content, image_paths):
    prompt = f"""
Summarize the financial news from the following content. Focus on actionable information relevant to trading decisions — especially news related to companies, sectors, market movements, and economic indicators.

HTML Content:

{html_content[:10000]}
"""
    system_prompt = (
        "You are a financial summary agent helping a trading system. Your job is to extract concise and actionable insights from financial news pages. "
        "Return a JSON object with 'headlines' (list of strings) and 'insights' (paragraph summary focused on companies, trades, economic indicators, or investor sentiment)."
    )

    result = prompt_manager.ask_openai(prompt, system_prompt, agent_name=agent_name, image_paths=image_paths)
    return result

def try_click_popup(driver, agent_name):

    def click_button(button):
        try:
            driver.execute_script("arguments[0].click();", button)
            print(f"Clicked button via JS: '{button.text.strip()}'")
            return True
        except Exception as e:
            print(f"JavaScript click failed: {e}")
            return False

    keywords = ["agree", "accept", "ok", "got it", "understand", "continue"]

    try:
        # Specific: CNN Money popup
        if agent_name == "Agent_CNN_Money":
            try:
                # Wait for any button that contains "Agree" in text (case-insensitive)
                button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]"))
                )
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Agree')]")))
                if click_button(button):
                    print("CNN Money popup dismissed.")
                    return
            except Exception as e:
                print("Failed to dismiss CNN popup via direct XPath:", e)

        # Try general buttons
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for btn in buttons:
            text = btn.text.lower()
            if any(keyword in text for keyword in keywords):
                if click_button(btn):
                    return

        # Try inside iframes
        for frame in driver.find_elements(By.TAG_NAME, 'iframe'):
            try:
                driver.switch_to.frame(frame)
                buttons = driver.find_elements(By.TAG_NAME, 'button')
                for btn in buttons:
                    text = btn.text.lower()
                    if any(keyword in text for keyword in keywords):
                        if click_button(btn):
                            driver.switch_to.default_content()
                            return
            except Exception as e:
                print(f"Iframe error: {e}")
            finally:
                driver.switch_to.default_content()

        print("No popup matched or was clickable.")
    except Exception as e:
        print(f"Unexpected error in try_click_popup for {agent_name}: {e}")

def summarize_page(agent_name, url):
    driver.get(url)
    time.sleep(5)

    try_click_popup(driver, agent_name)

    # First screenshot (initial viewport)
    screenshot_path_1 = os.path.join(RUN_DIR, f"{agent_name}_1.png")
    try:
        driver.save_screenshot(screenshot_path_1)
    except Exception as e:
        print(f"Error capturing screenshot 1 for {agent_name}: {e}")

    # Scroll using ActionChains instead of script to avoid triggering popups on scroll
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        ActionChains(driver).move_to_element(body).scroll_by_amount(0, 945).perform()  # 7/8 of 1080
        time.sleep(2)
    except Exception as e:
        print(f"Scroll failed for {agent_name}: {e}")

    screenshot_path_2 = os.path.join(RUN_DIR, f"{agent_name}_2.png")
    try:
        driver.save_screenshot(screenshot_path_2)
    except Exception as e:
        print(f"Error capturing screenshot 2 for {agent_name}: {e}")

    html = driver.page_source

    try:
        summary_data = get_openai_summary(agent_name, html, [screenshot_path_1, screenshot_path_2])
    except Exception as e:
        summary_data = {"error": f"Summary failed: {e}"}

    summary = {
        "agent": agent_name,
        "timestamp": RUN_TIMESTAMP,
        "summary": summary_data,
        "screenshot_paths": [screenshot_path_1, screenshot_path_2],
        "run_id": RUN_TIMESTAMP
    }

    return summary

def store_summary(summary):
    with engine.connect() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS summaries (
                id SERIAL PRIMARY KEY,
                agent TEXT,
                timestamp TIMESTAMP,
                run_id TEXT,
                data JSONB
            )
        '''))
        conn.execute(text(
            "INSERT INTO summaries (agent, timestamp, run_id, data) VALUES (:agent, :timestamp, :run_id, :data)"
        ), {
            "agent": summary['agent'],
            "timestamp": datetime.strptime(summary['timestamp'], "%Y%m%dT%H%M%S"),
            "run_id": summary['run_id'],
            "data": json.dumps(summary)
        })

def run_summary_agents():
    for agent_name, url in URLS:
        try:
            summary = summarize_page(agent_name, url)
            store_summary(summary)
            print(f"Stored summary for {agent_name}")
        except Exception as e:
            print(f"Error processing {agent_name} ({url}): {e}")

if __name__ == "__main__":
    run_summary_agents()
    driver.quit()

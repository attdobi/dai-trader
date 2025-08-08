import os
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import text
from config import engine, api_key, PromptManager, session
import chromedriver_autoinstaller
import openai

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

    if agent_name == "Agent_Fox_Business":
        print("Skipping popup checks for Fox Business.")
        return

    try:
        if agent_name == "Agent_CNN_Money":
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree')]"))
                )
                WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Agree')]")))
                if click_button(button):
                    print("CNN Money popup dismissed.")
                    return
            except Exception as e:
                print("Failed to dismiss CNN popup via XPath:", e)

        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for btn in buttons:
            text = btn.text.lower()
            if any(keyword in text for keyword in keywords):
                if click_button(btn):
                    return

        print("No popup matched or was clickable.")
    except Exception as e:
        print(f"Unexpected error in try_click_popup for {agent_name}: {e}")

def summarize_page(agent_name, url):
    driver.get(url)
    time.sleep(5)

    try_click_popup(driver, agent_name)

    screenshot_path_1 = os.path.join(RUN_DIR, f"{agent_name}_1.png")
    try:
        driver.save_screenshot(screenshot_path_1)
    except Exception as e:
        print(f"Screenshot 1 failed for {agent_name}: {e}")
        time.sleep(3)
        try:
            driver.save_screenshot(screenshot_path_1)
        except Exception as e:
            print(f"Retry failed for Screenshot 1: {e}")

    try:
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.875);")
    except Exception as e:
        print(f"Scroll failed for {agent_name}: {e}")

    time.sleep(2)

    screenshot_path_2 = os.path.join(RUN_DIR, f"{agent_name}_2.png")
    try:
        driver.save_screenshot(screenshot_path_2)
    except Exception as e:
        print(f"Screenshot 2 failed for {agent_name}: {e}")
        time.sleep(3)
        try:
            driver.save_screenshot(screenshot_path_2)
        except Exception as e:
            print(f"Retry failed for Screenshot 2: {e}")

    try:
        html = driver.page_source
    except Exception as e:
        print(f"Failed to capture page source for {agent_name}: {e}")
        html = ""

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

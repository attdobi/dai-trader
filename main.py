import os
import time
import json
import re
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
import undetected_chromedriver as uc
from feedback_agent import TradeOutcomeTracker
from bs4 import BeautifulSoup

# Configuration
URLS = [
    ("Agent_CNBC", "https://www.cnbc.com"),
    ("Agent_CNN_Money", "https://money.cnn.com"),
    ("Agent_SeekingAlpha", "https://seekingalpha.com"),
    ("Agent_Fox_Business", "https://www.foxbusiness.com"),
    ("Agent_Yahoo_Finance", "https://finance.yahoo.com")
]

# Use absolute path for screenshot directory to avoid working directory issues
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCREENSHOT_DIR = os.path.join(SCRIPT_DIR, "screenshots")
RUN_TIMESTAMP = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
RUN_DIR = os.path.join(SCREENSHOT_DIR, RUN_TIMESTAMP)
os.makedirs(RUN_DIR, exist_ok=True)

print(f"Screenshot directory: {SCREENSHOT_DIR}")
print(f"Run directory: {RUN_DIR}")

# Automatically install correct ChromeDriver version
chromedriver_autoinstaller.install()

# Set up undetected Chrome with options
chrome_options = uc.ChromeOptions()
chrome_options.add_argument("--headless=new")  #This is stealthier than old headless
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

# Setup Selenium WebDriver for Chrome
# chrome_options = Options()
# chrome_options.add_argument("--headless")
# chrome_options.add_argument("--disable-gpu")
# chrome_options.add_argument("--window-size=1920,1080")
# chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
driver = webdriver.Chrome(options=chrome_options)

# PromptManager instance
prompt_manager = PromptManager(client=openai, session=session, run_id=RUN_TIMESTAMP)

# Initialize feedback tracker
feedback_tracker = TradeOutcomeTracker()

def initialize_database():
    with engine.begin() as conn:
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS summaries (
                id SERIAL PRIMARY KEY,
                agent TEXT,
                timestamp TIMESTAMP,
                run_id TEXT,
                data JSONB
            )
        '''))

def get_openai_summary(agent_name, html_content, image_paths):
    # Get feedback context for summarizer
    feedback_context = ""
    try:
        latest_feedback = feedback_tracker.get_latest_feedback()
        if latest_feedback:
            summarizer_feedback = latest_feedback.get('summarizer_feedback', '')
            if summarizer_feedback and summarizer_feedback != 'null':
                # Parse JSON feedback if it's a string
                if isinstance(summarizer_feedback, str):
                    try:
                        summarizer_feedback = json.loads(summarizer_feedback)
                    except:
                        pass
                
                feedback_context = f"\nPERFORMANCE FEEDBACK: {summarizer_feedback}\nIncorporate this guidance to improve analysis quality."
    except Exception as e:
        print(f"Failed to get summarizer feedback: {e}")

    # Reduce HTML content length to avoid rate limiting
    # Extract only the most relevant content from the HTML
    
    # Remove script and style tags
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    
    # Extract text content more efficiently
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text_content = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content length to avoid rate limiting (reduced from 10000 to 5000)
        if len(text_content) > 5000:
            text_content = text_content[:5000] + "... [content truncated]"
            
        html_content = text_content
    except Exception as e:
        print(f"Failed to parse HTML content for {agent_name}: {e}")
        # Fallback: just truncate the raw HTML
        if len(html_content) > 5000:
            html_content = html_content[:5000] + "... [content truncated]"

    prompt = f"""
Summarize the financial news from the following content. Focus on actionable information relevant to trading decisions — especially news related to companies, sectors, market movements, and economic indicators.

{feedback_context}

Content:

{html_content}

IMPORTANT: You must respond with a valid JSON object in this exact format:
{{
    "headlines": ["headline 1", "headline 2", "headline 3"],
    "insights": "A comprehensive analysis paragraph focusing on actionable trading insights, market sentiment, and specific companies or sectors mentioned."
}}

Do not include any text before or after the JSON object. Only return the JSON.
"""
    system_prompt = (
        "You are a financial summary agent helping a trading system. Your job is to extract concise and actionable insights from financial news pages."
        "Pay special attention to the images that portray positive or negative sentiment. Remember in some cases a new story and image could be shown for market manipulation"
        "Though it is good to buy on optimism and sell on negative news it could also be a good time to sell and buy, respectively."
        "Learn from feedback to improve your analysis quality and focus on information that leads to profitable trades."
        "You must ALWAYS respond with valid JSON format as specified in the prompt."
    )
    
    # Only include images if they were successfully saved and are reasonably sized
    valid_image_paths = []
    for img_path in image_paths:
        if os.path.exists(img_path):
            file_size = os.path.getsize(img_path)
            # Only include images smaller than 1MB to avoid rate limiting
            if file_size < 1024 * 1024:
                valid_image_paths.append(img_path)
            else:
                print(f"Skipping large image {img_path} ({file_size} bytes)")
    
    return prompt_manager.ask_openai(prompt, system_prompt, agent_name="SummarizerAgent", image_paths=valid_image_paths)

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
    # Special handling for Yahoo Finance which can be slow
    if "yahoo.com" in url.lower():
        print(f"Loading {agent_name} (Yahoo Finance - extended timeout)")
        try:
            # Set page load timeout for Yahoo Finance
            driver.set_page_load_timeout(180)  # 3 minutes
            driver.get(url)
            time.sleep(8)  # Extra wait for Yahoo Finance
        except Exception as e:
            print(f"Timeout loading {agent_name}, retrying with shorter timeout: {e}")
            try:
                driver.set_page_load_timeout(60)  # Fallback to 1 minute
                driver.get(url)
                time.sleep(5)
            except Exception as e2:
                print(f"Failed to load {agent_name} after retry: {e2}")
                # Return empty summary if we can't load the page
                return {
                    "agent": agent_name,
                    "timestamp": RUN_TIMESTAMP,
                    "summary": {"error": f"Failed to load page: {e2}"},
                    "screenshot_paths": [],
                    "run_id": RUN_TIMESTAMP
                }
    else:
        # Normal handling for other sites
        driver.get(url)
        time.sleep(5)

    # Reset timeout to default after successful page load
    try:
        driver.set_page_load_timeout(30)  # Reset to 30 seconds default
    except:
        pass

    try_click_popup(driver, agent_name)

    screenshot_path_1 = os.path.join(RUN_DIR, f"{agent_name}_1.png")
    screenshot_saved_1 = False
    try:
        driver.save_screenshot(screenshot_path_1)
        if os.path.exists(screenshot_path_1) and os.path.getsize(screenshot_path_1) > 0:
            screenshot_saved_1 = True
            print(f"Screenshot 1 saved successfully for {agent_name}: {screenshot_path_1}")
        else:
            print(f"Screenshot 1 file not created or empty for {agent_name}")
    except Exception as e:
        print(f"Screenshot 1 failed for {agent_name}: {e}")
        time.sleep(3)
        try:
            driver.save_screenshot(screenshot_path_1)
            if os.path.exists(screenshot_path_1) and os.path.getsize(screenshot_path_1) > 0:
                screenshot_saved_1 = True
                print(f"Screenshot 1 retry successful for {agent_name}")
            else:
                print(f"Screenshot 1 retry failed - file not created for {agent_name}")
        except Exception as e:
            print(f"Retry failed for Screenshot 1: {e}")

    try:
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.875);")
    except Exception as e:
        print(f"Scroll failed for {agent_name}: {e}")

    time.sleep(2)

    screenshot_path_2 = os.path.join(RUN_DIR, f"{agent_name}_2.png")
    screenshot_saved_2 = False
    try:
        driver.save_screenshot(screenshot_path_2)
        if os.path.exists(screenshot_path_2) and os.path.getsize(screenshot_path_2) > 0:
            screenshot_saved_2 = True
            print(f"Screenshot 2 saved successfully for {agent_name}: {screenshot_path_2}")
        else:
            print(f"Screenshot 2 file not created or empty for {agent_name}")
    except Exception as e:
        print(f"Screenshot 2 failed for {agent_name}: {e}")
        time.sleep(3)
        try:
            driver.save_screenshot(screenshot_path_2)
            if os.path.exists(screenshot_path_2) and os.path.getsize(screenshot_path_2) > 0:
                screenshot_saved_2 = True
                print(f"Screenshot 2 retry successful for {agent_name}")
            else:
                print(f"Screenshot 2 retry failed - file not created for {agent_name}")
        except Exception as e:
            print(f"Retry failed for Screenshot 2: {e}")

    try:
        html = driver.page_source
    except Exception as e:
        print(f"Failed to capture page source for {agent_name}: {e}")
        html = ""

    # Only include screenshot paths that were actually saved
    saved_screenshots = []
    if screenshot_saved_1:
        saved_screenshots.append(screenshot_path_1)
    if screenshot_saved_2:
        saved_screenshots.append(screenshot_path_2)

    try:
        summary_data = get_openai_summary(agent_name, html, saved_screenshots)
    except Exception as e:
        summary_data = {"error": f"Summary failed: {e}"}

    summary = {
        "agent": agent_name,
        "timestamp": RUN_TIMESTAMP,
        "summary": summary_data,
        "screenshot_paths": saved_screenshots,
        "run_id": RUN_TIMESTAMP
    }

    return summary

def store_summary(summary):
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO summaries (agent, timestamp, run_id, data) VALUES (:agent, :timestamp, :run_id, :data)"
        ), {
            "agent": summary['agent'],
            "timestamp": datetime.strptime(summary['timestamp'], "%Y%m%dT%H%M%S"),
            "run_id": summary['run_id'],
            "data": json.dumps(summary)
        })

def run_summary_agents():
    global driver
    initialize_database()
    
    # Create a fresh Chrome driver for this run
    try:
        # Close existing driver if it exists
        if 'driver' in globals() and driver:
            try:
                driver.quit()
            except:
                pass
        
        # Create new driver
        driver = webdriver.Chrome(options=chrome_options)
        print("Created new Chrome driver for summarizer run")
        
        for agent_name, url in URLS:
            try:
                summary = summarize_page(agent_name, url)
                store_summary(summary)
                print(f"Stored summary for {agent_name}")
                # Small delay between agents to prevent overwhelming the system
                time.sleep(2)
            except Exception as e:
                print(f"Error processing {agent_name} ({url}): {e}")
                # Continue with next agent even if one fails
                continue
                
    except Exception as e:
        print(f"Failed to create Chrome driver: {e}")
    finally:
        # Always cleanup the driver
        try:
            if 'driver' in globals() and driver:
                driver.quit()
                print("Chrome driver cleaned up")
        except:
            pass

if __name__ == "__main__":
    run_summary_agents()

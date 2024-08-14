from fastapi import APIRouter, BackgroundTasks
from ..services.scheduler import update_interacting_addresses
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import json

router = APIRouter()

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

async def check_website_update():
    url = "https://cache.wayfinder.ai/cache/account/0x8e5e01DCa1706F9Df683c53a6Fc9D4bb8D237153"
    driver = setup_driver()
    
    try:
        driver.get(url)
        
        # Wait for the element to be present (adjust the timeout as needed)
        last_updated_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.text-white\\/70.text-2xs"))
        )
        
        last_updated_text = last_updated_element.text
        last_updated_date_wayfinder = datetime.strptime(last_updated_text.split()[-1], "%Y-%m-%d")

        try:
            with open("last_updated_date.json", "r") as file:
                data = json.load(file)
                last_updated_date_addresses_json = datetime.strptime(data["date"], "%Y-%m-%d")
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"date": datetime.min.strftime("%Y-%m-%d"), "times": []}
            last_updated_date_addresses_json = datetime.min
        
        if last_updated_date_addresses_json.date() < last_updated_date_wayfinder.date():
            await update_interacting_addresses()
            current_time = datetime.now().strftime("%H:%M:%S")
            data["date"] = last_updated_date_wayfinder.strftime("%Y-%m-%d")
            data["times"].append(current_time)
            with open("last_updated_date.json", "w") as file:
                json.dump(data, file)
        else:
            print(f"Website not updated today. Last update: {last_updated_date_addresses_json.date()}")
    
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        driver.quit()


@router.post("/update_addresses")
async def trigger_update_addresses(background_tasks: BackgroundTasks):
    background_tasks.add_task(check_website_update)
    return {"message": "Address update initiated"}

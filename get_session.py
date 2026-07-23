import webbrowser
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def get_session_id():
    print("Opening Dreamina in browser...")
    print("Please login manually in the browser window.")
    print("After login, press Enter here to continue...")
    
    options = Options()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    driver.get("https://jimeng.jianying.com/")
    
    input("Press Enter after you have logged in...")
    
    cookies = driver.get_cookies()
    session_id = None
    
    for cookie in cookies:
        if cookie["name"] == "sessionid":
            session_id = cookie["value"]
            break
    
    driver.quit()
    
    if session_id:
        print(f"\nSession ID found: {session_id}")
        print(f"\nAdd this to your .env file:")
        print(f"DREAMINA_SESSION_ID={session_id}")
    else:
        print("\nSession ID not found. Please make sure you are logged in.")
    
    return session_id


if __name__ == "__main__":
    get_session_id()

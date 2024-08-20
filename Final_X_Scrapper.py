import streamlit as st
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import dotenv 
import os

# Load environment variables from .env file
dotenv.load_dotenv()

# Retrieve the variables from the environment
username = os.getenv('X_USERNAME')
password = os.getenv('X_PASSWORD')
mobile_number = os.getenv('X_MOBILE')

def login_to_x(driver, username, password, mobile_number):
    driver.get('https://www.x.com/login')
    time.sleep(10)

    username_input = driver.find_element(By.CSS_SELECTOR, 'input[name="text"]')
    username_input.send_keys(username)
    time.sleep(4)

    next_button = driver.find_element(By.XPATH, '//button[contains(@class, "css-175oi2r") and .//span[text()="Next"]]')
    next_button.click()
    time.sleep(4)

    try:
        mobile_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="ocfEnterTextTextInput"]'))
        )
        mobile_input.send_keys(mobile_number)

        verify_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="ocfEnterTextNextButton"]'))
        )
        verify_button.click()

        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
    except:
        # If mobile input is not found, proceed to password input directly
        password_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )

    password_input.send_keys(password)

    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="LoginForm_Login_Button"]'))
    )
    login_button.click()
    time.sleep(10)

def search_hashtag(driver, query, desired_posts=50, posts_per_scroll=5):
    search_url = f'https://x.com/search?q=%23{query}'
    driver.get(search_url)
    time.sleep(5)

    all_posts_data = []
    while len(all_posts_data) < desired_posts:
        new_posts_data = extract_post_data(driver)
        all_posts_data.extend(new_posts_data)

        if len(all_posts_data) >= desired_posts:
            break
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

    return all_posts_data[:desired_posts]

def extract_post_data(driver):
    posts_data = []
    try:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        posts = soup.find_all('div', {'class': 'css-175oi2r r-1igl3o0 r-qklmqi r-1adg3ll r-1ny4l3l'})

        for post in posts:
            # Extract profile URL
            profile_url_tag = post.find('a', {'role': 'link'})
            profile_url = f"https://x.com{profile_url_tag['href']}" if profile_url_tag else None

            # Extract image URL
            image_tag = post.find('img', {'alt': 'Image'})
            image_url = image_tag['src'] if image_tag else None

            # Extract post text
            post_text_tag = post.find('div', {'data-testid': 'tweetText'})
            post_text = post_text_tag.get_text(strip=True) if post_text_tag else None

            posts_data.append({
                'profile_url': profile_url,
                'image_url': image_url,
                'post_text': post_text
            })
    except Exception as e:
        print(f"Error extracting post data: {e}")

    return posts_data

def main():
    st.title("Twitter(X) Scraper")
    st.write("Enter the details below to scrape posts from X.")

    query = st.text_input("Enter your query (without '#'):")
    desired_posts = st.number_input("Enter the number of posts you want to scrape:", min_value=1, max_value=100, value=50)

    if st.button("Start Scraping"):
        st.write("Scraping in progress...")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        try:
            login_to_x(driver, username, password, mobile_number)
            posts_data = search_hashtag(driver, query, desired_posts=desired_posts)

            st.write(f"Scraped {len(posts_data)} posts:")

            df = pd.DataFrame(posts_data)
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name='scraped_posts.csv',
                mime='text/csv',
            )

        finally:
            driver.quit()

if __name__ == "__main__":
    main()

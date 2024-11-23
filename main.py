import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initialize_driver(chrome_driver_path: str, headless: bool = True) -> webdriver.Chrome:
    """Initialize the Chrome WebDriver with the provided settings."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    if headless:
        chrome_options.add_argument("--headless")  # Run headless
    chrome_options.add_argument("--no-sandbox")
    service = Service(chrome_driver_path)
    
    return webdriver.Chrome(service=service, options=chrome_options)


def download_image(image_url: str, save_path: str):
    """Download and save an image from the given URL."""
    try:
        img_data = requests.get(image_url).content
        with open(save_path, "wb") as f:
            f.write(img_data)
        print(f"Image saved as {save_path} successfully.")
    except Exception as e:
        print(f"Error downloading image {save_path}: {e}")


def process_product_images(driver: webdriver.Chrome, product_url: str, product_id: str, product_name: str, output_dir: str):
    """Process the product page and download images."""
    driver.execute_script(f"window.open('{product_url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Wait for pictures to load
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "picture"))
    )

    pictures = driver.find_elements(By.TAG_NAME, "picture")
    
    if not pictures:
        print(f"No pictures found for {product_url}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return

    # Extract product ID from URL (dkp-<id>)
    base_id = product_url.split("/product/")[1].split("/")[0]

    # Download images
    for pic_index, picture in enumerate(pictures):
        try:
            img = picture.find_element(By.TAG_NAME, "img")
            img_url = img.get_attribute("src")

            if img_url:
                # Use the extracted product base ID for the filename
                filename = f"{output_dir}/{base_id}_{product_name}_{pic_index + 1}.jpg"
                download_image(img_url, filename)

                # Sleep 1 second before downloading the next image
                time.sleep(0.5)
            else:
                print(f"Image does not have a valid source URL for product {product_name}.")
        except Exception as e:
            print(f"Error processing image {pic_index + 1} for product {product_name}: {e}")
    
    # Close the product tab and return to main tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    """Process the product page and download images."""
    driver.execute_script(f"window.open('{product_url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])

    # Wait for pictures to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "picture"))
    )

    pictures = driver.find_elements(By.TAG_NAME, "picture")
    
    if not pictures:
        print(f"No pictures found for {product_url}")
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        return

    # Download images
    for pic_index, picture in enumerate(pictures):
        try:
            img = picture.find_element(By.TAG_NAME, "img")
            img_url = img.get_attribute("src")

            if img_url:
                filename = f"{output_dir}/{product_id}_{product_name}_{pic_index + 1}.jpg"
                download_image(img_url, filename)
            else:
                print(f"Image does not have a valid source URL for product {product_name}.")
        except Exception as e:
            print(f"Error processing image {pic_index + 1} for product {product_name}: {e}")
    
    # Close the product tab and return to main tab
    driver.close()
    driver.switch_to.window(driver.window_handles[0])


def scrape_products(driver: webdriver.Chrome, target_url: str, output_dir: str, max_pages: int = 500):
    """Scrape products from the provided URL."""
    page_number = 1
    product_counter = 0

    for i in range(max_pages):
        try:
            page_url = f"{target_url}page={page_number}"
            print(f"Navigating to: {page_url}")
            driver.get(page_url)

            # Wait for products to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "product-list_ProductList__item__LiiNI"))
            )

            divs = driver.find_elements(By.CLASS_NAME, "product-list_ProductList__item__LiiNI")

            if not divs:
                print("No products found, breaking out.")
                break

            # Process each product
            for div in divs:
                product_counter += 1
                print(f"Processing product {product_counter}...")

                try:
                    a_tag = div.find_element(By.TAG_NAME, "a")
                    href = a_tag.get_attribute("href")

                    if href:
                        product_id = href.split('/')[-2]
                        product_name = href.split('/')[-1]
                        print(f"Processing {product_name} with ID {product_id}")

                        # Process the product page
                        process_product_images(driver, href, product_id, product_name, output_dir)

                except Exception as e:
                    print(f"Error processing product link {product_counter}: {e}")
                    continue

        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            break

        page_number += 1


def main():
    # Load environment variables
    load_dotenv()
    target_url = os.getenv("TARGET_URL")

    if not target_url:
        print("Error: TARGET_URL not found in .env file")
        exit(1)

    # Set up output directory
    output_dir = "downloaded_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Path to your ChromeDriver
    chrome_driver_path = "/Users/ehsan/Downloads/chromedriver/chromedriver"
    
    # Initialize WebDriver
    driver = initialize_driver(chrome_driver_path)

    # Start scraping
    scrape_products(driver, target_url, output_dir)

    # Quit driver after scraping
    driver.quit()


if __name__ == "__main__":
    main()

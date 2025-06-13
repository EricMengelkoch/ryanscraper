from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError
import json
import os
import urllib.parse
import pandas as pd
import csv

ZOOMINFO_LOGIN_URL = "https://login.zoominfo.com/"
ZOOMINFO_APP_URL = "https://app.zoominfo.com/"
FILTER_TOKEN = "eyJmaWx0ZXJzIjp7InBhZ2UiOjEsImNvbXBhbnlQYXN0T3JQcmVzZW50IjoiMSIsImlzQ2VydGlmaWVkIjoiaW5jbHVkZSIsInNvcnRCeSI6IlJlbGV2YW5jZSIsInNvcnRPcmRlciI6ImRlc2MiLCJleGNsdWRlRGVmdW5jdENvbXBhbmllcyI6dHJ1ZSwiY29uZmlkZW5jZVNjb3JlTWluIjo4NSwiY29uZmlkZW5jZVNjb3JlTWF4Ijo5OSwib3V0cHV0Q3VycmVuY3lDb2RlIjoiVVNEIiwiaW5wdXRDdXJyZW5jeUNvZGUiOiJVU0QiLCJleGNsdWRlTm9Db21wYW55IjoidHJ1ZSIsInJldHVybk9ubHlCb2FyZE1lbWJlcnMiOmZhbHNlLCJleGNsdWRlQm9hcmRNZW1iZXJzIjp0cnVlLCJVU19TdGF0ZXMiOiJBcml6b25hIiwidGl0bGVTZW5pb3JpdHkiOiJDX0VYRUNVVElWRVMifSwic2VhcmNoVHlwZSI6MH0%3D"
COOKIES_FILE = "cookies.json"
USERNAME = "ryanp@sparx.solar"
PASSWORD = "MoneyBall@2"

def save_cookies(context):
    cookies = context.cookies()
    with open(COOKIES_FILE, "w") as f:
        json.dump(cookies, f, indent=2)
    print("[+] Cookies saved to", COOKIES_FILE)

def load_cookies(context):
    if os.path.exists(COOKIES_FILE):
        try:
            with open(COOKIES_FILE, "r") as f:
                data = f.read().strip()
                if not data:
                    print("[-] cookies.json is empty.")
                    return False
                cookies = json.loads(data)
                context.add_cookies(cookies)
                print("[+] Cookies loaded from", COOKIES_FILE)
                return True
        except Exception as e:
            print(f"[-] Failed to load cookies: {e}")
    return False

def login_and_save(page, context):
    page.goto(ZOOMINFO_LOGIN_URL)
    page.fill('input[id="usernameInput"]', USERNAME)
    page.fill('input[id="pwInput"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url("https://app.zoominfo.com/**", timeout=20000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(5000)
    save_cookies(context)
    print("[+] Logged in and cookies saved.")

def extract_ids(page):
    results = []
    print("tests")

    i = 0

    with open('contacts.csv', 'r', encoding='utf-8') as file:
        for line in file:
            i += 1
    while (len(results) < 1000):
        try:
            page.wait_for_selector('tr[data-automation-id^="saved-searches-table-row"]', timeout=10000)
        except TimeoutError:
            page.wait_for_timeout(1000)
            page.reload()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_selector('tr[data-automation-id^="saved-searches-table-row"]', timeout=10000)
        rows = page.query_selector_all('tr[data-automation-id^="saved-searches-table-row"]')
        print(f"[+] Found {len(rows)} companies")

        if (i < 1):
            for card in rows:
                try:
                    link = card.query_selector('a[data-zoominfo-id]')
                    zoominfo_id = link.get_attribute('data-zoominfo-id') if link else None

                    results.append({
                        zoominfo_id if zoominfo_id else ""
                    })
                except Exception as e:
                    print("[-] Error parsing a company card:", e)
        else:
            i = i - 25

        next_button = page.query_selector('.p-paginator-next')
        if next_button:
            next_button.click()
            page.wait_for_timeout(1000)  # optional: wait for next page to load
        else:
            print("[-] Next button not found")
            break

    df = pd.DataFrame(results)
    df.to_csv("results.csv", index=False)
    print("[+] Saved results to results.csv")
    return results

def search_and_save(page, line, index):
    line = next(iter(line))
    url = f"https://app.zoominfo.com/#/apps/profile/person/{line}/contact-profile"
    page.goto(url)
    selector = "#primaryContact > div > div > div.contact-details-grid-col-left > div.contact-details-left-wrapper > zi-person-contact-details > main > div.person-contact-details__phone-email.ng-star-inserted > section:nth-child(2)"
    selectwo = "#app-wrapper > div.application-content-wrapper > zi-sales-root > zi-profile-page > main > section > zi-person-profile-wrapper > zi-person-classic-view > zi-person-fullpage > div > div > div:nth-child(1) > zi-header-person-details > div > div.contact-details__data > div.contact-details__data__text > div.contact-details__data__text__name-container > div > div"
    try:
        page.wait_for_timeout(200)
        page.wait_for_selector(selector, timeout=5000)
    except TimeoutError:
        try:
            page.wait_for_selector(selectwo, timeout=1000)
        except TimeoutError:
            print("[!] Timeout waiting for contact info, retrying...")
            page.wait_for_timeout(3000)
            page.reload()
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_selector(selectwo, timeout=5000)  # second try

    # Extract fields
    print(index)
    def get(selector, default=None):
        try:
            return page.locator(selector).text_content().strip()
        except:
            return default

    full_name = get("div.contact-details__data__text__name")
    title = get("div.contact-details__data__text__title")
    company = get("span.company-details__link-row__link")
    email = get("div.contact-details-left-wrapper")
    if (email):
        normalized_text = ' '.join(email.split())
    else:
        normalized_text = "No contact info found"
    location = get("#primaryContact > div > div > div.contact-details-grid-col-left > zi-person-location > div > zi-designed-divided-text:nth-child(2) > div > div:nth-child(2)")

    print(full_name)

    # Prepare data row
    row = {
        "Full Name": full_name,
        "Title": title,
        "Company": company,
        "Info": normalized_text,
        "Location": location
    }
    # Write to CSV in append mode
    file_exists = os.path.isfile("contacts.csv")
    with open("contacts.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()

        if load_cookies(context):
            page = context.new_page()
            page.goto(ZOOMINFO_APP_URL)
            page.wait_for_load_state("domcontentloaded")
            page.wait_for_timeout(3000)

            if "login" in page.url:
                print("[-] Redirected to login. Cookies invalid.")
                login_and_save(page, context)
        else:
            page = context.new_page()
            login_and_save(page, context)

        encoded_url = f"https://app.zoominfo.com/#/apps/searchV2/v2/results/person?query={FILTER_TOKEN}"
        print("[+] Navigating to search URL with filters...")
        page.wait_for_timeout(5000)
        page.goto(encoded_url)
        page.wait_for_timeout(8000)

        results = extract_ids(page)

        print(results)

        n = 0
        for line in results:
            search_and_save(page, line, n)
            n = n + 1

        browser.close()

if __name__ == "__main__":
    run()

from playwright.sync_api import sync_playwright
import json
import os
import urllib.parse
import pandas as pd

ZOOMINFO_LOGIN_URL = "https://login.zoominfo.com/"
ZOOMINFO_APP_URL = "https://app.zoominfo.com/"
FILTER_TOKEN = "eyJmaWx0ZXJzIjp7InBhZ2UiOjEsImNvbXBhbnlQYXN0T3JQcmVzZW50IjoiMSIsImlzQ2VydGlmaWVkIjoiaW5jbHVrZSIsInNvcnRCeSI6Imxpa2VseV90b19lbmdhZ2VfcGhvbmUiLCJzb3J0T3JkZXIiOiJkZXNjIiwiZXhjbHVkZURlZnVuY3RDb21wYW5pZXMiOnRydWUsImNvbmZpZGVuY2VTY29yZU1pbiI6ODUsImNvbmZpZGVuY2VTY29yZU1heCI6OTksIm91dHB1dEN1cnJlbmN5Q29kZSI6IlVTRCIsImlucHV0Q3VycmVuY3lDb2RlIjoiVVNEIiwiZXhjbHVkZU5vQ29tcGFueSI6InRydWUiLCJyZXR1cm5Pbmx5Qm9hcmRNZW1iZXJzIjpmYWxzZSwiZXhjbHVkZUJvYXJkTWVtYmVycyI6dHJ1ZSwiemlwQ29kZSI6Ijg1MjYyLDg1MjY2LDg1Mzc3LDg1MzMxLDg1MDg1LDg1MDgzLDg1MzEwLDg1MzA4LDg1MDI3LDg1MDI0LDg1MDUwLDg1MDU0LDg1MjU0LDg1MDMyLDg1MDIyIn0sInNlYXJjaFR5cGUiOjB9"
COOKIES_FILE = "cookies.json"
USERNAME = "ryanp@sparx.solar"
PASSWORD = "FireFire@2"

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

def extract_and_save(page):
    print("tests")
    page.wait_for_selector(".company-card", timeout=10000)
    print("2")
    companies = page.query_selector_all(".company-card")
    print(f"[+] Found {len(companies)} companies")

    results = []
    for card in companies:
        try:
            name = card.query_selector(".company-name") or card.query_selector('[data-qa="company-name"]')
            phone = card.query_selector(".phone-number") or card.query_selector('[data-qa="company-phone"]')
            website = card.query_selector(".website a") or card.query_selector('[data-qa="company-website"]')
            fullname = card.query_selector(".contact-name") or card.query_selector('[data-qa="contact-name"]')

            results.append({
                "Company": name.inner_text().strip() if name else "",
                "Phone": phone.inner_text().strip() if phone else "",
                "Website": website.inner_text().strip() if website else "",
                "Full Name": fullname.inner_text().strip() if fullname else ""
            })
        except Exception as e:
            print("[-] Error parsing a company card:", e)

    df = pd.DataFrame(results)
    df.to_csv("results.csv", index=False)
    print("[+] Saved results to results.csv")

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

        encoded_url = "https://app.zoominfo.com/#/apps/searchV2/v2/results/person?query=eyJmaWx0ZXJzIjp7InBhZ2UiOjEsImNvbXBhbnlQYXN0T3JQcmVzZW50IjoiMSIsImlzQ2VydGlmaWVkIjoiaW5jbHVkZSIsInNvcnRCeSI6Imxpa2VseV90b19lbmdhZ2VfcGhvbmUiLCJzb3J0T3JkZXIiOiJkZXNjIiwiZXhjbHVkZURlZnVuY3RDb21wYW5pZXMiOnRydWUsImNvbmZpZGVuY2VTY29yZU1pbiI6ODUsImNvbmZpZGVuY2VTY29yZU1heCI6OTksIm91dHB1dEN1cnJlbmN5Q29kZSI6IlVTRCIsImlucHV0Q3VycmVuY3lDb2RlIjoiVVNEIiwiZXhjbHVkZU5vQ29tcGFueSI6InRydWUiLCJyZXR1cm5Pbmx5Qm9hcmRNZW1iZXJzIjpmYWxzZSwiZXhjbHVkZUJvYXJkTWVtYmVycyI6dHJ1ZSwiemlwQ29kZSI6Ijg1MjYyLDg1MjY2LDg1Mzc3LDg1MzMxLDg1MDg1LDg1MDgzLDg1MzEwLDg1MzA4LDg1MDI3LDg1MDI0LDg1MDUwLDg1MDU0LDg1MjU0LDg1MDMyLDg1MDIyIn0sInNlYXJjaFR5cGUiOjB9"
        print("[+] Navigating to search URL with filters...")
        page.wait_for_timeout(5000)
        page.goto(encoded_url)
        page.wait_for_timeout(8000)

        extract_and_save(page)
        browser.close()

if __name__ == "__main__":
    run()

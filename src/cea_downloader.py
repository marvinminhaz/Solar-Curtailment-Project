"""
Download "Power Supply Position - Peak" PDF reports (2015-2016) from:
https://cea.nic.in/monthly-reports-archive/?lang=en

Setup:
    pip install selenium requests

Run:
    python scrape_cea_peak_simple.py

Saves files into ./downloads/ as PSP_Peak_2015-01.pdf, PSP_Peak_2015-02.pdf, etc.
"""

import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

URL = "https://cea.nic.in/monthly-reports-archive/?lang=en"
YEARS = list(range(2026, 2027))
MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]

os.makedirs("downloads", exist_ok=True)

options = webdriver.ChromeOptions()
# options.add_argument("--headless=new")   # set False / remove this line to watch it run
driver = webdriver.Chrome(options=options)

for year in YEARS:
    for i, month in enumerate(MONTHS, start=1):
        print(f"Checking {month} {year}...")
        driver.get(URL)

        # Pick Year, Month, and Report Type dropdowns.
        # If this fails, open the page in Chrome DevTools (F12) and check
        # the real <select> elements - the options below match the visible
        # text shown on the page.
        selects = driver.find_elements(By.TAG_NAME, "select")
        year_dd, month_dd, type_dd = None, None, None
        for s in selects:
            options_text = [o.text.strip() for o in Select(s).options]
            if str(year) in options_text and "2015" in options_text:
                year_dd = Select(s)
            elif month in options_text and "January" in options_text:
                month_dd = Select(s)
            elif "Power Supply Reports" in options_text:
                type_dd = Select(s)

        if not (year_dd and month_dd and type_dd):
            print("  Could not find one of the dropdowns, skipping.")
            continue

        year_dd.select_by_visible_text(str(year))
        month_dd.select_by_visible_text(month)
        type_dd.select_by_visible_text("Power Supply Reports")

        # Click the "Show Archive Reports" button
        try:
            driver.find_element(
                By.XPATH,
                "//*[contains(translate(text(),"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),"
                "'show archive reports')]"
            ).click()
        except Exception:
            print("  Could not find the 'Show Archive Reports' button, skipping.")
            continue

        time.sleep(3)  # let the results load

        # Find the "Power Supply Position - Peak" row and its PDF link
        pdf_url = None
        rows = driver.find_elements(By.XPATH, "//*[contains(text(), 'Power Supply Position - Peak')]")
        for row in rows:
            parent = row.find_element(By.XPATH, "./ancestor::tr[1]") if row.tag_name != "tr" else row
            links = parent.find_elements(By.XPATH, ".//a[@href]")
            for link in links:
                href = link.get_attribute("href") or ""
                if ".pdf" in href.lower():
                    pdf_url = href
                    break
            if pdf_url:
                break

        if not pdf_url:
            print("  No Peak report found for this month.")
            continue

        filename = f"downloads/PSP_Peak_{year}-{i:02d}.pdf"
        response = requests.get(pdf_url, timeout=60)
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"  Saved {filename}")

driver.quit()
print("Done.")
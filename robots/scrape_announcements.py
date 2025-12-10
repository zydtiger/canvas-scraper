import asyncio
from playwright.async_api import async_playwright
import json
from typing import List, Dict
import sys
import argparse


async def scrape_canvas_announcements(page) -> List[Dict[str, str]]:
    """
    Extract unread announcement data from Canvas table#announcement-details.

    Args:
        page: Playwright page object with Canvas already loaded

    Returns:
        List of dictionaries with date, title, and course information
    """
    try:
        # Wait for the announcement table to be present
        await page.wait_for_selector(
            "table#announcement-details tbody", timeout=10000, state="attached"
        )

        # Find all tr elements that contain div.unread
        rows_with_unread = await page.query_selector_all(
            "table#announcement-details tbody tr:has(div.unread)"
        )

        announcements = []

        for row in rows_with_unread:
            try:
                # Extract date from td.date
                date_element = await row.query_selector("td.date")
                date = await date_element.inner_text() if date_element else "N/A"

                # Extract content summary from a.content_summary
                content_link = await row.query_selector("a.content_summary")
                if content_link:
                    href = await content_link.get_attribute("href")
                    if href.startswith("/"):
                        href = f"https://jhu.instructure.com{href}"

                    content_text = await content_link.inner_text()

                    fake_link_element = await content_link.query_selector(
                        "span.fake-link"
                    )
                    course_code = await fake_link_element.inner_text()

                    title = content_text.replace(course_code, "").strip()

                    # Store the announcement data
                    announcements.append(
                        {
                            "date": date.strip(),
                            "title": title.strip(),
                            "course": course_code.strip(),
                            "link": href,
                        }
                    )

            except Exception as e:
                print(f"Error processing row: {e}", file=sys.stderr)
                continue

        return announcements

    except Exception as e:
        print(f"Error scraping announcements: {e}", file=sys.stderr)
        return []


async def scrape_announcements_page(cookies_list):
    """
    Open Canvas with session and scrape announcements
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Set cookies before navigation
            if cookies_list:
                await context.add_cookies(cookies_list)

            # Navigate to Canvas announcements page
            await page.goto("https://jhu.instructure.com")
            await page.wait_for_load_state("networkidle")

            # Click on dashboard options and recent activity
            await page.click('button[data-testid="dashboard-options-button"]')
            await page.click('span[data-testid="recent-activity-menu-item"]')

            # Scrape announcements
            announcements = await scrape_canvas_announcements(page)

            # Output results
            print(json.dumps(announcements))

        except Exception as error:
            print(f"Error: {error}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

        finally:
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Canvas announcements.")
    parser.add_argument(
        "--cookies", help="Cookies in key:value,key:value format", type=str
    )
    args = parser.parse_args()

    cookies_list = []
    if args.cookies:
        pairs = args.cookies.split(",")
        for pair in pairs:
            if ":" in pair:
                key, value = pair.split(":", 1)
                cookies_list.append(
                    {
                        "name": key.strip(),
                        "value": value.strip(),
                        "domain": "jhu.instructure.com",
                        "path": "/",
                    }
                )

    if not cookies_list:
        print(
            "Error: No cookies provided. Please use --cookies argument.",
            file=sys.stderr,
        )
        sys.exit(1)

    asyncio.run(scrape_announcements_page(cookies_list))

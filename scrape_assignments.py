import asyncio
from playwright.async_api import async_playwright
import json
from typing import List, Dict
import sys
import argparse


async def scrape_canvas_assignments(page) -> List[Dict[str, str]]:
    """
    Extract assignment data from Canvas table#assignment-details.

    Args:
        page: Playwright page object with Canvas already loaded

    Returns:
        List of dictionaries with course, title, and due_date information
    """
    assignments = []
    assignment_index = 0

    while True:
        # Re-query the table rows each time to get fresh DOM elements
        await page.wait_for_selector(
            "table#assignment-details tbody", timeout=10000, state="attached"
        )
        assignment_rows = await page.query_selector_all(
            "table#assignment-details tbody tr"
        )

        # If we've processed all assignments, break the loop
        if assignment_index >= len(assignment_rows):
            break

        row = assignment_rows[assignment_index]

        try:
            # Extract content summary from a.content_summary
            content_link = await row.query_selector("a.content_summary")
            if not content_link:
                assignment_index += 1
                continue

            # Get the href for navigation
            href = await content_link.get_attribute("href")
            if not href:
                assignment_index += 1
                continue

            # Extract content text
            content_text = await content_link.inner_text()

            # Extract course code from fake-link
            fake_link_element = await content_link.query_selector("span.fake-link")
            if not fake_link_element:
                assignment_index += 1
                continue

            course_code = await fake_link_element.inner_text()

            # Extract title by removing course code from content text
            title = content_text.replace(course_code, "").strip()

            # Navigate to assignment page to get due date
            # Store current page URL to return later
            current_url = page.url

            # Navigate to assignment page - handle relative URLs
            assignment_url = href
            if href.startswith("/"):
                assignment_url = f"https://jhu.instructure.com{href}"

            await page.goto(assignment_url)
            await page.wait_for_load_state("networkidle")

            # Get due date from span.date_text
            date_element = await page.query_selector("span.date_text")
            due_date = "N/A"
            if date_element:
                due_date = await date_element.inner_text()
                due_date = due_date.strip()

            # Navigate back to original page
            await page.goto(current_url)
            await page.wait_for_load_state("networkidle")

            # Store the assignment data
            assignments.append(
                {
                    "course": course_code.strip(),
                    "title": title.strip(),
                    "due_date": due_date,
                    "link": assignment_url,
                }
            )

            # Move to next assignment
            assignment_index += 1

        except Exception as e:
            print(
                f"Error processing assignment row {assignment_index}: {e}",
                file=sys.stderr,
            )
            assignment_index += 1
            continue

    return assignments


async def scrape_assignments_page(cookies_list):
    """
    Open Canvas with session and scrape assignments
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Set cookies before navigation
            if cookies_list:
                await context.add_cookies(cookies_list)

            # Navigate to Canvas assignments page
            await page.goto("https://jhu.instructure.com")
            await page.wait_for_load_state("networkidle")

            # Click on dashboard options and recent activity
            await page.click('button[data-testid="dashboard-options-button"]')
            await page.click('span[data-testid="recent-activity-menu-item"]')

            # Scrape assignments
            assignments = await scrape_canvas_assignments(page)

            # Output results
            print(json.dumps(assignments))

        except Exception as error:
            print(f"Error: {error}", file=sys.stderr)
            import traceback

            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

        finally:
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Canvas assignments.")
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

    asyncio.run(scrape_assignments_page(cookies_list))

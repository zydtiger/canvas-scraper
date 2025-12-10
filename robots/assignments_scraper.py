from playwright.async_api import Page
from typing import List
from pydantic import HttpUrl

from .base_scraper import BaseScraper
from ..models import Assignment


class AssignmentScraper(BaseScraper[Assignment]):
    """
    Canvas assignments scraper implementation.
    """

    async def scrape_page(self, page: Page) -> List[Assignment]:
        """
        Extract assignment data from Canvas table#assignment-details.

        Args:
            page: Playwright page object with Canvas already loaded

        Returns:
            List of Assignment objects with course, title, due_date, and link information
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

            # Extract content summary from a.content_summary
            content_link = await row.query_selector("a.content_summary")
            if content_link is None:
                assignment_index += 1
                continue

            # Get the href for navigation
            href = await content_link.get_attribute("href")
            if href is None:
                assignment_index += 1
                continue

            # Extract content text
            content_text = await content_link.inner_text()

            # Extract course code from fake-link
            fake_link_element = await content_link.query_selector("span.fake-link")
            if fake_link_element is None:
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
                Assignment(
                    course=course_code.strip(),
                    title=title.strip(),
                    due_date=due_date,
                    link=HttpUrl(assignment_url),
                )
            )

            # Move to next assignment
            assignment_index += 1

        return assignments

from playwright.async_api import Page
from typing import List
from pydantic import HttpUrl

from .base_scraper import BaseScraper
from ..models import Announcement


class AnnouncementScraper(BaseScraper[Announcement]):
    """
    Canvas announcements scraper implementation.
    """

    async def scrape_page(self, page: Page) -> List[Announcement]:
        """
        Extract unread announcement data from Canvas table#announcement-details.

        Args:
            page: Playwright page object with Canvas already loaded

        Returns:
            List of Announcement objects with date, title, course, and link information
        """
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
            # Extract date from td.date
            date_element = await row.query_selector("td.date")
            date = await date_element.inner_text() if date_element else "N/A"

            # Extract content summary from a.content_summary
            content_link = await row.query_selector("a.content_summary")
            if content_link:
                href = await content_link.get_attribute("href")
                if href is None:
                    continue
                if href.startswith("/"):
                    href = f"https://jhu.instructure.com{href}"

                content_text = await content_link.inner_text()

                fake_link_element = await content_link.query_selector("span.fake-link")
                if fake_link_element is None:
                    continue
                course_code = await fake_link_element.inner_text()

                title = content_text.replace(course_code, "").strip()

                # Store the announcement data
                announcements.append(
                    Announcement(
                        date=date.strip(),
                        title=title.strip(),
                        course=course_code.strip(),
                        link=HttpUrl(href),
                    )
                )

        return announcements

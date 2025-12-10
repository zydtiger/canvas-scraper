from abc import ABC, abstractmethod
from playwright.async_api import async_playwright, Page
from typing import List, TypeVar, Generic
from pydantic import BaseModel

from ..models import ScrapeException

T = TypeVar("T", bound=BaseModel)


class BaseScraper(Generic[T], ABC):
    """
    Abstract base class for Canvas scrapers.
    """

    def __init__(self, session: str):
        """
        Initialize the scraper with a Canvas session.

        Args:
            session: Canvas session token string
        """
        self.session = session

    @abstractmethod
    async def scrape_page(self, page: Page) -> List[T]:
        """
        Scrape data from a given Playwright page object.
        This method should be implemented by subclasses to extract specific data.

        Args:
            page: Playwright page object with Canvas already loaded

        Returns:
            List of scraped objects (Announcement or Assignment)
        """
        pass

    async def scrape(self) -> List[T]:
        """
        Main scraping method that handles browser setup, authentication,
        and delegates the actual scraping to scrape_page().

        Returns:
            List of scraped objects
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Set cookies before navigation
                await context.add_cookies(
                    [
                        {
                            "name": "canvas_session",
                            "value": self.session,
                            "domain": "jhu.instructure.com",
                            "path": "/",
                        }
                    ]
                )

                # Navigate to Canvas
                await page.goto("https://jhu.instructure.com")
                await page.wait_for_load_state("networkidle")

                # Click on dashboard options and recent activity
                await page.click('button[data-testid="dashboard-options-button"]')
                await page.click('span[data-testid="recent-activity-menu-item"]')

                # Delegate scraping to subclass implementation
                return await self.scrape_page(page)

            except Exception as error:
                raise ScrapeException(f"Failed to scrape Canvas: {error}")

            finally:
                await browser.close()

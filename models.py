from pydantic import BaseModel, HttpUrl, Field


class ScrapeException(Exception):
    pass


class Announcement(BaseModel):
    date: str = Field(..., description="The date when the announcement was posted")
    title: str = Field(..., description="The title of the announcement")
    course: str = Field(..., description="The course code or name")
    link: HttpUrl = Field(..., description="Direct URL to the announcement in Canvas")


class Assignment(BaseModel):
    course: str = Field(..., description="The course code or name")
    title: str = Field(..., description="The assignment title")
    due_date: str = Field(
        ..., description="The due date of the assignment (format may vary)"
    )
    link: HttpUrl = Field(
        ..., description="Direct URL to the assignment page in Canvas"
    )

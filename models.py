from pydantic import BaseModel

class CrawlResult(BaseModel):
    domain: str
    pages: list[str]
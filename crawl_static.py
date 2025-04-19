from urllib.parse import urljoin, urlparse
from fastapi import HTTPException, APIRouter
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel

router = APIRouter(tags=["static"])

class CrawlResult(BaseModel):
    domain: str
    pages: list[str]


async def crawl(target_url: str) -> CrawlResult:
    visited = set()
    queue = [target_url]
    domain = urlparse(target_url).netloc
    pages = []

    async with httpx.AsyncClient() as client:
            while queue:
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                try:
                    response = await client.get(url, timeout=5)
                    if response.status_code == 200:
                        pages.append(url)
                        soup = BeautifulSoup(response.text, "html.parser")
                        # print(soup)
                    for link in soup.find_all("a", href=True):
                        href =link.get("href")   #link["href"] 
                        absolute_url = urljoin(url, href)
                        parsed = urlparse(absolute_url)
                        if parsed.netloc == domain:
                            queue.append(absolute_url)
                    for link in soup.find_all("img", src=True):
                        # print("link",link)
                        src= link["src"]   
                        # print("src", src) 
                        absolute_url =urljoin(url, src)
                    
                        parsed=urlparse(absolute_url)
                        # print("parsed",parsed)

                        if parsed.netloc == domain:
                            queue.append(absolute_url)
                except Exception as e:
                    print(f"Error crawling {url}: {e}")
    return CrawlResult(domain=target_url, pages=pages)     


@router.get("/pages")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    return await crawl(target)
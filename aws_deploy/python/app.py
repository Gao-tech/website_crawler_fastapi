from mangum import Mangum
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, HTTPException
import httpx
from bs4 import BeautifulSoup
from models import CrawlResult
import datetime


MAX_LINKS =50
async def crawl(target_url: str) -> list[str]:
    visited = set()
    queue = [target_url]
    domain = urlparse(target_url).netloc
    pages = set()
    async with httpx.AsyncClient() as client:
            while queue and len(pages) <= MAX_LINKS:
                print("--Size of the pages---", len(pages), MAX_LINKS)
                url = queue.pop(0)
                if url in visited:
                    continue
                visited.add(url)
                try:
                    response = await client.get(url, timeout=1)
                    if response.status_code == 200:
                        pages.add(url)
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
    return pages     

app = FastAPI()

@app.get("/pages")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    pages = await crawl(target)
    return CrawlResult(domain=target, pages=pages)

handler = Mangum(app)
from urllib.parse import urljoin, urlparse
from fastapi import FastAPI, HTTPException
import httpx
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, HttpUrl


app = FastAPI()

# class URL(BaseModel):
#     url: HttpUrl

# @app.get('/')
# async def get_url():
#     return {'message': 'hello url'}

# @app.post('/crawling_pages')
# async def crawling_pages(url: URL):
#     page = requests.get(str(url.url))
#     soup = BeautifulSoup(page.text, "html.parser")

#     import pdb
#     pdb.set_trace()
#     return url
    

class CrawlResult(BaseModel):
    domain: HttpUrl
    pages: list[HttpUrl]

async def crawl(target_url: HttpUrl) -> CrawlResult:
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
            
            response = await client.get(url, timeout=5)
            if response.status_code == 200:
                pages.append(url)
                soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.find_all("a", href=True):
                href = link["href"]
                absolute_url = urljoin(url, href)
                parsed = urlparse(absolute_url)
                if parsed.netloc == domain:
                    queue.append(absolute_url)

    return CrawlResult(domain=target_url, pages=pages)                

@app.get("/pages")
async def get_pages(target: HttpUrl):
    if not target.startswitch(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    return await crawl(target)
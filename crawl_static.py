from urllib.parse import urljoin, urlparse
from fastapi import HTTPException, APIRouter
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from models import CrawlResult
import datetime
import os
from redis_connect import save_to_redis, get_from_redis

MAX_LINKS = int(os.environ.get("MAX_LINKS_PER_URL_STATIC",50))


router = APIRouter(tags=["static"])


async def crawl(target_url: str) -> list[str]:
    visited = set()
    queue = [target_url]
    domain = urlparse(target_url).netloc
    pages = set()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"error_log_{domain}_{timestamp}.txt"
    err_count=1
    async with httpx.AsyncClient() as client:
            while queue and len(pages) <= MAX_LINKS:
                print("--Size of the pages---", len(pages), MAX_LINKS, len(pages) <= MAX_LINKS)
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
                    await write_err_in_file(e,err_count, filename)
                    err_count+=1
    return pages     


async def write_err_in_file(err,err_count, filename):

    error_message = str(err_count) + "," + str(datetime.datetime.now(datetime.timezone.utc))+ "\t" + str(err) + "\n"
    with open(filename, "a") as f:
        f.write(error_message)
    print(f"Error log saved to {filename}")

@router.get("/pages")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    pages = await crawl(target)
    return CrawlResult(domain=target, pages=pages)


@router.get("/pages_redis")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    value = get_from_redis(target)
    if not value:
        value = await crawl(target)
        save_to_redis(target, value)
    return CrawlResult(domain=target, pages=value)
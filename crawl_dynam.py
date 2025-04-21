import datetime
from urllib.parse import urljoin, urlparse
from fastapi import HTTPException, APIRouter
from models import CrawlResult
from playwright.async_api import async_playwright
import os
from redis_connect import save_to_redis, get_from_redis


MAX_LINKS = int(os.getenv("MAX_LINKS_PER_URL", 10))

router = APIRouter(tags=["dynam"])


async def crawl(target_url: str) -> list[str]:

    visited = set()
    queue = [target_url]
    parsed_target = urlparse(target_url)
    target_domain = parsed_target.hostname 
    pages = set()
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"error_log_{target_domain}_{timestamp}.txt"
    err_count=1

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
     
        while queue and len(pages)<= MAX_LINKS:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                STATIC_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".svg", ".ico", ".pdf")
                if any(url.lower().endswith(ext) for ext in STATIC_EXTENSIONS):
                    print("-Size of pages ", len(pages), MAX_LINKS)
                    pages.add(url)
                    continue  
                page = await context.new_page()
                await page.goto(url, wait_until="networkidle")  
                content = await page.content()
                # print(content)
                
                print("--Size of pages ", len(pages))
                pages.add(url)
                links = await page.eval_on_selector_all(
                    "a, img", 
                    """elements => elements.map(e => 
                        e.href || e.getAttribute('data-src') || e.src
                    )"""
                )
                # print("links", links)

                for href in links:
                    if not href:
                        continue
                    absolute_url = urljoin(url, href)
                    parsed = urlparse(absolute_url)
                   
                    if parsed.hostname == target_domain:
                        queue.append(absolute_url)
                    # print("queue:", queue)    
                for src in links:
                    if not src:
                        continue
                    absolute_url = urljoin(url, src)
                    parsed = urlparse(absolute_url)
                    # print("src parsed", parsed)
                    if parsed.hostname == target_domain:
                        queue.append(absolute_url)        
                    # print("queue:", queue)
                await page.close()
            except Exception as e:
               
                # print(f"Error crawling {url}: {e}")
                await write_err_in_file(e,err_count, filename)
                err_count +=1
        await browser.close()

    return pages #CrawlResult(domain=target_url, pages=pages)


async def write_err_in_file(err, err_count, filename):
       # error_message = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H-%M-%S") + "\t" + str(err) + "\n"
        error_message = str(err_count) + ","+ str(datetime.datetime.now(datetime.timezone.utc)) + "\t" + str(err) + "\n"
        
        with open(filename, "a") as f:
            f.write(error_message)
        print(f"Error log saved to {filename}")

@router.get("/pages_dynam")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    pages= await crawl(target)
    return CrawlResult(domain=target, pages=pages)


@router.get("/pages_dynam_redis")
async def get_pages(target: str):
    if not target.startswith (("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    key = "Dynam"+target
    value = get_from_redis(key)
    if not value:
        value = await crawl(target)
        save_to_redis(key, value)
    return CrawlResult(domain=target, pages=value)

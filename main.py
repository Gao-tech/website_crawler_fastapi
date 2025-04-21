from fastapi import FastAPI
import crawl_dynam
import crawl_static
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI()
app.include_router(crawl_dynam.router)
app.include_router(crawl_static.router)


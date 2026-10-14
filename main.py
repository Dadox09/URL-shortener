# main.py
import hashlib
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI()

conn = sqlite3.connect("database.sql", check_same_thread=False)
conn.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_url TEXT NOT NULL,
        digest TEXT NOT NULL UNIQUE
    )
    """)


class UrlRequest(BaseModel):
    url: HttpUrl


@app.get("/")  # endpoint
async def read_root():
    """
    This is the root endpoint of the API.
    It returns a simple greeting message.
    """
    return {"message": "Hello from the FastAPI Service!"}


@app.get("/status")  # endpoint to check the status of the API
async def get_status():
    """
    A simple status endpoint.
    """
    return {"status": "API is running correctly."}


@app.post("/shorten")  # endpoint to shorten a URL
def shorten_url(url_request: UrlRequest):
    """
    This endpoint takes a URL as input and returns a shortened version of it.
    """
    url = str(url_request.url)
    digest = hashlib.md5(url.encode()).hexdigest()[:6]
    shortened_url = f"https://short.url/{digest}"

    # Save the original and shortened URL in the database
    try:
        conn.execute(
            "INSERT INTO urls (original_url, digest) VALUES (?, ?)",
            (url, digest),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # shortened_url already exists: same URL shortened again, or a hash collision
        conn.rollback()
        cursor = conn.execute(
            "SELECT original_url FROM urls WHERE digest = ?", (digest,)
        )
        if cursor.fetchone()[0] != url:
            raise HTTPException(
                status_code=409, detail="409 - Shortened URL collision."
            ) from None

    return {"original_url": url, "shortened_url": shortened_url}


@app.get("/{code}", responses={404: {"description": "Shortened URL not found"}})
def redirect_to_original(code: str):
    """
    This endpoint takes a shortened URL code and redirects to the original URL.
    """
    digest = code
    try:
        cursor = conn.execute(
            "SELECT original_url FROM urls WHERE digest = ?", (digest,)
        )
        original_url = cursor.fetchone()[0]
    except TypeError:
        raise HTTPException(
            status_code=404, detail="404 - Shortened URL not found."
        ) from None

    return RedirectResponse(url=original_url)

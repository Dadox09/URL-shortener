# main.py
import hashlib
import os
from contextlib import asynccontextmanager
from typing import Annotated

import psycopg
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from psycopg_pool import ConnectionPool
from pydantic import BaseModel, HttpUrl

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: open the connection pool and create the table.
    Shutdown: close the pool (when the `with` block exits).
    """
    with ConnectionPool(
        kwargs={
            "host": os.environ.get("DB_HOST", "localhost"),
            "dbname": os.environ["POSTGRES_DB"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PASSWORD"],
        },
        # Verify each connection before handing it out, so a DB restart
        # doesn't leave dead connections in the pool
        check=ConnectionPool.check_connection,
    ) as pool:
        with pool.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    original_url TEXT NOT NULL,
                    digest TEXT NOT NULL UNIQUE
                )
                """)

        app.state.pool = pool
        yield


app = FastAPI(lifespan=lifespan)


def get_conn(request: Request):
    """
    Dependency: borrow a connection from the pool for the duration of a request.
    On exit the pool commits (or rolls back on error) and takes the connection back.
    """
    with request.app.state.pool.connection() as conn:
        yield conn


DbConn = Annotated[psycopg.Connection, Depends(get_conn)]


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
def shorten_url(url_request: UrlRequest, conn: DbConn):
    """
    This endpoint takes a URL as input and returns a shortened version of it.
    """
    url = str(url_request.url)
    digest = hashlib.md5(url.encode()).hexdigest()[:6]
    shortened_url = f"https://short.url/{digest}"

    # Save the original and shortened URL in the database
    try:
        conn.execute(
            "INSERT INTO urls (original_url, digest) VALUES (%s, %s)",
            (url, digest),
        )
        conn.commit()
    except psycopg.IntegrityError:
        # shortened_url already exists: same URL shortened again, or a hash collision
        conn.rollback()
        cursor = conn.execute(
            "SELECT original_url FROM urls WHERE digest = %s", (digest,)
        )
        if cursor.fetchone()[0] != url:
            raise HTTPException(
                status_code=409, detail="409 - Shortened URL collision."
            ) from None

    return {"original_url": url, "shortened_url": shortened_url}


@app.get("/{code}", responses={404: {"description": "Shortened URL not found"}})
def redirect_to_original(code: str, conn: DbConn):
    """
    This endpoint takes a shortened URL code and redirects to the original URL.
    """
    digest = code
    try:
        cursor = conn.execute(
            "SELECT original_url FROM urls WHERE digest = %s", (digest,)
        )
        original_url = cursor.fetchone()[0]
    except TypeError:
        raise HTTPException(
            status_code=404, detail="404 - Shortened URL not found."
        ) from None

    return RedirectResponse(url=original_url)

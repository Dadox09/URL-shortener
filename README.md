# URL Shortener

Minimal URL shortening API built with [FastAPI](https://fastapi.tiangolo.com/) and SQLite.

## How it works

- The short code is the first 6 characters of the URL's MD5 hash, so the same URL always gets the same code.
- URLs are stored in the SQLite file `database.sql`, table `urls` (`id`, `original_url`, `digest`). The table is created on startup if it doesn't exist.

## Endpoints

| Method | Path       | Description |
|--------|------------|-------------|
| GET    | `/`        | Welcome message. |
| GET    | `/status`  | Checks that the API is running. |
| POST   | `/shorten?url=<URL>` | Shortens the URL and returns `original_url` and `shortened_url` (`https://short.url/<code>`). If the URL was already shortened, returns the same link. If a different URL already has that code, responds `409`. |
| GET    | `/{code}`  | Returns the `original_url` for the code as JSON, or `404` if the code doesn't exist. |

## Running

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

Interactive docs are available at <http://127.0.0.1:8000/docs>.

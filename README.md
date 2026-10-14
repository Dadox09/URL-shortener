# URL Shortener

URL shortening API built with [FastAPI](https://fastapi.tiangolo.com/) and SQLite.

## How it works

- The short code is the first 6 characters of the URL's MD5 hash, so the same URL always gets the same code.
- Input URLs are validated with Pydantic's `HttpUrl`, which also normalizes them (e.g. `https://example.com` becomes `https://example.com/`).
- URLs are stored in the SQLite file `database.sql`, table `urls` (`id`, `original_url`, `digest`). The table is created on startup if it doesn't exist.

## Endpoints

| Method | Path       | Description |
|--------|------------|-------------|
| GET    | `/`        | Welcome message. |
| GET    | `/status`  | Checks that the API is running. |
| POST   | `/shorten` | Takes a JSON body `{"url": "<URL>"}` and returns `original_url` and `shortened_url` (`https://short.url/<code>`). If the URL was already shortened, returns the same link. If a different URL already has that code, responds `409`. Invalid URLs get `422`. |
| GET    | `/{code}`  | Redirects (`307 Temporary Redirect`) to the original URL, or responds `404` if the code doesn't exist. |

Example:

```bash
curl -X POST http://127.0.0.1:8000/shorten -H "Content-Type: application/json" -d '{"url": "https://example.com"}'
curl -i http://127.0.0.1:8000/<code>
```

## Running

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Interactive docs are available at <http://127.0.0.1:8000/docs>.

## Testing

```bash
python -m pytest -v
```

Note: tests currently run against the same `database.sql` file used by the app.

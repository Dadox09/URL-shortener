from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_read_root():
    """
    Test the root endpoint.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from the FastAPI Service!"}


def test_get_status():
    """
    Test the status endpoint.
    """
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "API is running correctly."}


def test_shorten_url():
    """
    Test the URL shortening endpoint.
    """
    test_url = "https://www.example.com/"
    response = client.post("/shorten", json={"url": test_url})
    assert response.status_code == 200
    data = response.json()
    assert "original_url" in data
    assert "shortened_url" in data
    assert data["original_url"] == test_url


def test_not_valid_url():
    """
    Test the URL shortening endpoint with an invalid URL.
    """
    invalid_url = "not_a_valid_url"
    response = client.post("/shorten", json={"url": invalid_url})
    assert response.status_code == 422  # Unprocessable Entity


def test_shorten_url_same_digest():
    """
    Test the URL shortening endpoint for a collision scenario.
    """
    test_url = "https://www.example.com/"
    # First, shorten the URL to get the digest
    response = client.post("/shorten", json={"url": test_url})
    assert response.status_code == 200
    shortened_url = response.json()["shortened_url"]

    response = client.post("/shorten", json={"url": test_url})
    assert response.status_code == 200
    assert response.json()["shortened_url"] == shortened_url


def test_redirect_to_original():
    """
    Test the redirection endpoint.
    """
    test_url = "https://www.example.com/"
    # First, shorten the URL to get the digest
    response = client.post("/shorten", json={"url": test_url})
    assert response.status_code == 200
    shortened_url = response.json()["shortened_url"]
    digest = shortened_url.split("/")[-1]

    # Now, test the redirection using the digest
    # Don't follow the redirect: TestClient would send it to our own app
    response = client.get(f"/{digest}", follow_redirects=False)
    assert response.status_code == 307  # Temporary Redirect
    assert response.headers["location"] == test_url


def test_redirect_to_original_not_found():
    """
    Test the redirection endpoint for a non-existent digest.
    """
    non_existent_digest = "abcdef"
    response = client.get(f"/{non_existent_digest}")
    assert response.status_code == 404
    assert response.json() == {"detail": "404 - Shortened URL not found."}

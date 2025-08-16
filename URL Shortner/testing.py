import unittest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal, engine
from models import Base, URL, Click
from datetime import datetime, timedelta

client = TestClient(app)
Base.metadata.create_all(bind=engine)


def create_dummy_url(
    db,
    long_url="https://example.com",
    short_code="abc123",
    expires_at=None,
    is_active=True,
):
    url = URL(
        long_url=long_url,
        short_code=short_code,
        created_at=datetime.now(),
        expires_at=expires_at,
        is_active=is_active,
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


class TestURLShortener(unittest.TestCase):

    def setUp(self):
        self.db = SessionLocal()
        self.db.query(Click).delete()
        self.db.query(URL).delete()
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_shorten_url(self):
        response = client.post("/shorten", json={"long_url": "https://test.com"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("short_url", response.json())

    def test_redirect_valid_url(self):
        # Create a test URL
        test_long_url = "https://example.com"
        url = create_dummy_url(self.db, long_url=test_long_url, short_code="valid123")

        # Debug: Print all URLs in database
        all_urls = self.db.query(URL).all()
        print("\nDebug - All URLs in database:")
        for u in all_urls:
            print(
                f"Short code: {u.short_code}, Long URL: {u.long_url}, Active: {u.is_active}"
            )

        # Verify URL was created
        created_url = self.db.query(URL).filter(URL.short_code == "valid123").first()
        self.assertIsNotNone(created_url, "URL was not created in database")

        if created_url:
            print(f"\nDebug - Created URL status: {created_url.status}")
        else:
            print("\nDebug - No URL found in database")

        # Test the redirect
        response = client.get("/valid123", follow_redirects=False)
        print(f"\nDebug - Response status: {response.status_code}")
        print(f"Debug - Response body: {response.text}")

        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], test_long_url)

    def test_redirect_expired_url(self):
        expired_time = datetime.now() - timedelta(days=1)
        url = create_dummy_url(
            self.db, short_code="expired123", expires_at=expired_time
        )
        response = client.get(f"/{url.short_code}")
        self.assertEqual(response.status_code, 410)
        self.assertIn("URL is expired", response.text)
        self.assertEqual(url.status, "expired")

    def test_redirect_inactive_url(self):
        url = create_dummy_url(self.db, short_code="inactive123", is_active=False)
        response = client.get(f"/{url.short_code}")
        self.assertEqual(response.status_code, 410)
        self.assertIn("URL is inactive", response.text)
        self.assertEqual(url.status, "inactive")

    def test_click_tracking(self):
        url = create_dummy_url(self.db, short_code="track123")
        initial_clicks = self.db.query(Click).filter(Click.url_id == url.id).count()
        client.get(f"/{url.short_code}")
        final_clicks = self.db.query(Click).filter(Click.url_id == url.id).count()
        self.assertEqual(final_clicks, initial_clicks + 1)

    def test_url_analytics(self):
        # Test active URL
        url = create_dummy_url(self.db, short_code="analytics123")
        response = client.get(f"/analytics/{url.short_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "active")

        # Test inactive URL
        url_inactive = create_dummy_url(
            self.db, short_code="inactive_analytics", is_active=False
        )
        response = client.get(f"/analytics/{url_inactive.short_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "inactive")

        # Test expired URL
        expired_time = datetime.now() - timedelta(days=1)
        url_expired = create_dummy_url(
            self.db, short_code="expired_analytics", expires_at=expired_time
        )
        response = client.get(f"/analytics/{url_expired.short_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "expired")

    def test_url_creation_with_custom_expiry(self):
        # Test URL creation with future expiry
        future_time = datetime.now() + timedelta(days=7)
        response = client.post(
            "/shorten",
            json={
                "long_url": "https://example.com",
                "expires_at": future_time.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("short_url", data)

    def test_multiple_clicks_tracking(self):
        # Create a URL and simulate multiple clicks from different sources
        url = create_dummy_url(self.db, short_code="multiclick")

        # Simulate clicks with different IP addresses and user agents
        test_cases = [
            {"ip": "192.168.1.1", "agent": "Mozilla/5.0"},
            {"ip": "10.0.0.1", "agent": "Chrome/91.0"},
            {"ip": "172.16.0.1", "agent": "Safari/14.0"},
        ]

        initial_clicks = self.db.query(Click).filter(Click.url_id == url.id).count()

        for case in test_cases:
            headers = {"user-agent": case["agent"]}
            client.get(f"/{url.short_code}", headers=headers)

        final_clicks = self.db.query(Click).filter(Click.url_id == url.id).count()
        self.assertEqual(final_clicks, initial_clicks + len(test_cases))

        # Verify click details
        clicks = self.db.query(Click).filter(Click.url_id == url.id).all()
        user_agents = [click.user_agent for click in clicks]
        self.assertTrue(any("Chrome" in ua for ua in user_agents))
        self.assertTrue(any("Safari" in ua for ua in user_agents))

    def test_url_statistics(self):
        # Create a URL and generate some click statistics
        url = create_dummy_url(self.db, short_code="stats123")

        # Generate clicks at different times
        click_times = [
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        for time in click_times:
            click = Click(
                url_id=url.id,
                timestamp=time,  # Using timestamp instead of created_at
                ip_address="127.0.0.1",
                user_agent="Test Agent",
            )
            self.db.add(click)
        self.db.commit()

        # Get analytics
        response = client.get(f"/analytics/{url.short_code}")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Verify statistics
        self.assertEqual(data["click_count"], len(click_times))
        self.assertEqual(data["status"], "active")
        self.assertIsNotNone(data["created_at"])

    def test_batch_url_operations(self):
        # Test creating multiple URLs and verifying them
        test_urls = [
            {"long_url": "https://example1.com", "code": "batch1"},
            {"long_url": "https://example2.com", "code": "batch2"},
            {"long_url": "https://example3.com", "code": "batch3"},
        ]

        created_urls = []
        for url_data in test_urls:
            url = create_dummy_url(
                self.db, long_url=url_data["long_url"], short_code=url_data["code"]
            )
            created_urls.append(url)

        # Test batch retrieval
        for url in created_urls:
            response = client.get(f"/{url.short_code}", follow_redirects=False)
            self.assertEqual(response.status_code, 307)
            self.assertEqual(response.headers["location"], url.long_url)

        # Test analytics for all URLs
        for url in created_urls:
            response = client.get(f"/analytics/{url.short_code}")
            self.assertEqual(response.status_code, 200)

    def test_url_expiration_flow(self):
        # Test URL lifecycle with different expiration states
        # 1. Create a URL that expires in 1 second
        expire_soon = datetime.now() + timedelta(seconds=1)
        url = create_dummy_url(
            self.db,
            long_url="https://expiring.com",
            short_code="expire_test",
            expires_at=expire_soon,
        )

        # URL should be active initially
        response = client.get(f"/{url.short_code}", follow_redirects=False)
        self.assertEqual(response.status_code, 307)

        # Wait for expiration
        import time

        time.sleep(1.1)  # Wait just over 1 second

        # URL should now be expired
        response = client.get(f"/{url.short_code}")
        self.assertEqual(response.status_code, 410)
        self.assertIn("expired", response.text.lower())


if __name__ == "__main__":
    unittest.main()

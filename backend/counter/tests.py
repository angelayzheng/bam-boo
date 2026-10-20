import json

from django.test import TestCase


class CounterApiTests(TestCase):
    def test_count_starts_at_zero(self):
        response = self.client.get("/api/count/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"count": 0})

    def test_count_updates_and_persists(self):
        increment = self.client.post(
            "/api/count/",
            data=json.dumps({"delta": 1}),
            content_type="application/json",
        )
        decrement = self.client.post(
            "/api/count/",
            data=json.dumps({"delta": -1}),
            content_type="application/json",
        )

        self.assertEqual(increment.json(), {"count": 1})
        self.assertEqual(decrement.json(), {"count": 0})
        self.assertEqual(self.client.get("/api/count/").json(), {"count": 0})

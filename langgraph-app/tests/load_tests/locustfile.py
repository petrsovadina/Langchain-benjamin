"""Load testing for Czech MedAI API using Locust.

Usage:
    # Run locally
    locust -f tests/load_tests/locustfile.py --host=http://localhost:8000

    # Run headless (100 users, 10/s spawn rate, 5 min)
    locust -f tests/load_tests/locustfile.py \
        --host=http://localhost:8000 \
        --users 100 \
        --spawn-rate 10 \
        --run-time 5m \
        --headless

Performance Targets:
    - 100+ concurrent users
    - <5s p95 latency
    - <1% error rate
    - >50 RPS throughput
"""

import json
import random
from locust import HttpUser, task, between


class MedAIUser(HttpUser):
    """Simulated user for Czech MedAI API."""

    wait_time = between(1, 3)  # Wait 1-3s between requests

    # Sample queries (realistic medical queries)
    queries = [
        "Jaké jsou kontraindikace metforminu?",
        "Guidelines pro léčbu hypertenze",
        "Nejnovější studie o SGLT2 inhibitorech",
        "Dávkování warfarinu u CKD",
        "Interakce mezi atorvastatinem a klaritromycinem",
        "Léčba diabetu 2. typu u srdečního selhání",
        "Kontraindikace ACE inhibitorů",
        "Úhrada metforminu VZP",
        "Doporučené postupy pro ICHS",
        "Studie o empagliflozinu u HFrEF",
    ]

    @task(3)
    def health_check(self):
        """Health check endpoint (30% of requests)."""
        self.client.get("/health")

    @task(7)
    def consult_quick(self):
        """Quick consult endpoint (70% of requests)."""
        query = random.choice(self.queries)

        with self.client.post(
            "/api/v1/consult",
            json={"query": query, "mode": "quick"},
            catch_response=True,
            stream=True,
        ) as response:
            if response.status_code == 200:
                # Read SSE stream
                events = []
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data:'):
                            try:
                                data = json.loads(line_str[5:].strip())
                                events.append(data)
                            except json.JSONDecodeError:
                                pass

                # Verify final response
                final_events = [e for e in events if e.get('type') == 'final']
                if final_events:
                    response.success()
                else:
                    response.failure("No final response in SSE stream")
            else:
                response.failure(f"Status code: {response.status_code}")

    @task(1)
    def consult_deep(self):
        """Deep consult endpoint (10% of requests)."""
        query = random.choice(self.queries)

        with self.client.post(
            "/api/v1/consult",
            json={"query": query, "mode": "deep"},
            catch_response=True,
            stream=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")

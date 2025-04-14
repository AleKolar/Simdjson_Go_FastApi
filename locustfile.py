from locust import HttpUser, task, between
from datetime import datetime, timezone


class EventUser(HttpUser):
    wait_time = between(0.001, 0.002)
    host = "http://127.0.0.1:8000"

    @task
    def send_event(self):
        event = {
            "event_name": "video_play",
            "profile_id": "user_123",
            "device_ip": "192.168.1.1",
            "event_datetime_str": datetime.now(timezone.utc).isoformat(),
            "content_id": "movie_456"
        }
        self.client.post("/event", json=event)

# locust --host=http://127.0.0.1:8000
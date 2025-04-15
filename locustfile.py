from locust import HttpUser, task, between, constant, events
from datetime import datetime, timezone
import random
import logging
import uuid

# Настройка логирования
logger = logging.getLogger("locust")


class EventUser(HttpUser):
    wait_time = constant(0.001)  # Минимальная задержка
    fixed_count = 800  # Фиксированное число запросов
    host = "http://127.0.0.1:8000"

    # Параметры теста
    RPS_TARGET = 800  # Целевая нагрузка
    TEST_DURATION = 300  # Длительность теста в секундах

    def on_start(self):
        """Инициализация перед тестом"""
        self.user_id = str(uuid.uuid4())
        self.content_ids = [f"content_{i}" for i in range(1, 101)]

    @task
    def send_event(self):
        """Основная задача для отправки события"""
        event = {
            "event_name": random.choice(["video_play", "video_pause", "page_view"]),
            "event_datetime": datetime.now(timezone.utc).isoformat(),
            "profile_id": f"user_{random.randint(1, 10000)}",
            "device_ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "raw_data": {
                "content_id": random.choice(self.content_ids),
                "quality": random.choice(["HD", "4K", "SD"]),
                "playback_time": random.randint(0, 3600)
            }
        }

        with self.client.post(
                "/events",
                json=event,
                catch_response=True,
                name="Send Event"
        ) as response:
            if response.status_code != 200:
                logger.error(f"Error: {response.status_code} - {response.text}")


# Хук для анализа результатов
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    stats = environment.stats.total
    rps = stats.get_current_rps()

    print("\n=== ИТОГОВАЯ СТАТИСТИКА ===")
    print(f"Целевая RPS: {EventUser.RPS_TARGET}")
    print(f"Достигнутая RPS: {rps:.2f}")
    print(f"Всего запросов: {stats.num_requests}")
    print(f"Успешных: {stats.num_requests - stats.num_failures}")
    print(f"Ошибок: {stats.num_failures}")
    print(f"Среднее время ответа: {stats.avg_response_time:.2f}ms")
    print(f"Максимальное время ответа: {stats.max_response_time:.2f}ms")

    if rps < EventUser.RPS_TARGET * 0.9:  # 90% от цели
        logger.warning(f"Предупреждение: RPS ниже целевого ({rps:.2f} < {EventUser.RPS_TARGET})")

# locust -f locustfile.py --headless --users 100 --spawn-rate 50 --run-time 5m
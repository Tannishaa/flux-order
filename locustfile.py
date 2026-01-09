from locust import HttpUser, task, between

class FlashSaleUser(HttpUser):
    # Each user waits between 1 and 3 seconds before clicking buy again
    # This simulates real human chaos
    wait_time = between(1, 3)

    @task
    def buy_ticket(self):
        # The payload (User trying to buy ticket_1)
        # We use a random user ID so it looks like different people
        self.client.post("/buy", json={
            "user_id": f"user_{self.environment.runner.user_count}", 
            "item_id": "ticket_1"
        })
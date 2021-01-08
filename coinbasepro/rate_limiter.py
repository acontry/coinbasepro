import threading
import time

from coinbasepro.token_bucket import TokenBucket


class RateLimiter:
    """Simple thread-safe rate limiter.

    Can be configured with a burst size and long term rate limit.
    """

    def __init__(self, burst_size: int, rate_limit: int):
        self.lock = threading.Lock()
        self.token_bucket = TokenBucket(
            max_amount=burst_size, refill_period=1.0, refill_amount=rate_limit
        )

    def rate_limit(self):
        """Blocks until a token can be obtained from the bucket."""
        with self.lock:
            while not self.token_bucket.reduce(tokens=1):
                time.sleep(self.token_bucket.time_to_next_token())

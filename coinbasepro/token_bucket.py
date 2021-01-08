import time


class TokenBucket:
    """Token bucket for rate-limiting.

    The token bucket algorithm provides rate-limiting with
    burstiness. The amount of burst and longer term rate
    limit allowed is determined by the bucket size and refill
    time/amount.
    """

    def __init__(self, max_amount: int, refill_period: float, refill_amount: int):
        """Create a token bucket.

        Args:
            max_amount: Maximum amount that bucket can hold.
            refill_period: Number of seconds between refills.
            refill_amount: Amount to refill each time.

        """
        self.max_amount = max_amount
        self.refill_period = refill_period
        self.refill_amount = refill_amount
        self.value = 0
        self.last_update = 0
        self.reset()

    def _refill_count(self):
        """Get number of refills to perform."""
        return int(((time.monotonic() - self.last_update) / self.refill_period))

    def time_to_next_token(self):
        """Time remaining until next token is added to the bucket."""
        return (
            self.last_update
            + self.refill_period
            - time.monotonic()
            - self._refill_count() * self.refill_period
        )

    def reset(self):
        """Reset bucket."""
        self.value = self.max_amount
        self.last_update = time.monotonic()

    def get(self):
        """Get count of bucket."""
        return min(
            self.max_amount, self.value + self._refill_count() * self.refill_amount
        )

    def reduce(self, tokens: int):
        """Reduce bucket count by tokens.

        Returns True if successful.
        """
        refill_count = self._refill_count()
        self.value += refill_count * self.refill_amount
        self.last_update += refill_count * self.refill_period

        if self.value >= self.max_amount:
            self.reset()
        if tokens > self.value:
            return False

        self.value -= tokens
        return True

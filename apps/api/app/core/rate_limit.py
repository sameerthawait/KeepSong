import time
from collections import defaultdict
from fastapi import HTTPException, status

class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 5, window_seconds: int = 900):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Maps key -> list of attempt timestamps
        self.history: dict[str, list[float]] = defaultdict(list)

    def check_rate_limit(self, key: str):
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean up old timestamps for this key
        self.history[key] = [t for t in self.history[key] if t > window_start]
        
        if len(self.history[key]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.history[key][0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts. Please try again later.",
                headers={"Retry-After": str(max(1, retry_after))}
            )

    def record_attempt(self, key: str):
        now = time.time()
        self.history[key].append(now)

    def reset(self, key: str):
        if key in self.history:
            del self.history[key]

# Global instance for Patient PIN rate-limiting (5 attempts per 15 minutes)
pin_rate_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=900)

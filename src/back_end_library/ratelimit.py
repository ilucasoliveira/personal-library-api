"""Limite simples de tentativas, em memória (a API roda em uma instância só no Render).

Não substitui um limitador distribuído, mas barra força bruta em senhas e cadastros em massa.
"""
import time
from collections import defaultdict, deque

from fastapi import Request

from .errors import ApiError


class RateLimiter:
    def __init__(self, max_hits: int, window_seconds: int):
        self.max_hits = max_hits
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)

    def _prune(self, key: str) -> deque:
        bucket = self.hits[key]
        limit = time.monotonic() - self.window
        while bucket and bucket[0] < limit:
            bucket.popleft()
        return bucket

    def check(self, key: str):
        if len(self._prune(key)) >= self.max_hits:
            raise ApiError(429, "too_many_requests", "Too many attempts. Try again later.")

    def hit(self, key: str):
        self._prune(key).append(time.monotonic())

    def reset(self, key: str):
        self.hits.pop(key, None)

    def clear(self):
        self.hits.clear()


def client_ip(request: Request) -> str:
    # no Render a API fica atrás de um proxy; o IP real vem no X-Forwarded-For
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# 5 senhas erradas por email a cada 15 minutos
failed_logins = RateLimiter(max_hits=5, window_seconds=15 * 60)
# 5 contas novas por IP por hora
signups = RateLimiter(max_hits=5, window_seconds=60 * 60)

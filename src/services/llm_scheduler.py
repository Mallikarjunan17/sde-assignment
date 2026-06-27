from collections import deque
from dataclasses import dataclass
from threading import Lock
import time

from src.config import settings


@dataclass
class ScheduledJob:
    interaction_id: str
    customer_id: str
    priority: str
    estimated_tokens: int


class LLMScheduler:

    def __init__(self):

        self.lock = Lock()

        self.available_tokens = settings.LLM_TOKENS_PER_MINUTE

        self.available_requests = settings.LLM_REQUESTS_PER_MINUTE

        self.last_reset = time.time()

        self.customer_usage = {}

        self.deferred_queue = deque()

    def reset_if_required(self):

        now = time.time()

        if now - self.last_reset >= 60:

            self.available_tokens = settings.LLM_TOKENS_PER_MINUTE

            self.available_requests = settings.LLM_REQUESTS_PER_MINUTE

            self.customer_usage.clear()

            self.last_reset = now

    def estimate_tokens(self, transcript: str):

        words = len(transcript.split())

        estimated = max(500, words * 2)

        return estimated

    def can_process(self, customer_id, estimated_tokens):

        self.reset_if_required()

        customer_used = self.customer_usage.get(customer_id, 0)

        customer_limit = (
            settings.LLM_TOKENS_PER_MINUTE // 4
        )

        if customer_used + estimated_tokens > customer_limit:

            return False

        if estimated_tokens > self.available_tokens:

            return False

        if self.available_requests <= 0:

            return False

        return True

    def acquire(self, customer_id, estimated_tokens):

        with self.lock:

            if not self.can_process(
                customer_id,
                estimated_tokens,
            ):

                return False

            self.available_tokens -= estimated_tokens

            self.available_requests -= 1

            self.customer_usage[customer_id] = (
                self.customer_usage.get(customer_id, 0)
                + estimated_tokens
            )

            return True

    def release(self):

        pass

    def defer(self, job):

        self.deferred_queue.append(job)

    def queue_depth(self):

        return len(self.deferred_queue)


llm_scheduler = LLMScheduler()
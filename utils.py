import time, numpy as np, threading
from concurrent.futures import ThreadPoolExecutor
import math, os


_RESPONSES = [
    "Thank you for your email. I will get back to you shortly.",
    "I appreciate your message, and I'll respond as soon as possible.",
    "Your inquiry has been received. I'll review it and reply soon.",
    "Thanks for reaching out. Expect a detailed response shortly."
]
_counter = 0
_lock = threading.Lock()

def llm(subject: str) -> str:
    global _counter
    time.sleep(np.clip(np.random.exponential(0.5), 0.4, 0.6))
    with _lock:
        text = _RESPONSES[_counter % len(_RESPONSES)]
        _counter += 1
    return f"Re: {subject}\n\n{text}"


def enforce_gap(last_sent_ts: float | None):
    if last_sent_ts is None: return
    while (time.perf_counter_ns() - last_sent_ts) < 100_000:  # 100 µs
        pass

_AVG_LLM_LAT = 0.50                 # 0.4-0.6 s range ⇒ ≈ 0.5 s
_MAX_THREADS = int(os.getenv("MAX_THREADS", "512"))

def _suggest_pool_size(n_emails: int, max_deadline: float) -> int:
    """
    ceil(total_work / time_budget)  where total_work = n_emails * avg_latency
    """
    need = math.ceil(n_emails * _AVG_LLM_LAT / max_deadline)
    return min(max(need, 10), _MAX_THREADS)

_llm_pool_size = _suggest_pool_size(
    n_emails = int(os.getenv("BATCH_HINT", "0") or 1),    # can override in .env
    max_deadline = float(os.getenv("MAX_DEADLINE_HINT", "1.5"))
)
llm_pool = ThreadPoolExecutor(max_workers=_llm_pool_size)
import os, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MAX_HTTP_POOL = int(os.getenv("HTTP_POOL_SIZE", "300"))

_session = requests.Session()
adapter  = HTTPAdapter(
    pool_connections=MAX_HTTP_POOL,   # total pools
    pool_maxsize   = MAX_HTTP_POOL,   # per-host socket cap
    pool_block     = True,            # wait instead of warn/discard
    max_retries    = Retry(total=3, backoff_factor=0.2),  # optional
)

_session.mount("https://", adapter)
_session.mount("http://",  adapter)

import os, time, logging
from dotenv import load_dotenv
from fetch import fetch_emails
from dependencies import topo_sort
from utils import llm, _suggest_pool_size, enforce_gap
from respond import post_response
from concurrent.futures import ThreadPoolExecutor


load_dotenv()
level = os.getenv("LOG_LEVEL", "DEBUG").upper()

logging.basicConfig(
    level=getattr(logging, level, logging.DEBUG),
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.StreamHandler(),                # console
        logging.FileHandler("run.log", "w")     # file
    ]
)

TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

def main() -> None:
    emails = fetch_emails()
    dep_sorted = topo_sort(emails)
    emails_sorted = sorted(dep_sorted, key=lambda e: float(e["deadline"]))

    max_dl = max(float(e["deadline"]) for e in emails_sorted)
    need_thr = _suggest_pool_size(len(emails_sorted), max_dl)

    from utils import llm_pool          
    if need_thr > llm_pool._max_workers:
        llm_pool._max_workers = need_thr    

    fetched_at = time.time()

    futures = {e["email_id"]: llm_pool.submit(llm, e["subject"]) for e in emails_sorted}

    poster  = ThreadPoolExecutor(max_workers=need_thr)   

    for email in emails_sorted:
        body = futures[email["email_id"]].result()

        poster.submit(post_response, email["email_id"], body)

        elapsed = time.time() - fetched_at
        if elapsed > float(email["deadline"]):
            logging.warning("MISSED deadline  %.3fs (limit %.3fs)  %s",
                            elapsed, float(email["deadline"]), email["email_id"])
        else:
            logging.debug("On-time         %.3fs / %.3fs  %s",
                          elapsed, float(email["deadline"]), email["email_id"])

    poster.shutdown(wait=True)
    llm_pool.shutdown(wait=True)
    logging.info("Done – processed %s emails", len(emails_sorted))


if __name__ == "__main__":
    main()

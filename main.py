import os, time, logging
from dotenv import load_dotenv
from fetch import fetch_emails
from dependencies import topo_sort
from utils import llm, _suggest_pool_size, enforce_gap
from respond import post_response
from concurrent.futures import ThreadPoolExecutor, as_completed


load_dotenv()
level = os.getenv("LOG_LEVEL", "DEBUG").upper()

logging.basicConfig(
    level=getattr(logging, level, logging.DEBUG),
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[
        logging.StreamHandler(),                
        logging.FileHandler("run.log", "w")
    ]
)

TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

def main() -> None:
    emails = fetch_emails()
    emails_sorted = topo_sort(emails)

    max_dl = max(float(e["deadline"]) for e in emails_sorted)
    need_thr = _suggest_pool_size(len(emails_sorted), max_dl)

    from utils import llm_pool          
    if need_thr > llm_pool._max_workers:
        llm_pool._max_workers = need_thr    

    poster = ThreadPoolExecutor(max_workers=need_thr)
    last_sent_ns = None

    fetched_at = time.time()
    sent_ids = set()
    id_to_email = {e["email_id"]: e for e in emails_sorted}
    futures = {}
    future_to_id = {}

    for e in emails_sorted:
        fut = llm_pool.submit(llm, e["subject"])
        futures[e["email_id"]] = fut
        future_to_id[fut] = e["email_id"]

    sent_ids = set()
    waiting_ids = set() 
    last_sent_ns = None


    def try_send(e_id: str) -> bool:
        """
        Post the reply if every dependency has already been sent.
        Also logs a WARNING when we miss the per-e-mail deadline.
        """
        nonlocal last_sent_ns

        email = id_to_email[e_id]
        deps  = [d.strip() for d in email["dependencies"].split(",") if d.strip()]
        if not all(dep in sent_ids for dep in deps):
            return False

        # LLM result ready
        body = futures[e_id].result()
        enforce_gap(last_sent_ns)
        poster.submit(post_response, e_id, body)
        last_sent_ns = time.perf_counter_ns()
        sent_ids.add(e_id)

        # deadline bookkeeping
        elapsed  = time.time() - fetched_at
        deadline = float(email["deadline"])
        if elapsed > deadline:
            logging.warning("MISSED deadline  %.3fs (limit %.3fs)  %s",
                            elapsed, deadline, e_id)
        else:
            logging.debug("On-time         %.3fs / %.3fs  %s",
                        elapsed, deadline, e_id)
        return True

    # concurrent driver
    for fut in as_completed(future_to_id):
        e_id = future_to_id[fut]

        if not try_send(e_id): 
            waiting_ids.add(e_id)
            continue

        # just sent one; maybe some children can now be flushed
        progressed = True
        while progressed:
            progressed = False
            for wid in list(waiting_ids):
                if try_send(wid):
                    waiting_ids.remove(wid)
                    progressed = True

    poster.shutdown(wait=True)
    llm_pool.shutdown(wait=True)
    logging.info("Done – processed %s emails", len(emails_sorted))


if __name__ == "__main__":
    main()

from collections import defaultdict, deque

def topo_sort(emails: list[dict]) -> list[dict]:
    id2email = {e["email_id"]: e for e in emails}
    graph, indeg = defaultdict(list), defaultdict(int)

    for e in emails:
        for d in filter(None, map(str.strip, e["dependencies"].split(","))):
            graph[d].append(e["email_id"])
            indeg[e["email_id"]] += 1

    q = deque([eid for eid in id2email if indeg[eid] == 0])
    order = []
    while q:
        cur = q.popleft()
        order.append(id2email[cur])
        for nxt in graph[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    if len(order) != len(emails):
        raise ValueError("Cycle detected in dependencies")
    return order

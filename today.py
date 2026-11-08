"""Updates dark_mode.svg / light_mode.svg with live GitHub stats.

Env vars:  ACCESS_TOKEN (classic PAT: repo + read:user)   USER_NAME (GitHub login)
"""
import datetime
import json
import os
import time
from xml.etree import ElementTree as ET

import requests
from dateutil import relativedelta

USER_NAME = os.environ.get("USER_NAME", "Ahmadbilal-exe")
HEADERS = {"authorization": "token " + os.environ["ACCESS_TOKEN"]}
BIRTHDAY = datetime.datetime(2005, 1, 1)   # TODO: put your real date of birth
WIDTH = 58                                 # must match gen_svg.py
SVG_FILES = ["dark_mode.svg", "light_mode.svg"]
CACHE_FILE = "cache/loc.json"
ET.register_namespace("", "http://www.w3.org/2000/svg")


def gql(query, variables=None):
    for attempt in range(4):
        r = requests.post("https://api.github.com/graphql",
                          json={"query": query, "variables": variables or {}},
                          headers=HEADERS, timeout=60)
        if r.status_code == 200 and "errors" not in r.json():
            return r.json()["data"]
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"GraphQL failed: {r.status_code} {r.text[:300]}")


def user_info():
    d = gql("""query($login:String!){user(login:$login){id createdAt
        followers{totalCount} repositories(ownerAffiliations:OWNER){totalCount}}}""",
            {"login": USER_NAME})["user"]
    return d["id"], d["createdAt"], d["followers"]["totalCount"], d["repositories"]["totalCount"]


def contributions(created_at):
    """(total contributions, total commits) summed year by year since account creation."""
    start = datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    now = datetime.datetime.utcnow()
    total_c = total_k = 0
    for year in range(start.year, now.year + 1):
        frm = max(start, datetime.datetime(year, 1, 1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        to = min(now, datetime.datetime(year, 12, 31, 23, 59, 59)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cc = gql("""query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){
            contributionsCollection(from:$from,to:$to){totalCommitContributions
            contributionCalendar{totalContributions}}}}""",
                 {"login": USER_NAME, "from": frm, "to": to})["user"]["contributionsCollection"]
        total_k += cc["totalCommitContributions"]
        total_c += cc["contributionCalendar"]["totalContributions"]
    return total_c, total_k


def repos():
    out, cursor = [], None
    while True:
        d = gql("""query($login:String!,$cursor:String){user(login:$login){
            repositories(first:100,after:$cursor,ownerAffiliations:[OWNER,COLLABORATOR],isFork:false){
            pageInfo{hasNextPage endCursor} nodes{nameWithOwner stargazerCount
            owner{login}}}}}""", {"login": USER_NAME, "cursor": cursor})["user"]["repositories"]
        out += d["nodes"]
        if not d["pageInfo"]["hasNextPage"]:
            return out
        cursor = d["pageInfo"]["endCursor"]


def repo_loc(name_with_owner, user_id):
    owner, name = name_with_owner.split("/")
    add = dele = count = 0
    cursor = None
    while True:
        d = gql("""query($owner:String!,$name:String!,$id:ID!,$cursor:String){
            repository(owner:$owner,name:$name){defaultBranchRef{target{... on Commit{
            history(first:100,after:$cursor,author:{id:$id}){totalCount
            pageInfo{hasNextPage endCursor} nodes{additions deletions}}}}}}}""",
                {"owner": owner, "name": name, "id": user_id, "cursor": cursor})["repository"]
        if not d or not d["defaultBranchRef"]:
            return 0, 0, 0
        h = d["defaultBranchRef"]["target"]["history"]
        count = h["totalCount"]
        for n in h["nodes"]:
            add += n["additions"]
            dele += n["deletions"]
        if not h["pageInfo"]["hasNextPage"]:
            return count, add, dele
        cursor = h["pageInfo"]["endCursor"]


def loc_stats(repo_list, user_id):
    os.makedirs("cache", exist_ok=True)
    cache = json.load(open(CACHE_FILE)) if os.path.exists(CACHE_FILE) else {}
    add = dele = 0
    for r in repo_list:
        key = r["nameWithOwner"]
        owner, name = key.split("/")
        head = gql("""query($owner:String!,$name:String!,$id:ID!){repository(owner:$owner,name:$name){
            defaultBranchRef{target{... on Commit{history(first:1,author:{id:$id}){totalCount}}}}}}""",
                   {"owner": owner, "name": name, "id": user_id})["repository"]
        if not head or not head["defaultBranchRef"]:
            continue
        total = head["defaultBranchRef"]["target"]["history"]["totalCount"]
        if key not in cache or cache[key]["count"] != total:
            c, a, d = repo_loc(key, user_id)
            cache[key] = {"count": c, "add": a, "del": d}
        add += cache[key]["add"]
        dele += cache[key]["del"]
    json.dump(cache, open(CACHE_FILE, "w"), indent=1)
    return add, dele


def uptime():
    d = relativedelta.relativedelta(datetime.datetime.today(), BIRTHDAY)
    f = lambda n, w: f"{n} {w}{'s' if n != 1 else ''}"
    return f"{f(d.years, 'year')}, {f(d.months, 'month')}, {f(d.days, 'day')}"


def set_text(root, el_id, text):
    for el in root.iter():
        if el.get("id") == el_id:
            el.text = text
            return


def justify(root, base, value, key_len, extra=None):
    """Update the value tspan and re-pad its dotted leader to keep the line width constant."""
    vlen = extra if extra is not None else len(value)
    n = WIDTH - key_len - 1 - vlen
    set_text(root, f"{base}_dots", (" " + "." * (n - 2) + " ") if n >= 2 else " " * max(n, 0))
    if extra is None:
        set_text(root, f"{base}_data", value)


def update_svgs(s):
    for f in SVG_FILES:
        tree = ET.parse(f)
        root = tree.getroot()
        justify(root, "age", s["age"], len("Uptime"))
        justify(root, "repo", s["repos"], len("Repos"))
        justify(root, "contrib", s["contrib"], len("Contributions"))
        justify(root, "star", s["stars"], len("Stars"))
        justify(root, "follower", s["followers"], len("Followers"))
        justify(root, "commit", s["commits"], len("Commits"))
        set_text(root, "loc_data", s["loc"])
        set_text(root, "loc_add", s["add"])
        set_text(root, "loc_del", s["del"])
        loc_len = len(s["loc"]) + len(" ( ") + len(s["add"]) + len("++, ") + len(s["del"]) + len("-- )")
        justify(root, "loc", "", len("Lines of Code"), extra=loc_len)
        tree.write(f, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    uid, created, followers, _ = user_info()
    repo_list = repos()
    contrib, commits = contributions(created)
    add, dele = loc_stats(repo_list, uid)
    owned = [r for r in repo_list if r["owner"]["login"].lower() == USER_NAME.lower()]
    fmt = lambda n: f"{n:,}"
    update_svgs({
        "age": uptime(),
        "repos": fmt(len(owned)),
        "contrib": fmt(contrib),
        "stars": fmt(sum(r["stargazerCount"] for r in owned)),
        "followers": fmt(followers),
        "commits": fmt(commits),
        "loc": fmt(add - dele),
        "add": fmt(add),
        "del": fmt(dele),
    })
    print("Updated.")

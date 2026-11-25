"""Fetch WoW character data from Blizzard's API and write characters.json.

Reads BNET_ID and BNET_SECRET from the environment (GitHub Actions secrets).
Output is public Armory data only: no credentials are ever written.
"""
import base64
import json
import os
import time
import urllib.request

CID, CS = os.environ["BNET_ID"], os.environ["BNET_SECRET"]

# key -> (API path, namespace)
CHARS = {
    "osimbs-retail": ("icecrown/osimbs", "profile-us"),
    "osimbs-osimbs": ("osimbs-osimbs", "profile-forever-us"),
}


def token():
    req = urllib.request.Request(
        "https://oauth.battle.net/token",
        data=b"grant_type=client_credentials",
        headers={"Authorization": "Basic " + base64.b64encode(f"{CID}:{CS}".encode()).decode()},
    )
    return json.load(urllib.request.urlopen(req, timeout=20))["access_token"]


def get(slug, ns, path, tok):
    url = f"https://us.api.blizzard.com/profile/wow/character/{slug}{path}?namespace={ns}&locale=en_US"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=20))
    except Exception:
        return None


def profs(pr):
    out = []
    for kind in ("primaries", "secondaries"):
        for x in pr.get(kind, []) or []:
            t = (x.get("tiers") or [{}])[-1]
            out.append({
                "name": (x.get("profession") or {}).get("name"),
                "skill": t.get("skill_points", x.get("skill_points")),
                "max": t.get("max_skill_points", x.get("max_skill_points")),
                "tier": (t.get("tier") or {}).get("name"),
                "secondary": kind == "secondaries",
            })
    return [p for p in out if p["name"] and p["max"]]


def name(obj):
    return (obj or {}).get("name")


def main():
    tok = token()
    old = {}
    if os.path.exists("characters.json"):
        with open("characters.json") as f:
            old = json.load(f).get("characters", {})
    result = {}
    for key, (slug, ns) in CHARS.items():
        p = get(slug, ns, "", tok)
        if not p:
            if key in old:
                result[key] = old[key]  # keep last good data on a failed lookup
            continue
        e = get(slug, ns, "/equipment", tok) or {}
        pr = get(slug, ns, "/professions", tok) or {}
        out = {
            "name": p.get("name"), "surname": p.get("surname"), "level": p.get("level"),
            "xp": p.get("experience"), "race": name(p.get("race")), "class": name(p.get("character_class")),
            "spec": name(p.get("active_spec")), "realm": name(p.get("realm")),
            "faction": name(p.get("faction")), "guild": name(p.get("guild")),
            "ilvlAvg": p.get("average_item_level"), "ilvlEquipped": p.get("equipped_item_level"),
            "lastLogin": p.get("last_login_timestamp"),
            "gear": [{"slot": i["slot"]["name"], "name": i.get("name"), "quality": name(i.get("quality")),
                      "ilvl": (i.get("level") or {}).get("value")} for i in e.get("equipped_items", [])],
            "professions": profs(pr) or None,
        }
        result[key] = {k: v for k, v in out.items() if v is not None}
    # Only stamp a new sync time when something changed, so unchanged runs make no commit.
    if result == old:
        print("No changes")
        return
    with open("characters.json", "w") as f:
        json.dump({"syncedAt": int(time.time() * 1000), "characters": result}, f, indent=1)
    print("Updated:", ", ".join(result))


if __name__ == "__main__":
    main()

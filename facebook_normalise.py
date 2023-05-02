import csv
import re
from urllib.parse import parse_qs, urlencode, urlparse

import requests

profile_id = re.compile(r"^@?((?:profile\.php\?id=)?[-.\w%/]+)$")
valid_domains = ["facebook.com", "facebook.de", "facebook.es", "fb.com", "fb.me", "m.me"]


def fetch_page(key: str, page: int) -> dict:
    return requests.get(
        f"https://taginfo.openstreetmap.org/api/4/key/values?key={key}&filter=all&lang=en&sortname=count&sortorder=desc&rp=999&page={page}"
    ).json()


def clean_url(url_str: str) -> str:
    for bad_type in ["/sharer.php", "/share.php"]:
        if bad_type in url_str:
            return None

    if not re.match("^https?://", url_str):
        url_str = f"https://{url_str}"

    url = urlparse(url_str)

    if url.path in ["/profile.php", "/group.php"]:
        # Just copy id/gid param eg https://www.facebook.com/profile.php?id=100057371322568
        query = parse_qs(url.query)
        clean_query = {}
        for k, v in query.items():
            if k in ["id", "gid"]:
                clean_query[k] = v[0]
        url = url._replace(scheme="https", netloc="www.facebook.com", query=urlencode(clean_query), fragment="")
    else:
        # Just copy the path eg https://www.facebook.com/Ernstingsfamily/
        url = url._replace(scheme="https", netloc="www.facebook.com", query="", fragment="")
    return url.geturl()


if __name__ == "__main__":
    csvwriter = csv.writer(open("out.csv", "w"))
    csvwriter.writerow(["parsed", "osm_key", "osm_value", "normalised_value"])

    for key in ["contact:facebook", "facebook"]:
        page = 1

        while True:
            values = fetch_page(key, page)
            for value in values["data"]:
                osm_value = value["value"]
                parsed = False
                cleaned_value = None
                for domain in valid_domains:
                    if domain in osm_value.lower():
                        if cleaned_value := clean_url(osm_value):
                            parsed = True
                        break
                else:  # no domain/unknown domain
                    if m := re.match(profile_id, osm_value):
                        cleaned_value = f"https://www.facebook.com/{m.group(1)}"
                        parsed = True

                csvwriter.writerow([parsed, key, osm_value, cleaned_value])

            if len(values["data"]) == values["rp"]:
                page += 1
            else:
                break

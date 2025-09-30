import requests
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from tqdm import tqdm
import os

# ---------- CONFIG ----------
LEAGUE_CODE = "eng.1"   # Premier League (Inglaterra)
START_DATE = "2010-01-01"   # inicio del rango
END_DATE   = "2025-09-28"

OUT_JSONL = f"espn_{LEAGUE_CODE}{START_DATE}_to{END_DATE}.jsonl"
OUT_CSV   = f"espn_{LEAGUE_CODE}{START_DATE}_to{END_DATE}.csv"

# Timing / politeness
SCOREBOARD_SLEEP = 0.25
SUMMARY_SLEEP = 0.6
RETRY_SLEEP = 2.0
MAX_RETRIES = 4
TIMEOUT = 15

# map human league label fallback
LEAGUE_LABELS = {
    "eng.1": "Premier League",
    "esp.1": "LaLiga (España)",
    "fra.1": "Ligue 1"
}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.espn.com/"
})

def daterange(start_date, end_date):
    s = datetime.strptime(start_date, "%Y-%m-%d").date()
    e = datetime.strptime(end_date, "%Y-%m-%d").date()
    d = s
    while d <= e:
        yield d
        d += timedelta(days=1)

def safe_get(url, params=None, max_retries=MAX_RETRIES, timeout=TIMEOUT):
    """GET con reintentos y backoff para errores transitorios"""
    for attempt in range(1, max_retries+1):
        try:
            r = session.get(url, params=params, timeout=timeout)
            if r.status_code == 200:
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                wait = RETRY_SLEEP * attempt
                print(f"HTTP {r.status_code} para {r.url} — reintentando en {wait:.1f}s (intento {attempt}/{max_retries})")
                time.sleep(wait)
                continue
            print(f"HTTP {r.status_code} para {r.url}")
            return r
        except requests.exceptions.RequestException as e:
            wait = RETRY_SLEEP * attempt
            print(f"Error request (intento {attempt}) para {url}: {e} — reintentando en {wait:.1f}s")
            time.sleep(wait)
    return None

def normalize_num(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    s = str(v).strip()
    if s.endswith('%'):
        s = s.replace('%', '').strip()
        try:
            return float(s)
        except:
            return s
    s = s.replace(',', '')
    try:
        if '.' in s:
            return float(s)
        return int(s)
    except:
        return s

def extract_stats_from_summary_json(summary_json):
    out = {
        "posesion_local": None, "posesion_visitante": None,
        "tiros_totales_local": None, "tiros_totales_visitante": None,
        "tiros_a_puerta_local": None, "tiros_a_puerta_visitante": None,
        "corners_local": None, "corners_visitante": None,
        "tarjetas_amarillas_local": None, "tarjetas_amarillas_visitante": None,
        "tarjetas_rojas_local": None, "tarjetas_rojas_visitante": None
    }
    try:
        box = summary_json.get("boxscore") or {}
        teams = box.get("teams") or []
        for team in teams:
            is_home = team.get("homeAway") == "home"
            stats_list = team.get("statistics") or []
            for s in stats_list:
                name = (s.get("name") or "").lower()
                val = s.get("displayValue") if s.get("displayValue") is not None else s.get("value")
                if val is None:
                    continue
                if "possession" in name:
                    out["posesion_local" if is_home else "posesion_visitante"] = normalize_num(val)
                elif "total" in name and "shot" in name:
                    out["tiros_totales_local" if is_home else "tiros_totales_visitante"] = normalize_num(val)
                elif "on target" in name:
                    out["tiros_a_puerta_local" if is_home else "tiros_a_puerta_visitante"] = normalize_num(val)
                elif "corner" in name:
                    out["corners_local" if is_home else "corners_visitante"] = normalize_num(val)
                elif "yellow" in name:
                    out["tarjetas_amarillas_local" if is_home else "tarjetas_amarillas_visitante"] = normalize_num(val)
                elif "red" in name:
                    out["tarjetas_rojas_local" if is_home else "tarjetas_rojas_visitante"] = normalize_num(val)
        return out
    except Exception as e:
        print("Error extrayendo stats:", e)
        return out

def parse_event_basic(event):
    rec = {
        "match_id": None,
        "fecha": None,
        "liga": LEAGUE_LABELS.get(LEAGUE_CODE, LEAGUE_CODE),
        "equipo_local": None,
        "equipo_visitante": None,
        "goles_local": None,
        "goles_visitante": None,
    }
    try:
        rec["match_id"] = str(event.get("id") or "")
        rec["fecha"] = (event.get("date") or "").split("T")[0]
        comps = event.get("competitions") or []
        if comps:
            comp = comps[0]
            for team in comp.get("competitors", []):
                is_home = team.get("homeAway") == "home"
                tname = team.get("team", {}).get("displayName")
                score = team.get("score")
                rec["equipo_local" if is_home else "equipo_visitante"] = tname
                rec["goles_local" if is_home else "goles_visitante"] = int(score) if score else None
        return rec
    except Exception as e:
        print("Error parse_event_basic:", e)
        return rec

def scrape_range(start_date, end_date, league_code):
    if os.path.exists(OUT_JSONL):
        os.remove(OUT_JSONL)
    open(OUT_JSONL, "a", encoding="utf-8").close()

    processed = set()
    records = []
    dates = list(daterange(start_date, end_date))
    for d in tqdm(dates, desc="Fechas"):
        datestr = d.strftime("%Y%m%d")
        scoreboard_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/scoreboard"
        resp = safe_get(scoreboard_url, params={"dates": datestr})
        time.sleep(SCOREBOARD_SLEEP)
        if not resp:
            continue
        try:
            data = resp.json()
        except Exception as e:
            print("JSON decode error scoreboard:", e)
            continue

        events = data.get("events") or []
        for event in events:
            basic = parse_event_basic(event)
            mid = basic["match_id"]
            if not mid or mid in processed:
                continue
            processed.add(mid)

            summary_url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league_code}/summary"
            sresp = safe_get(summary_url, params={"event": mid})
            time.sleep(SUMMARY_SLEEP)
            summary_json = sresp.json() if sresp else {}

            stats = extract_stats_from_summary_json(summary_json)
            rec = {**basic, **stats}
            records.append(rec)
            try:
                with open(OUT_JSONL, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception as e:
                print("Error escribiendo JSONL:", e)

    return records

def main():
    print(" Scraping ESPN API")
    print(f"Liga: {LEAGUE_LABELS.get(LEAGUE_CODE, LEAGUE_CODE)}")
    print(f"Rango: {START_DATE} -> {END_DATE}")
    start = time.time()
    recs = scrape_range(START_DATE, END_DATE, LEAGUE_CODE)
    end = time.time()
    total = len(recs)
    print(f"\n Proceso finalizado. Partidos extraídos: {total}")
    print(f"Tiempo: {end - start:.1f}s")

    if recs:
        df = pd.DataFrame(recs)
        df.to_csv(OUT_CSV, index=False, encoding="utf-8-sig")
        print(f" Guardado CSV: {OUT_CSV}")
        print(f" Guardado JSONL: {OUT_JSONL}")

if __name__ == "__main__":
    main()

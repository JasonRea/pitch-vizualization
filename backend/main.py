import asyncio
import os
import sys
from datetime import datetime, timezone

import httpx
from cachetools import TTLCache
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Allow importing fetch_data from repo root when running from backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Pitch Viz API")

ALLOWED_ORIGIN   = os.getenv("ALLOWED_ORIGIN", "*")
GITHUB_TOKEN     = os.environ["GITHUB_TOKEN"]
GITHUB_OWNER     = os.environ["GITHUB_OWNER"]
GITHUB_REPO      = os.environ["GITHUB_REPO"]
DO_SPACES_REGION = os.environ["DO_SPACES_REGION"]
DO_SPACES_BUCKET = os.environ["DO_SPACES_BUCKET"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

PITCH_COLORS = {
    "FF": "#FF007D", "FA": "#FF007D", "SI": "#98165D", "FC": "#BE5FA0",
    "CH": "#F79E70", "FS": "#FE6100", "SC": "#F08223", "FO": "#FFB000",
    "SL": "#67E18D", "ST": "#1BB999", "SV": "#376748", "KC": "#311D8B",
    "CU": "#3025CE", "CS": "#274BFC", "EP": "#648FFF", "KN": "#867A08",
    "PO": "#472C30", "UN": "#9C8975",
}

PITCH_NAMES = {
    "FF": "4-Seam Fastball", "FA": "Fastball",       "SI": "Sinker",
    "FC": "Cutter",          "CH": "Changeup",        "FS": "Splitter",
    "SC": "Screwball",       "FO": "Forkball",        "SL": "Slider",
    "ST": "Sweeper",         "SV": "Slurve",          "KC": "Knuckle Curve",
    "CU": "Curveball",       "CS": "Slow Curve",      "EP": "Eephus",
    "KN": "Knuckleball",     "PO": "Pitch Out",       "UN": "Unknown",
}

# TTL caches — MLB roster refreshes hourly, pitch data valid for the day
_players_cache:    TTLCache = TTLCache(maxsize=1,   ttl=3600)
_pitch_type_cache: TTLCache = TTLCache(maxsize=500, ttl=3600)

# In-memory run inputs (survives for the lifetime of the process)
_render_jobs: dict[int, dict] = {}

_GH_HEADERS = {
    "Authorization":        f"Bearer {GITHUB_TOKEN}",
    "Accept":               "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ---------------------------------------------------------------------------
# GET /pitchers?q={name}
# ---------------------------------------------------------------------------

@app.get("/pitchers")
async def search_pitchers(q: str = ""):
    if not q or len(q) < 2:
        return []

    if "roster" not in _players_cache:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                "https://statsapi.mlb.com/api/v1/sports/1/players",
                params={"season": 2026, "gameType": "R"},
                timeout=15,
            )
            r.raise_for_status()
        _players_cache["roster"] = [
            p for p in r.json().get("people", [])
            if p.get("primaryPosition", {}).get("type") == "Pitcher"
        ]

    q_lower = q.lower()
    return [
        {
            "mlbam_id":  p["id"],
            "full_name": p["fullName"],
            "team":      p.get("currentTeam", {}).get("abbreviation", ""),
        }
        for p in _players_cache["roster"]
        if q_lower in p["fullName"].lower()
    ][:10]


# ---------------------------------------------------------------------------
# GET /dates?pitcher_name={name}&season={year}
# ---------------------------------------------------------------------------

@app.get("/dates")
async def get_dates(pitcher_name: str, season: int = 2026):
    loop = asyncio.get_event_loop()

    def _lookup_id() -> int:
        import pybaseball
        parts = pitcher_name.split(" ", 1)
        first, last = (parts[0], parts[1]) if len(parts) == 2 else (parts[0], "")
        result = pybaseball.playerid_lookup(last, first, fuzzy=True)
        if result.empty:
            raise ValueError("not found")
        return int(result["key_mlbam"].head(1).item())

    try:
        player_id = await loop.run_in_executor(None, _lookup_id)
    except ValueError:
        raise HTTPException(404, detail="Pitcher not found")
    except Exception:
        raise HTTPException(500, detail="Failed to look up pitcher")

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "season": season, "group": "pitching"},
            timeout=15,
        )
        r.raise_for_status()

    splits = (r.json().get("stats") or [{}])[0].get("splits", [])
    return [
        {
            "date":      s["date"],
            "opponent":  s.get("opponent", {}).get("abbreviation", ""),
            "home_away": "home" if s.get("isHome") else "away",
        }
        for s in splits
    ]


# ---------------------------------------------------------------------------
# GET /pitch-types?pitcher_name={name}&date={YYYY-MM-DD}
# ---------------------------------------------------------------------------

@app.get("/pitch-types")
async def get_pitch_types(pitcher_name: str, date: str):
    cache_key = f"{pitcher_name}:{date}"
    if cache_key in _pitch_type_cache:
        return _pitch_type_cache[cache_key]

    loop = asyncio.get_event_loop()

    def _fetch() -> list[dict]:
        from fetch_data import pitch_data
        df = pitch_data(date, pitcher_name)
        if df.empty:
            return []
        rows = (
            df[["pitch_type", "pitch_name"]]
            .dropna()
            .drop_duplicates("pitch_type")
        )
        result = []
        for _, row in rows.iterrows():
            code = row["pitch_type"]
            result.append({
                "code":  code,
                "name":  row.get("pitch_name") or PITCH_NAMES.get(code, code),
                "color": PITCH_COLORS.get(code, "#9C8975"),
                "count": int((df["pitch_type"] == code).sum()),
            })
        result.sort(key=lambda x: -x["count"])
        return result

    try:
        result = await loop.run_in_executor(None, _fetch)
    except Exception as e:
        raise HTTPException(500, detail=f"Failed to fetch pitch data: {e}")

    _pitch_type_cache[cache_key] = result
    return result


# ---------------------------------------------------------------------------
# POST /render
# ---------------------------------------------------------------------------

class RenderRequest(BaseModel):
    pitcher_name: str
    date:         str
    split:        str = "all"
    pitch_type:   str = ""
    quality:      str = "low_quality"


@app.post("/render")
async def trigger_render(req: RenderRequest):
    before_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
            f"/actions/workflows/render_trajectory.yml/dispatches",
            headers=_GH_HEADERS,
            json={
                "ref": "main",
                "inputs": {
                    "pitcher_name": req.pitcher_name,
                    "date":         req.date,
                    "split":        req.split or "all",
                    "pitch_type":   req.pitch_type or "",
                    "quality":      req.quality or "low_quality",
                },
            },
            timeout=15,
        )
    if r.status_code != 204:
        raise HTTPException(502, detail=f"GitHub API error {r.status_code}: {r.text}")

    # Poll up to ~12s for the newly created run to appear
    run_id: int | None = None
    async with httpx.AsyncClient() as client:
        for _ in range(6):
            await asyncio.sleep(2)
            r = await client.get(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs",
                headers=_GH_HEADERS,
                params={
                    "workflow_id": "render_trajectory.yml",
                    "event":       "workflow_dispatch",
                    "created":     f">={before_ts}",
                },
                timeout=10,
            )
            runs = r.json().get("workflow_runs", [])
            if runs:
                run_id = runs[0]["id"]
                break

    if run_id is None:
        raise HTTPException(504, detail="Timed out waiting for GitHub Actions run to start")

    _render_jobs[run_id] = {
        "pitcher_name": req.pitcher_name,
        "date":         req.date,
        "split":        req.split or "all",
        "pitch_type":   req.pitch_type or "all",
    }

    return {"run_id": run_id}


# ---------------------------------------------------------------------------
# GET /render/{run_id}
# ---------------------------------------------------------------------------

_SKIP_STEPS = {"Set up job", "Complete job"}


def _map_step_status(step: dict) -> str:
    gh_status   = step.get("status", "queued")
    conclusion  = step.get("conclusion")
    if gh_status == "in_progress":
        return "running"
    if gh_status == "completed":
        return "done" if conclusion == "success" else "failed"
    return "pending"


@app.get("/render/{run_id}")
async def get_render_status(run_id: int):
    async with httpx.AsyncClient() as client:
        run_resp, jobs_resp = await asyncio.gather(
            client.get(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}",
                headers=_GH_HEADERS,
                timeout=10,
            ),
            client.get(
                f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}/jobs",
                headers=_GH_HEADERS,
                timeout=10,
            ),
        )

    if run_resp.status_code == 404:
        raise HTTPException(404, detail="Run not found")
    run_resp.raise_for_status()

    run        = run_resp.json()
    status     = run["status"]
    conclusion = run.get("conclusion")

    # Extract steps from the first job, filtering out GitHub infrastructure noise
    steps: list[dict] = []
    if jobs_resp.status_code == 200:
        jobs = jobs_resp.json().get("jobs", [])
        if jobs:
            steps = [
                {"name": s["name"], "status": _map_step_status(s)}
                for s in jobs[0].get("steps", [])
                if s.get("name") not in _SKIP_STEPS
            ]

    output_url = None
    if status == "completed" and conclusion == "success":
        job          = _render_jobs.get(run_id, {})
        pitcher_slug = job.get("pitcher_name", "").lower().replace(" ", "_")
        date         = job.get("date", "")
        split        = job.get("split", "all")
        pitch_type   = job.get("pitch_type", "all")
        output_url   = (
            f"https://{DO_SPACES_BUCKET}.{DO_SPACES_REGION}.digitaloceanspaces.com"
            f"/vizualizations/trajectories/{date}/{pitcher_slug}-{split}-{pitch_type}.mp4"
        )

    api_status = {
        "queued":      "queued",
        "in_progress": "in_progress",
        "completed":   "completed" if conclusion == "success" else "failed",
    }.get(status, status)

    return {"status": api_status, "output_url": output_url, "steps": steps}

# Pitch Viz API

FastAPI backend that powers the [pitch trajectory web UI](../frontend/). It handles pitcher search, game date lookup, pitch type lookup, and proxies render jobs to GitHub Actions.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/pitchers?q={name}` | Search active MLB pitchers by name (min 2 chars) |
| `GET` | `/dates?pitcher_name={name}&season={year}` | Get dates the pitcher appeared in games |
| `GET` | `/pitch-types?pitcher_name={name}&date={YYYY-MM-DD}` | Get pitch types thrown in a specific outing |
| `POST` | `/render` | Trigger a GitHub Actions render job |
| `GET` | `/render/{run_id}` | Poll render job status |

Interactive docs available at `/docs` when the server is running.

### POST /render — request body

```json
{
  "pitcher_name": "Ranger Suarez",
  "date": "2026-04-18",
  "split": "all",
  "pitch_type": "SL",
  "quality": "low_quality"
}
```

- `split`: `"all"` | `"left"` | `"right"`
- `pitch_type`: 2-letter Statcast code (e.g. `"FF"`, `"SL"`) or `""` for all pitch types
- `quality`: `"low_quality"` | `"medium_quality"` | `"high_quality"` | `"fourk_quality"`

Returns `{ "run_id": 12345 }`. Poll `/render/{run_id}` every 10s until `status` is `"completed"` or `"failed"`. On success, `output_url` contains the public MP4 link.

## Running locally

From the **repo root**:

```bash
pip install -r backend/requirements.txt
```

Set environment variables:

```bash
export GITHUB_TOKEN=ghp_...          # Fine-grained PAT with Actions: write
export GITHUB_OWNER=your_username
export GITHUB_REPO=pitch-vizualization
export DO_SPACES_REGION=nyc3
export DO_SPACES_BUCKET=your_bucket
export ALLOWED_ORIGIN=http://localhost:5173
```

Start the server:

```bash
uvicorn backend.main:app --reload
```

API is available at `http://localhost:8000`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | Yes | GitHub PAT with `Actions: write` permission |
| `GITHUB_OWNER` | Yes | GitHub username or org that owns the repo |
| `GITHUB_REPO` | Yes | Repository name (e.g. `pitch-vizualization`) |
| `DO_SPACES_REGION` | Yes | DigitalOcean Spaces region (e.g. `nyc3`) |
| `DO_SPACES_BUCKET` | Yes | Spaces bucket name |
| `ALLOWED_ORIGIN` | No | CORS origin for the frontend (defaults to `*`) |

## Deploying to Render.com

A `render.yaml` is included at the repo root. Connect the GitHub repo to Render.com and it will auto-configure the service. Set the 6 env vars above in the Render dashboard (Dashboard → your service → Environment).

The free tier spins down after 15 minutes of inactivity. The first request after idle takes ~30 seconds to cold-start.

## How rendering works

`POST /render` dispatches the `.github/workflows/render_trajectory.yml` workflow via the GitHub API. It then polls for up to 12 seconds to find the new run ID and returns it. The run input is stored in memory so the output URL can be reconstructed when the job finishes.

Output MP4s are uploaded to DigitalOcean Spaces at:
```
vizualizations/trajectories/{date}/{pitcher_slug}-{split}-{pitch_type}.mp4
```

The URL is deterministic from the inputs, so no callback from Actions back to the API is needed.

## Caveats

- **Render.com cold starts** — first request after 15 min idle is slow (~30s).
- **In-memory job store** — `_render_jobs` is lost on server restart. If the server restarts between `/render` and `/render/{run_id}`, the status endpoint won't be able to construct `output_url` (it will return `null` even on success).
- **`/pitch-types` latency** — calls Statcast via pybaseball, takes 3–8 seconds. Results are cached for 1 hour per pitcher+date pair.
- **GitHub Actions PAT** — the token needs `Actions: write` on the target repo. A fine-grained PAT scoped to just that repo is recommended over a classic PAT.

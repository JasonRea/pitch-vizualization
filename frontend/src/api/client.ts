const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`API ${r.status}: ${text}`);
  }
  return r.json() as Promise<T>;
}

export const searchPitchers = (q: string) =>
  fetchJson<{ mlbam_id: number; full_name: string; team: string }[]>(
    `${API_BASE}/pitchers?q=${encodeURIComponent(q)}`
  );

export const getDates = (pitcherName: string, season = 2026) =>
  fetchJson<{ date: string; opponent: string; home_away: string }[]>(
    `${API_BASE}/dates?pitcher_name=${encodeURIComponent(pitcherName)}&season=${season}`
  );

export const getPitchTypes = (pitcherName: string, date: string) =>
  fetchJson<{ code: string; name: string; color: string; count: number }[]>(
    `${API_BASE}/pitch-types?pitcher_name=${encodeURIComponent(pitcherName)}&date=${encodeURIComponent(date)}`
  );

export interface RenderReq {
  pitcher_name: string;
  date: string;
  split: string;
  pitch_type: string;
  quality: string;
}

export const triggerRender = (req: RenderReq) =>
  fetchJson<{ run_id: number }>(`${API_BASE}/render`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

export type StepStatus = "pending" | "running" | "done" | "failed";
export interface RenderStep { name: string; status: StepStatus; }

export const getRenderStatus = (runId: number) =>
  fetchJson<{ status: string; output_url: string | null; steps: RenderStep[] }>(
    `${API_BASE}/render/${runId}`
  );

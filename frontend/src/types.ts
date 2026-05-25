export type BlockType = "pitcher" | "date" | "split" | "pitch_type";

export interface Block {
  id: string;
  type: BlockType;
  label: string;
  value: string;
  color: string;
}

export interface Pitcher {
  mlbam_id: number;
  full_name: string;
  team: string;
}

export interface GameDate {
  date: string;
  opponent: string;
  home_away: string;
}

export interface PitchType {
  code: string;
  name: string;
  color: string;
  count: number;
}

export type Quality = "low_quality" | "medium_quality" | "high_quality" | "fourk_quality";
export type RenderStatus = "idle" | "queued" | "in_progress" | "completed" | "failed";

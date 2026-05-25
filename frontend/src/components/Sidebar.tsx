import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { DraggableBlock } from "./DraggableBlock";
import { searchPitchers, getDates, getPitchTypes } from "@/api/client";
import type { Block } from "@/types";

const SPLIT_BLOCKS: Block[] = [
  { id: "split-all",   type: "split", label: "vs All",   value: "all",   color: "#376748" },
  { id: "split-left",  type: "split", label: "vs Left",  value: "left",  color: "#376748" },
  { id: "split-right", type: "split", label: "vs Right", value: "right", color: "#376748" },
];

function formatDate(dateStr: string, opponent: string, homeAway: string) {
  const d = new Date(`${dateStr}T12:00:00`);
  const label = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  const vs = homeAway === "home" ? "vs" : "@";
  return opponent ? `${label} ${vs} ${opponent}` : label;
}

function SectionHeader({ label }: { label: string }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
      {label}
    </p>
  );
}

interface Props {
  pitcherBlock: Block | null;
  dateBlock: Block | null;
}

export function Sidebar({ pitcherBlock, dateBlock }: Props) {
  const [searchQ, setSearchQ] = useState("");

  const { data: pitchers, isFetching: searchFetching } = useQuery({
    queryKey: ["pitchers", searchQ],
    queryFn: () => searchPitchers(searchQ),
    enabled: searchQ.length >= 2,
  });

  const { data: dates, isFetching: datesFetching } = useQuery({
    queryKey: ["dates", pitcherBlock?.value],
    queryFn: () => getDates(pitcherBlock!.value),
    enabled: !!pitcherBlock,
  });

  const { data: pitchTypes, isFetching: pitchTypesFetching } = useQuery({
    queryKey: ["pitch-types", pitcherBlock?.value, dateBlock?.value],
    queryFn: () => getPitchTypes(pitcherBlock!.value, dateBlock!.value),
    enabled: !!(pitcherBlock && dateBlock),
  });

  return (
    <div className="w-72 shrink-0 border-r flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b">
        <h2 className="font-semibold text-sm text-foreground">Blocks</h2>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 flex flex-col gap-5">

          {/* Pitchers */}
          <div className="flex flex-col gap-2">
            <SectionHeader label="Pitcher" />
            <input
              type="text"
              value={searchQ}
              onChange={(e) => setSearchQ(e.target.value)}
              placeholder="Search by name..."
              className="w-full rounded-md border bg-background px-3 py-1.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
            {searchFetching && (
              <p className="text-xs text-muted-foreground">Searching...</p>
            )}
            {searchQ.length >= 2 && !searchFetching && pitchers?.length === 0 && (
              <p className="text-xs text-muted-foreground">No pitchers found</p>
            )}
            <div className="flex flex-col gap-1.5">
              {(pitchers ?? []).map((p) => {
                const block: Block = {
                  id: `pitcher-${p.mlbam_id}`,
                  type: "pitcher",
                  label: p.team ? `${p.full_name} (${p.team})` : p.full_name,
                  value: p.full_name,
                  color: "#3025CE",
                };
                return <DraggableBlock key={block.id} block={block} />;
              })}
            </div>
          </div>

          <Separator />

          {/* Dates */}
          <div className={`flex flex-col gap-2 ${!pitcherBlock ? "opacity-40" : ""}`}>
            <SectionHeader label="Date" />
            {!pitcherBlock && (
              <p className="text-xs text-muted-foreground">Select a pitcher first</p>
            )}
            {pitcherBlock && datesFetching && (
              <p className="text-xs text-muted-foreground">Loading dates...</p>
            )}
            {pitcherBlock && !datesFetching && dates?.length === 0 && (
              <p className="text-xs text-muted-foreground">No appearances found this season</p>
            )}
            <div className="flex flex-col gap-1.5">
              {pitcherBlock &&
                (dates ?? []).map((d) => {
                  const block: Block = {
                    id: `date-${d.date}`,
                    type: "date",
                    label: formatDate(d.date, d.opponent, d.home_away),
                    value: d.date,
                    color: "#1BB999",
                  };
                  return <DraggableBlock key={block.id} block={block} />;
                })}
            </div>
          </div>

          <Separator />

          {/* Splits */}
          <div className={`flex flex-col gap-2 ${!pitcherBlock ? "opacity-40" : ""}`}>
            <SectionHeader label="Split" />
            <div className="flex flex-col gap-1.5">
              {SPLIT_BLOCKS.map((block) =>
                pitcherBlock ? (
                  <DraggableBlock key={block.id} block={block} />
                ) : (
                  <div
                    key={block.id}
                    className="flex items-center gap-2.5 rounded-lg border bg-card px-3 py-2 text-sm text-muted-foreground"
                  >
                    <span className="w-1.5 shrink-0 self-stretch min-h-[1em] rounded-full opacity-30" style={{ backgroundColor: block.color }} />
                    {block.label}
                  </div>
                )
              )}
            </div>
          </div>

          <Separator />

          {/* Pitch Types */}
          <div className={`flex flex-col gap-2 ${!dateBlock ? "opacity-40" : ""}`}>
            <SectionHeader label="Pitch Type" />
            {!dateBlock && (
              <p className="text-xs text-muted-foreground">Select a pitcher & date first</p>
            )}
            {dateBlock && pitchTypesFetching && (
              <p className="text-xs text-muted-foreground">Loading pitch types...</p>
            )}
            {dateBlock && !pitchTypesFetching && pitchTypes?.length === 0 && (
              <p className="text-xs text-muted-foreground">No pitch data available</p>
            )}
            <div className="flex flex-col gap-1.5">
              {dateBlock &&
                (pitchTypes ?? []).map((pt) => {
                  const block: Block = {
                    id: `pitch_type-${pt.code}`,
                    type: "pitch_type",
                    label: `${pt.name} (${pt.count})`,
                    value: pt.code,
                    color: pt.color,
                  };
                  return <DraggableBlock key={block.id} block={block} />;
                })}
            </div>
          </div>

        </div>
      </ScrollArea>
    </div>
  );
}

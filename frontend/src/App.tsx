import { useState } from "react";
import { DndContext, DragOverlay, type DragEndEvent, type DragStartEvent } from "@dnd-kit/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Sidebar } from "@/components/Sidebar";
import { Workspace } from "@/components/Workspace";
import { RenderPanel } from "@/components/RenderPanel";
import { useRenderJob } from "@/hooks/useRenderJob";
import type { Block, Quality } from "@/types";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 60_000 } },
});

const QUALITY_OPTIONS: { value: Quality; label: string }[] = [
  { value: "low_quality",    label: "Lo" },
  { value: "medium_quality", label: "Med" },
  { value: "high_quality",   label: "Hi" },
  { value: "fourk_quality",  label: "4K" },
];

function BlockApp() {
  const [pitcherBlock, setPitcherBlock] = useState<Block | null>(null);
  const [dateBlock, setDateBlock]       = useState<Block | null>(null);
  const [splitBlock, setSplitBlock]     = useState<Block | null>(null);
  const [pitchTypeBlocks, setPitchTypeBlocks] = useState<Block[]>([]);
  const [activeBlock, setActiveBlock]   = useState<Block | null>(null);

  const {
    quality, setQuality,
    handleBuild,
    renderStatus,
    elapsed,
    error,
    outputUrl,
    steps,
    canBuild,
    isWaiting,
    isTriggering,
  } = useRenderJob(pitcherBlock, dateBlock, splitBlock, pitchTypeBlocks);

  function handleDragStart({ active }: DragStartEvent) {
    const data = active.data.current as { block: Block } | undefined;
    setActiveBlock(data?.block ?? null);
  }

  function handleDragEnd({ over }: DragEndEvent) {
    setActiveBlock(null);
    if (over?.id !== "workspace" || !activeBlock) return;

    switch (activeBlock.type) {
      case "pitcher":
        setPitcherBlock(activeBlock);
        setDateBlock(null);
        setSplitBlock(null);
        setPitchTypeBlocks([]);
        break;
      case "date":
        if (!pitcherBlock) return;
        setDateBlock(activeBlock);
        setPitchTypeBlocks([]);
        break;
      case "split":
        if (!pitcherBlock) return;
        setSplitBlock(activeBlock);
        break;
      case "pitch_type":
        if (!dateBlock) return;
        setPitchTypeBlocks((prev) =>
          prev.some((b) => b.value === activeBlock.value) ? prev : [...prev, activeBlock]
        );
        break;
    }
  }

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex h-screen overflow-hidden bg-background text-foreground">

        <Sidebar pitcherBlock={pitcherBlock} dateBlock={dateBlock} />

        <div className="flex-1 flex flex-col overflow-hidden">

          {/* Toolbar */}
          <header className="flex items-center justify-between px-6 py-3 border-b shrink-0 bg-background">
            <h1 className="font-semibold tracking-tight text-sm">Pitch Trajectory Builder</h1>
            <div className="flex items-center gap-3">
              <div className="flex gap-1">
                {QUALITY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setQuality(opt.value)}
                    className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                      quality === opt.value
                        ? "bg-foreground text-background border-foreground"
                        : "bg-background border-border text-muted-foreground hover:border-muted-foreground"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <button
                onClick={handleBuild}
                disabled={!canBuild || isWaiting}
                className="px-5 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest transition-colors
                  bg-foreground text-background
                  hover:bg-foreground/90
                  disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isTriggering ? "Queuing…" : "Build"}
              </button>
            </div>
          </header>

          {/* Workspace */}
          <Workspace
            pitcherBlock={pitcherBlock}
            dateBlock={dateBlock}
            splitBlock={splitBlock}
            pitchTypeBlocks={pitchTypeBlocks}
            onRemovePitcher={() => {
              setPitcherBlock(null);
              setDateBlock(null);
              setSplitBlock(null);
              setPitchTypeBlocks([]);
            }}
            onRemoveDate={() => {
              setDateBlock(null);
              setPitchTypeBlocks([]);
            }}
            onRemoveSplit={() => setSplitBlock(null)}
            onRemovePitchType={(id) =>
              setPitchTypeBlocks((prev) => prev.filter((b) => b.id !== id))
            }
          />

          {/* Status card — only visible when a render is active */}
          <RenderPanel
            renderStatus={renderStatus}
            elapsed={elapsed}
            outputUrl={outputUrl}
            error={error}
            steps={steps}
          />

        </div>
      </div>

      <DragOverlay dropAnimation={null}>
        {activeBlock && (
          <div className="flex items-center gap-2.5 rounded-lg border bg-card px-3 py-2 text-sm font-medium shadow-xl cursor-grabbing opacity-95">
            <span
              className="w-1.5 shrink-0 self-stretch min-h-[1em] rounded-full"
              style={{ backgroundColor: activeBlock.color }}
            />
            <span className="truncate">{activeBlock.label}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BlockApp />
    </QueryClientProvider>
  );
}

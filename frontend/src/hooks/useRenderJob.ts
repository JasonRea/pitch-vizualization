import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import type { Block, Quality, RenderStatus } from "@/types";
import { triggerRender, getRenderStatus } from "@/api/client";

export function useRenderJob(
  pitcherBlock: Block | null,
  dateBlock: Block | null,
  splitBlock: Block | null,
  pitchTypeBlocks: Block[]
) {
  const [quality, setQuality] = useState<Quality>("low_quality");
  const [runId, setRunId] = useState<number | null>(null);
  const [renderStatus, setRenderStatus] = useState<RenderStatus>("idle");
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [isTriggering, setIsTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canBuild = !!(pitcherBlock && dateBlock);
  const isWaiting = isTriggering || renderStatus === "queued" || renderStatus === "in_progress";

  useEffect(() => {
    if (!startTime || ["completed", "failed", "idle"].includes(renderStatus)) return;
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - startTime) / 1000)), 1000);
    return () => clearInterval(id);
  }, [startTime, renderStatus]);

  const { data: statusData } = useQuery({
    queryKey: ["render-status", runId],
    queryFn: () => getRenderStatus(runId!),
    enabled: !!runId && !["completed", "failed"].includes(renderStatus),
    refetchInterval: 10_000,
  });

  useEffect(() => {
    if (!statusData) return;
    setRenderStatus(statusData.status as RenderStatus);
  }, [statusData]);

  async function handleBuild() {
    if (!canBuild || !pitcherBlock || !dateBlock || isWaiting) return;
    setIsTriggering(true);
    setError(null);
    setRenderStatus("queued");
    setStartTime(Date.now());
    setElapsed(0);
    setRunId(null);

    try {
      const { run_id } = await triggerRender({
        pitcher_name: pitcherBlock.value,
        date:         dateBlock.value,
        split:        splitBlock?.value ?? "all",
        pitch_type:   pitchTypeBlocks[0]?.value ?? "",
        quality,
      });
      setRunId(run_id);
    } catch (e) {
      setRenderStatus("failed");
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsTriggering(false);
    }
  }

  const outputUrl = statusData?.output_url ?? null;

  return {
    quality,
    setQuality,
    handleBuild,
    renderStatus,
    elapsed,
    error,
    outputUrl,
    canBuild,
    isWaiting,
    isTriggering,
  };
}

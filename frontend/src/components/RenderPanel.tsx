import type { RenderStatus } from "@/types";
import type { RenderStep } from "@/api/client";

function formatElapsed(s: number) {
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

const STEP_ICON: Record<string, string> = {
  done:    "✓",
  running: "↻",
  pending: "○",
  failed:  "✗",
};

const STEP_COLOR: Record<string, string> = {
  done:    "text-green-500",
  running: "text-foreground",
  pending: "text-muted-foreground",
  failed:  "text-destructive",
};

interface Props {
  renderStatus: RenderStatus;
  elapsed: number;
  outputUrl: string | null;
  error: string | null;
  steps: RenderStep[];
}

export function RenderPanel({ renderStatus, elapsed, outputUrl, error, steps }: Props) {
  if (renderStatus === "idle") return null;

  return (
    <div className="shrink-0 border-t bg-background">
      <div className="p-4 max-w-2xl">
        {(renderStatus === "queued" || renderStatus === "in_progress") && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 text-sm">
              <span className="shrink-0 animate-spin inline-block">↻</span>
              <span className="text-muted-foreground">
                {renderStatus === "queued" ? "Queued in GitHub Actions…" : "Rendering…"}
              </span>
              <span className="ml-auto font-mono text-xs text-muted-foreground">
                {formatElapsed(elapsed)}
              </span>
            </div>

            {steps.length > 0 && (
              <div className="flex flex-col gap-0.5 pl-1">
                {steps.map((step) => (
                  <div key={step.name} className={`flex items-center gap-2 text-xs ${STEP_COLOR[step.status]}`}>
                    <span className={`w-3 text-center shrink-0 ${step.status === "running" ? "animate-spin" : ""}`}>
                      {STEP_ICON[step.status]}
                    </span>
                    <span>{step.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {renderStatus === "completed" && outputUrl && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium">Done in {formatElapsed(elapsed)}</p>
              <a
                href={outputUrl}
                download
                className="text-xs border rounded-md px-3 py-1 hover:bg-muted transition-colors font-medium"
              >
                Download MP4
              </a>
            </div>
            <video
              src={outputUrl}
              controls
              playsInline
              className="w-full rounded-lg bg-black"
              style={{ maxHeight: 360 }}
            />
          </div>
        )}

        {renderStatus === "failed" && (
          <p className="text-sm text-destructive">
            Render failed.{error ? ` ${error}` : " Check GitHub Actions for details."}
          </p>
        )}
      </div>
    </div>
  );
}

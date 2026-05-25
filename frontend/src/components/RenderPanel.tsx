import type { RenderStatus } from "@/types";

function formatElapsed(s: number) {
  const m = Math.floor(s / 60);
  return `${m}:${String(s % 60).padStart(2, "0")}`;
}

interface Props {
  renderStatus: RenderStatus;
  elapsed: number;
  outputUrl: string | null;
  error: string | null;
}

export function RenderPanel({ renderStatus, elapsed, outputUrl, error }: Props) {
  if (renderStatus === "idle") return null;

  return (
    <div className="shrink-0 border-t bg-background">
      <div className="p-4 max-w-2xl">
        {(renderStatus === "queued" || renderStatus === "in_progress") && (
          <div className="flex items-center gap-2 text-sm">
            <span className="shrink-0 animate-spin inline-block">↻</span>
            <span className="text-muted-foreground">
              {renderStatus === "queued" ? "Queued in GitHub Actions…" : "Rendering…"}
            </span>
            <span className="ml-auto font-mono text-xs text-muted-foreground">
              {formatElapsed(elapsed)}
            </span>
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

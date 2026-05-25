import type { Block } from "@/types";

interface Props {
  block: Block;
  onRemove: () => void;
}

export function PlacedBlock({ block, onRemove }: Props) {
  return (
    <div
      className="flex items-center gap-2.5 rounded-lg border-2 bg-card px-3 py-2 text-sm font-medium shadow-sm"
      style={{ borderColor: block.color + "55" }}
    >
      <span
        className="w-1.5 shrink-0 self-stretch min-h-[1em] rounded-full"
        style={{ backgroundColor: block.color }}
      />
      <span className="flex-1 truncate text-card-foreground">{block.label}</span>
      <button
        onClick={onRemove}
        className="ml-1 text-muted-foreground hover:text-foreground text-lg leading-none"
        aria-label={`Remove ${block.label}`}
      >
        ×
      </button>
    </div>
  );
}

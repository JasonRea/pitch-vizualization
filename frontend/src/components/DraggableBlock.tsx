import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { cn } from "@/lib/utils";
import type { Block } from "@/types";

interface Props {
  block: Block;
}

export function DraggableBlock({ block }: Props) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: block.id,
    data: { block },
  });

  return (
    <div
      ref={setNodeRef}
      style={transform ? { transform: CSS.Translate.toString(transform) } : undefined}
      {...attributes}
      {...listeners}
      className={cn(
        "flex items-center gap-2.5 rounded-lg border bg-card px-3 py-2 text-sm font-medium shadow-sm cursor-grab select-none transition-opacity",
        isDragging && "opacity-30"
      )}
    >
      <span
        className="w-1.5 shrink-0 self-stretch min-h-[1em] rounded-full"
        style={{ backgroundColor: block.color }}
      />
      <span className="truncate text-card-foreground">{block.label}</span>
    </div>
  );
}

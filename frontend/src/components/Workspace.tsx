import { useDroppable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import { PlacedBlock } from "./PlacedBlock";
import type { Block } from "@/types";

interface Props {
  pitcherBlock: Block | null;
  dateBlock: Block | null;
  splitBlock: Block | null;
  pitchTypeBlocks: Block[];
  onRemovePitcher: () => void;
  onRemoveDate: () => void;
  onRemoveSplit: () => void;
  onRemovePitchType: (id: string) => void;
}

export function Workspace({
  pitcherBlock,
  dateBlock,
  splitBlock,
  pitchTypeBlocks,
  onRemovePitcher,
  onRemoveDate,
  onRemoveSplit,
  onRemovePitchType,
}: Props) {
  const { setNodeRef, isOver } = useDroppable({ id: "workspace" });

  const chain: { block: Block; onRemove: () => void }[] = [
    pitcherBlock    ? { block: pitcherBlock, onRemove: onRemovePitcher }          : null,
    dateBlock       ? { block: dateBlock,    onRemove: onRemoveDate }             : null,
    splitBlock      ? { block: splitBlock,   onRemove: onRemoveSplit }            : null,
    ...pitchTypeBlocks.map((b) => ({ block: b, onRemove: () => onRemovePitchType(b.id) })),
  ].filter(Boolean) as { block: Block; onRemove: () => void }[];

  const isEmpty = chain.length === 0;

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex-1 relative overflow-auto workspace-bg transition-colors",
        isOver && "workspace-bg-over"
      )}
    >
      {isEmpty ? (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <p className="text-sm text-muted-foreground/50 select-none">
            Drag a pitcher block here to start
          </p>
        </div>
      ) : (
        <div className="p-8">
          {chain.map((entry, i) => (
            <div key={entry.block.id}>
              <div style={{ width: 260 }}>
                <PlacedBlock block={entry.block} onRemove={entry.onRemove} />
              </div>
              {i < chain.length - 1 && <div className="block-connector" />}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

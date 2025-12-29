import { Info } from "lucide-react";

interface MissingContextProps {
  items: string[];
}

export function MissingContext({ items }: MissingContextProps) {
  if (items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No additional context needed.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item, index) => (
        <div key={index} className="flex items-start gap-2 text-sm">
          <Info className="h-3.5 w-3.5 text-muted-foreground mt-0.5 flex-shrink-0" />
          <span className="text-foreground">{item}</span>
        </div>
      ))}
    </div>
  );
}

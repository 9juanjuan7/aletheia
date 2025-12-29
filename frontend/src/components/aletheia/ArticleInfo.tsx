import { FileText, Globe } from "lucide-react";

interface ArticleInfoProps {
  title: string;
  source: string;
  url?: string;
}

export function ArticleInfo({ title, source, url }: ArticleInfoProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-start gap-2">
        <FileText className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
        <h3 className="text-sm font-semibold text-foreground leading-snug line-clamp-2">
          {title}
        </h3>
      </div>
      
      <div className="flex items-center gap-2 pl-6">
        <Globe className="h-3 w-3 text-muted-foreground" />
        {url ? (
          <a 
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted-foreground hover:text-primary hover:underline"
          >
            {source}
          </a>
        ) : (
          <span className="text-xs text-muted-foreground">{source}</span>
        )}
      </div>
    </div>
  );
}

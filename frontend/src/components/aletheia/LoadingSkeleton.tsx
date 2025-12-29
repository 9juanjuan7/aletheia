import { cn } from "@/lib/utils";

interface LoadingStep {
  message: string;
  submessage?: string;
  completed?: boolean;
}

interface LoadingSkeletonProps {
  steps?: LoadingStep[];
  currentStep?: number;
}

export function LoadingSkeleton({ steps = [], currentStep = 0 }: LoadingSkeletonProps) {
  if (steps.length === 0) {
    // Default skeleton layout
    return (
      <div className="space-y-6 p-4">
        {/* Header skeleton */}
        <div className="text-center space-y-2 py-4">
          <div className="skeleton h-6 w-32 mx-auto rounded" />
          <div className="skeleton h-4 w-48 mx-auto rounded" />
        </div>

        {/* Score skeleton */}
        <div className="space-y-3">
          <div className="skeleton h-4 w-24 rounded" />
          <div className="skeleton h-10 w-full rounded" />
          <div className="skeleton h-2 w-full rounded" />
        </div>

        {/* Content skeletons */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-3 pt-4 border-t border-border">
            <div className="skeleton h-4 w-32 rounded" />
            <div className="space-y-2">
              <div className="skeleton h-3 w-full rounded" />
              <div className="skeleton h-3 w-3/4 rounded" />
              <div className="skeleton h-3 w-1/2 rounded" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Progress steps view
  return (
    <div className="p-4 space-y-4">
      <div className="text-center py-4 border-b border-border">
        <h2 className="text-sm font-semibold text-foreground uppercase tracking-wider">
          Analyzing Article
        </h2>
        <p className="text-xs text-muted-foreground mt-1">
          Following the money trail...
        </p>
      </div>

      <div className="space-y-3">
        {steps.filter(Boolean).map((step, index) => {
          if (!step) return null;
          
          const isActive = index === currentStep;
          const isCompleted = index < currentStep || step.completed === true;

          return (
            <div 
              key={index}
              className={cn(
                "flex gap-3 p-2 transition-opacity duration-300",
                isActive ? "opacity-100" : "opacity-50"
              )}
            >
              {/* Status indicator */}
              <div className="flex-shrink-0 mt-0.5">
                {isCompleted ? (
                  <div className="h-4 w-4 rounded-full bg-success flex items-center justify-center">
                    <svg className="h-2.5 w-2.5 text-success-foreground" fill="currentColor" viewBox="0 0 12 12">
                      <path d="M10.28 2.28L4 8.56l-2.28-2.28a.75.75 0 00-1.06 1.06l2.81 2.81a.75.75 0 001.06 0l6.81-6.81a.75.75 0 00-1.06-1.06z" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="h-4 w-4 rounded-full border-2 border-primary relative">
                    <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-primary animate-spin" />
                  </div>
                ) : (
                  <div className="h-4 w-4 rounded-full border-2 border-muted" />
                )}
              </div>

              {/* Step content */}
              <div className="flex-1 min-w-0">
                <p className={cn(
                  "text-sm font-medium",
                  isActive ? "text-foreground" : "text-muted-foreground"
                )}>
                  {step.message}
                </p>
                {step.submessage && isActive && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {step.submessage}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

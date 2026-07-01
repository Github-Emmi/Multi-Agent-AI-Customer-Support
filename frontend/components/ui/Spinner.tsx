import React from "react";
import { Loader2 } from "lucide-react";

interface SpinnerProps {
  size?: "sm" | "md" | "lg";
  label?: string;
}

const sizeClasses = { sm: "h-4 w-4", md: "h-6 w-6", lg: "h-10 w-10" };

export function Spinner({ size = "md", label = "Loading..." }: SpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2" role="status">
      <Loader2
        className={`${sizeClasses[size]} animate-spin text-blue-600`}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}

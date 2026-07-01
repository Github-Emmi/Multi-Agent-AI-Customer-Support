import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export function Input({
  label,
  error,
  helperText,
  id,
  className = "",
  ...props
}: InputProps) {
  const inputId = id ?? label?.toLowerCase().replace(/\s+/g, "-");

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label
          htmlFor={inputId}
          className="text-sm font-medium text-slate-700"
        >
          {label}
          {props.required && <span className="text-rose-500 ml-0.5">*</span>}
        </label>
      )}
      <input
        id={inputId}
        className={`w-full rounded-lg border px-3 py-2 text-sm text-slate-900
          placeholder:text-slate-400
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
          disabled:bg-slate-50 disabled:cursor-not-allowed
          transition-colors
          ${error
            ? "border-rose-400 bg-rose-50 focus:ring-rose-400"
            : "border-slate-300 bg-white"
          } ${className}`}
        aria-describedby={error ? `${inputId}-error` : undefined}
        aria-invalid={error ? "true" : undefined}
        {...props}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-rose-600" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p className="text-xs text-slate-500">{helperText}</p>
      )}
    </div>
  );
}

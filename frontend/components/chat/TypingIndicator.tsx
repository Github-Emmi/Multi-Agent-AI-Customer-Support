export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-4 py-3" aria-label="AI is typing" role="status">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="h-2 w-2 rounded-full bg-slate-400 animate-bounce-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
          aria-hidden="true"
        />
      ))}
      <span className="sr-only">Assistant is typing...</span>
    </div>
  );
}

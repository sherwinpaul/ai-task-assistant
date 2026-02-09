import { useState, type KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { ArrowUp, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input);
    setInput("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-gray-100 dark:border-gray-800/50 bg-white dark:bg-gray-950 px-4 py-4"
    >
      <div className="flex gap-3 max-w-3xl mx-auto items-end">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about your tasks, emails, or calendar..."
            disabled={disabled}
            rows={1}
            className="w-full px-4 py-3 border border-gray-200 dark:border-gray-800 rounded-xl resize-none
                       focus:outline-none focus:border-purple-400 focus:ring-2 focus:ring-purple-100 dark:focus:ring-purple-900/50
                       disabled:opacity-50 disabled:cursor-not-allowed
                       bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100
                       placeholder:text-gray-400 dark:placeholder:text-gray-600
                       transition-all duration-200 text-sm"
            style={{ minHeight: "44px", maxHeight: "120px" }}
          />
        </div>
        <Button
          type="submit"
          disabled={disabled || !input.trim()}
          size="icon"
          className="h-11 w-11 bg-gray-900 hover:bg-purple-600 dark:bg-white dark:hover:bg-purple-500
                     text-white dark:text-gray-900 dark:hover:text-white
                     disabled:bg-gray-200 dark:disabled:bg-gray-800 disabled:text-gray-400
                     transition-all duration-200 rounded-xl flex-shrink-0 shadow-sm"
        >
          {disabled ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowUp className="h-4 w-4" />
          )}
        </Button>
      </div>
    </form>
  );
}

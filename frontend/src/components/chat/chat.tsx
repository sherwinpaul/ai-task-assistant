import { useChat } from "@/hooks/use-chat";
import { ChatMessageList } from "./chat-message-list";
import { ChatInput } from "./chat-input";
import { ChatWelcome } from "./chat-welcome";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

export function Chat() {
  const { messages, isLoading, error, sendMessage, clearChat } = useChat();

  return (
    <div className="flex flex-col h-screen bg-white dark:bg-gray-950">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b border-gray-200 dark:border-gray-800 bg-white/80 dark:bg-gray-950/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-4 md:px-6 py-3">
          <div className="flex items-center justify-between">
            {/* Left: Logo + Brand */}
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center">
                <span className="text-white font-bold text-lg">AI</span>
              </div>
              <div>
                <h1 className="text-base font-bold text-gray-900 dark:text-white tracking-tight">
                  AI Task Assistant
                </h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Jira &middot; Gmail &middot; Calendar
                </p>
              </div>
            </div>

            {/* Right: New Chat */}
            {messages.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearChat}
                disabled={isLoading}
                className="text-gray-600 dark:text-gray-400 hover:text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-950 dark:hover:text-purple-400 transition-colors"
              >
                <RotateCcw className="h-4 w-4 mr-1.5" />
                New Chat
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 dark:bg-red-950/30 border-l-4 border-red-500 p-3 mx-4 mt-3 rounded-r-lg">
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Main content */}
      {messages.length === 0 ? (
        <ChatWelcome onPromptClick={sendMessage} />
      ) : (
        <ChatMessageList messages={messages} isLoading={isLoading} />
      )}

      <ChatInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
}

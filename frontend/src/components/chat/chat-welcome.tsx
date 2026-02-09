import { ListChecks, Mail, Calendar, Clock, Search, Bell } from "lucide-react";

interface ChatWelcomeProps {
  onPromptClick: (prompt: string) => void;
}

export function ChatWelcome({ onPromptClick }: ChatWelcomeProps) {
  const examplePrompts = [
    {
      text: "What are my urgent tasks?",
      icon: ListChecks,
      category: "Jira",
    },
    {
      text: "Show me unread emails from today",
      icon: Mail,
      category: "Gmail",
    },
    {
      text: "What meetings do I have this week?",
      icon: Calendar,
      category: "Calendar",
    },
    {
      text: "Which tasks are due this week?",
      icon: Clock,
      category: "Deadlines",
    },
    {
      text: "Search for issues assigned to me",
      icon: Search,
      category: "Search",
    },
    {
      text: "Remind me to check KAN-1 tomorrow at 9am",
      icon: Bell,
      category: "Reminder",
    },
  ];

  return (
    <div className="flex-1 flex items-center justify-center px-4 py-12">
      <div className="max-w-3xl w-full text-center">
        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center shadow-lg shadow-purple-200/50 dark:shadow-purple-900/30">
            <span className="text-white font-bold text-2xl">AI</span>
          </div>
        </div>

        <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
          What can I help you with?
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-10">
          Ask about your Jira tasks, emails, or calendar events
        </p>

        {/* Prompt grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {examplePrompts.map((prompt, index) => {
            const Icon = prompt.icon;
            return (
              <button
                key={index}
                onClick={() => onPromptClick(prompt.text)}
                className="group p-4 rounded-xl border border-gray-200 dark:border-gray-800
                           bg-white dark:bg-gray-900
                           text-sm text-gray-700 dark:text-gray-300 text-left
                           transition-all duration-200
                           hover:shadow-lg hover:shadow-purple-100/40 dark:hover:shadow-purple-900/20
                           hover:border-purple-300 dark:hover:border-purple-700
                           hover:-translate-y-0.5
                           relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-purple-50 to-transparent dark:from-purple-950/30 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="relative">
                  <div className="flex items-start gap-3 mb-2">
                    <div className="p-1.5 rounded-lg bg-purple-50 dark:bg-purple-950/50 group-hover:bg-purple-100 dark:group-hover:bg-purple-900/50 transition-colors">
                      <Icon className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                    </div>
                    <span className="flex-1 font-medium leading-snug">{prompt.text}</span>
                  </div>
                  <div className="flex items-center justify-between pl-10">
                    <span className="text-[10px] text-gray-400 dark:text-gray-600 font-semibold uppercase tracking-widest">
                      {prompt.category}
                    </span>
                    <span className="text-xs text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
                      Ask &rarr;
                    </span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <p className="text-xs text-gray-400 dark:text-gray-600 mt-8">
          Click a suggestion or type your own question below
        </p>
      </div>
    </div>
  );
}

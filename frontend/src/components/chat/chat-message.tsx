import { memo } from "react";
import type { Message } from "@/types/message";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { User, Zap } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

const MARKDOWN_COMPONENTS = {
  table: ({ children }: any) => (
    <div className="overflow-x-auto my-4">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        {children}
      </table>
    </div>
  ),
  thead: ({ children }: any) => (
    <thead className="bg-gray-50 dark:bg-gray-900">{children}</thead>
  ),
  tbody: ({ children }: any) => (
    <tbody className="divide-y divide-gray-100 dark:divide-gray-800 bg-white dark:bg-gray-900">
      {children}
    </tbody>
  ),
  th: ({ children }: any) => (
    <th className="px-3 py-2 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider border border-gray-200 dark:border-gray-700">
      {children}
    </th>
  ),
  td: ({ children }: any) => (
    <td className="px-3 py-2 text-sm border border-gray-200 dark:border-gray-700">
      {children}
    </td>
  ),
  code: ({ inline, children, ...props }: any) =>
    inline ? (
      <code
        className="px-1.5 py-0.5 rounded-md bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 font-mono text-xs"
        {...props}
      >
        {children}
      </code>
    ) : (
      <code
        className="block p-3 rounded-lg bg-gray-900 dark:bg-black text-gray-100 font-mono text-xs overflow-x-auto"
        {...props}
      >
        {children}
      </code>
    ),
  pre: ({ children }: any) => (
    <pre className="my-2 rounded-lg overflow-hidden">{children}</pre>
  ),
};

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = memo(function ChatMessage({
  message,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const content = message.content;

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0 mt-0.5">
          <AvatarFallback className="bg-gray-900 dark:bg-white text-white dark:text-gray-900">
            <Zap className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className="flex flex-col gap-1.5 max-w-[80%]">
        <div
          className={`rounded-2xl px-4 py-3 shadow-sm ${
            isUser
              ? "bg-purple-600 dark:bg-purple-500 text-white rounded-br-md"
              : "bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 text-gray-900 dark:text-gray-100 rounded-bl-md"
          }`}
        >
          <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none prose-p:my-1.5 prose-pre:my-2 prose-ul:my-2 prose-ol:my-2">
            <ReactMarkdown
              remarkPlugins={[remarkGfm, remarkMath]}
              rehypePlugins={[rehypeRaw, rehypeKatex]}
              components={MARKDOWN_COMPONENTS}
            >
              {content}
            </ReactMarkdown>
          </div>
        </div>

        {/* Sources pill */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {message.sources.map((src, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium
                           bg-purple-50 dark:bg-purple-950/50 text-purple-600 dark:text-purple-400
                           border border-purple-100 dark:border-purple-900"
              >
                <span className="uppercase">{src.source}</span>
                <span className="text-purple-400 dark:text-purple-600">&middot;</span>
                <span>{src.id}</span>
              </span>
            ))}
            {message.cached && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 dark:bg-gray-800 text-gray-500">
                cached
              </span>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="h-8 w-8 flex-shrink-0 mt-0.5">
          <AvatarFallback className="bg-purple-600 text-white">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
});

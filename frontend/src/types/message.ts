export type MessageRole = 'user' | 'assistant';

export interface BaseMessage {
  id: string;
  role: MessageRole;
  timestamp: Date;
}

export interface TextMessage extends BaseMessage {
  type: 'text';
  content: string;
  sources?: { id: string; source: string; title: string }[];
  cached?: boolean;
}

export type Message = TextMessage;

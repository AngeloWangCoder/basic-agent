import { useChat } from '@ai-sdk/react';
import { chatTransport } from '@/services/chatTransport';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';

export function ChatContainer() {
  const { messages, sendMessage, status, stop, error } = useChat({
    transport: chatTransport,
  });

  return (
    <div className="h-full flex flex-col">
      <header className="border-b border-neutral-200 bg-white px-4 py-3">
        <h1 className="text-sm font-semibold text-neutral-800">basic-agent</h1>
      </header>
      <MessageList messages={messages} status={status} errorText={error?.message} />
      <ChatInput status={status} onSend={(text) => sendMessage({ text })} onStop={stop} />
    </div>
  );
}

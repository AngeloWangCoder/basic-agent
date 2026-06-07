import { ChatContainer } from '@/components/chat/ChatContainer';

export function ChatPage() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-neutral-100">
      <div className="h-full w-full max-w-3xl bg-white shadow-sm">
        <ChatContainer />
      </div>
    </div>
  );
}

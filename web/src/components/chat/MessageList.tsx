import type { UIMessage } from 'ai';
import { useAutoScroll } from '@/hooks/useAutoScroll';
import { MessageItem } from './MessageItem';

interface Props {
  messages: UIMessage[];
  status: 'submitted' | 'streaming' | 'ready' | 'error';
  errorText?: string;
}

function lastAssistantHasText(messages: UIMessage[]): boolean {
  const last = messages[messages.length - 1];
  if (!last || last.role !== 'assistant') return false;
  return last.parts.some((p) => p.type === 'text' && p.text.length > 0);
}

export function MessageList({ messages, status, errorText }: Props) {
  const ref = useAutoScroll(messages.length + (status === 'streaming' ? 1 : 0));

  const showThinking =
    status === 'submitted' || (status === 'streaming' && !lastAssistantHasText(messages));

  return (
    <div ref={ref} className="flex-1 overflow-y-auto px-4 py-6 space-y-3">
      {messages.length === 0 && (
        <div className="h-full flex items-center justify-center text-neutral-400 text-sm">
          开始一个对话吧
        </div>
      )}
      {messages.map((m) => (
        <MessageItem key={m.id} message={m} />
      ))}
      {showThinking && <div className="text-xs text-neutral-400 px-2">思考中…</div>}
      {status === 'error' && (
        <div className="text-xs text-red-600 px-2">{errorText ?? '出错了，请重试'}</div>
      )}
    </div>
  );
}

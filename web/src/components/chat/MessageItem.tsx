import type { UIMessage } from 'ai';
import { cn } from '@/lib/cn';
import { MessagePartView } from './MessageParts';

interface Props {
  message: UIMessage;
}

function hasVisibleContent(message: UIMessage): boolean {
  return message.parts.some((p) => p.type === 'text' && p.text.length > 0);
}

export function MessageItem({ message }: Props) {
  if (!hasVisibleContent(message)) return null;

  const isUser = message.role === 'user';
  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-2 text-sm shadow-sm',
          isUser
            ? 'bg-neutral-900 text-neutral-50'
            : 'bg-white text-neutral-900 border border-neutral-200',
        )}
      >
        {message.parts.map((part, idx) => (
          <MessagePartView key={idx} part={part} />
        ))}
      </div>
    </div>
  );
}

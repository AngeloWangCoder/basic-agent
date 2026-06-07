import { useState, type FormEvent, type KeyboardEvent } from 'react';
import { cn } from '@/lib/cn';

interface Props {
  status: 'submitted' | 'streaming' | 'ready' | 'error';
  onSend: (text: string) => void;
  onStop: () => void;
}

export function ChatInput({ status, onSend, onStop }: Props) {
  const [value, setValue] = useState('');
  const busy = status === 'submitted' || status === 'streaming';

  const send = () => {
    const text = value.trim();
    if (!text || busy) return;
    onSend(text);
    setValue('');
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    send();
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <form
      onSubmit={onSubmit}
      className="border-t border-neutral-200 bg-white px-4 py-3 flex gap-2 items-end"
    >
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        rows={1}
        placeholder="发消息… (Enter 发送 / Shift+Enter 换行)"
        className="flex-1 resize-none rounded-xl border border-neutral-300 bg-neutral-50 px-3 py-2 text-sm outline-none focus:border-neutral-900 focus:bg-white max-h-40"
      />
      {busy ? (
        <button
          type="button"
          onClick={onStop}
          className={cn(
            'rounded-xl px-4 py-2 text-sm font-medium',
            'bg-neutral-200 text-neutral-700 hover:bg-neutral-300',
          )}
        >
          停止
        </button>
      ) : (
        <button
          type="submit"
          disabled={!value.trim()}
          className={cn(
            'rounded-xl px-4 py-2 text-sm font-medium',
            'bg-neutral-900 text-neutral-50 hover:bg-neutral-700',
            'disabled:bg-neutral-300 disabled:cursor-not-allowed',
          )}
        >
          发送
        </button>
      )}
    </form>
  );
}

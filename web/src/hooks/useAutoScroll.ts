import { useEffect, useRef } from 'react';

/**
 * Returns a ref to attach to a scroll container; the container will follow
 * the bottom whenever `dep` changes (e.g. new tokens streamed in).
 */
export function useAutoScroll<T>(dep: T) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [dep]);

  return ref;
}

import { DefaultChatTransport } from 'ai';
import { env } from '@/lib/env';

/**
 * Single place to configure how the chat UI talks to the backend.
 * Swap this transport later (custom headers, auth, WebSocket, …) without
 * touching components.
 */
export const chatTransport = new DefaultChatTransport({
  api: `${env.API_BASE_URL}/chat`,
});

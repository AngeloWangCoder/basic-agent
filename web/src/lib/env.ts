interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export const env = {
  API_BASE_URL: (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, ''),
};

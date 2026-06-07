import { create } from 'zustand';

interface SettingsState {
  systemPrompt: string;
  setSystemPrompt: (value: string) => void;
}

export const useSettingsStore = create<SettingsState>((set) => ({
  systemPrompt: '',
  setSystemPrompt: (value) => set({ systemPrompt: value }),
}));

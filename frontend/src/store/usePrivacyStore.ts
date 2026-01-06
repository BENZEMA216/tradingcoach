/**
 * Privacy Mode Store
 * input: localStorage for persistence
 * output: privacy mode state and actions
 * pos: Global state management for privacy/percentage display feature
 *
 * Once updated, update this header and src/store/README.md
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface PrivacyState {
  // State
  isPrivacyMode: boolean;
  initialCapital: number | null;
  hasSetCapital: boolean;

  // Actions
  togglePrivacyMode: () => void;
  setPrivacyMode: (enabled: boolean) => void;
  setInitialCapital: (amount: number) => void;
  resetPrivacySettings: () => void;
}

export const usePrivacyStore = create<PrivacyState>()(
  persist(
    (set, _get) => ({
      // Initial state
      isPrivacyMode: false,
      initialCapital: null,
      hasSetCapital: false,

      // Toggle privacy mode
      togglePrivacyMode: () => {
        set((state) => ({ isPrivacyMode: !state.isPrivacyMode }));
      },

      setPrivacyMode: (enabled: boolean) => {
        set({ isPrivacyMode: enabled });
      },

      setInitialCapital: (amount: number) => {
        set({
          initialCapital: amount,
          hasSetCapital: true,
          isPrivacyMode: true, // Auto-enable after setting capital
        });
      },

      resetPrivacySettings: () => {
        set({
          isPrivacyMode: false,
          initialCapital: null,
          hasSetCapital: false,
        });
      },
    }),
    {
      name: 'privacy-settings', // localStorage key
      version: 1,
    }
  )
);

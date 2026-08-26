import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  email: string;
  is_admin?: boolean;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: ( user: User) => void; 
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,

      // Nimmt jetzt nur das user-Objekt entgegen
      login: ( user: User) => {
        set({
          user: user,
          isAuthenticated: true,
        });
      },

      logout: () => {
        set({
          user: null,
          isAuthenticated: false,
        });
      },
    }),
    {
      name: 'auth-storage', // Key im localStorage für den User-Status
    }
  )
);
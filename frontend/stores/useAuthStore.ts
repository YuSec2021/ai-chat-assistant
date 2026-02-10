/**
 * Authentication state management with Zustand
 * Handles JWT token, user info, and authentication actions
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  username: string;
  subscription_level: 'free' | 'gold' | 'diamond';
  role: 'user' | 'admin';
  is_active: boolean;
  is_banned: boolean;
  created_at: string;
}

interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface CaptchaResponse {
  captcha_id: string;
  image: string; // base64 encoded image
}

interface AuthState {
  // State
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  login: (username: string, password: string, captchaCode: string, captchaId: string) => Promise<void>;
  register: (username: string, password: string, captchaCode: string, captchaId: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  refreshUser: () => Promise<void>;
  fetchCaptcha: () => Promise<CaptchaResponse>;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:6969';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Set token
      setToken: (token: string) => {
        set({ token, isAuthenticated: true });
      },

      // Set user
      setUser: (user: User) => {
        set({ user });
      },

      // Login
      login: async (username: string, password: string, captchaCode: string, captchaId: string) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username,
              password,
              captcha_code: captchaCode,
              captcha_id: captchaId,
            }),
          });

          if (!response.ok) {
            let errorMessage = 'Login failed';
            try {
              const errorData = await response.json();
              errorMessage = errorData.detail || errorMessage;
            } catch {
              errorMessage = `Login failed (${response.status})`;
            }
            throw new Error(errorMessage);
          }

          const data: AuthResponse = await response.json();

          set({
            token: data.access_token,
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Login failed',
          });
          throw error;
        }
      },

      // Register
      register: async (username: string, password: string, captchaCode: string, captchaId: string) => {
        set({ isLoading: true, error: null });

        try {
          const url = `${API_BASE_URL}/auth/register`;
          console.log('Registering to:', url);

          const response = await fetch(url, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              username,
              password,
              captcha_code: captchaCode,
              captcha_id: captchaId,
            }),
          });

          console.log('Response status:', response.status);

          if (!response.ok) {
            let errorMessage = 'Registration failed';
            try {
              const errorData = await response.json();
              errorMessage = errorData.detail || errorMessage;
              console.error('Registration error:', errorData);
            } catch {
              errorMessage = `Registration failed (${response.status})`;
              console.error('Registration failed with status:', response.status);
            }
            throw new Error(errorMessage);
          }

          const data: AuthResponse = await response.json();
          console.log('Registration successful:', data);

          set({
            token: data.access_token,
            user: data.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          console.error('Registration error:', error);
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Registration failed',
          });
          throw error;
        }
      },

      // Logout
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Refresh user info
      refreshUser: async () => {
        const { token } = get();

        if (!token) {
          return;
        }

        try {
          const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            // Token invalid, logout
            get().logout();
            return;
          }

          const user: User = await response.json();
          set({ user });
        } catch (error) {
          console.error('Failed to refresh user:', error);
          get().logout();
        }
      },

      // Fetch captcha
      fetchCaptcha: async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/auth/captcha`);
          if (!response.ok) {
            throw new Error('Failed to fetch captcha');
          }
          const data: CaptchaResponse = await response.json();
          return data;
        } catch (error) {
          console.error('Failed to fetch captcha:', error);
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Helper function to get authorization header
export const getAuthHeader = (): Record<string, string> => {
  const { token } = useAuthStore.getState();
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
};

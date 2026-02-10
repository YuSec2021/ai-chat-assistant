/**
 * Auth Provider Component - Protects routes that require authentication
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/useAuthStore';

interface AuthProviderProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export default function AuthProvider({ children, requireAdmin = false }: AuthProviderProps) {
  const router = useRouter();
  const { isAuthenticated, user, refreshUser } = useAuthStore();

  useEffect(() => {
    // Refresh user info on mount
    refreshUser();
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (requireAdmin && user?.role !== 'admin') {
      router.push('/chat');
      return;
    }
  }, [isAuthenticated, user, requireAdmin, router]);

  if (!isAuthenticated) {
    return null;
  }

  if (requireAdmin && user?.role !== 'admin') {
    return null;
  }

  return <>{children}</>;
}

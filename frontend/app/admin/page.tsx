/**
 * Admin page - user management
 */

'use client';

import { useAuthStore } from '@/stores/useAuthStore';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import AdminUserTable from '@/components/admin-user-table';

export default function AdminPage() {
  const router = useRouter();
  const { user, isAuthenticated, hasHydrated } = useAuthStore();
  const [hasMounted, setHasMounted] = useState(false);

  // Wait for client-side mount
  useEffect(() => {
    setHasMounted(true);
  }, []);

  useEffect(() => {
    // Only check auth after hydration is complete
    if (!hasHydrated || !hasMounted) {
      return;
    }

    // Redirect if not authenticated
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    // Redirect if not admin
    if (user?.role !== 'admin') {
      router.push('/chat/new');
      return;
    }
  }, [isAuthenticated, user, router, hasHydrated, hasMounted]);

  // Show loading while hydrating
  if (!hasHydrated || !hasMounted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <p className="text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated or not admin (after hydration)
  if (!isAuthenticated || user?.role !== 'admin') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-8">
      <div className="max-w-7xl mx-auto">
        <AdminUserTable />
      </div>
    </div>
  );
}

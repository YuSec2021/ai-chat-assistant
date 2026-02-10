/**
 * Membership badge component for displaying user subscription level
 */

'use client';

import { useI18n } from '@/lib/i18n';

interface MembershipBadgeProps {
  level: 'free' | 'gold' | 'diamond';
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

export default function MembershipBadge({
  level,
  size = 'md',
  showText = true
}: MembershipBadgeProps) {
  const { t } = useI18n();

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base'
  };

  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  const config = {
    free: {
      bg: 'bg-slate-700/50',
      border: 'border-slate-600',
      text: 'text-slate-300',
      icon: (
        <svg className={iconSizes[size]} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
        </svg>
      ),
      label: t(`membership.${level}`)
    },
    gold: {
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      text: 'text-yellow-400',
      icon: (
        <svg className={iconSizes[size]} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.699-3.181a1 1 0 011.827 1.035L17.413 9H17a1 1 0 110 2h-.586l-.007.012a1 1 0 01-1.827-1.035L12.323 6.323 8.95 5.177 7.02 8.977l-1.699-3.181a1 1 0 00-1.827 1.035L5.586 11H5a1 1 0 110-2h.413l-.007-.012a1 1 0 011.827-1.035L8.95 5.177 7.677 4.323 10 3.323V3a1 1 0 011-1zM6 13a1 1 0 100-2 1 1 0 000 2zm8 0a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
        </svg>
      ),
      label: t(`membership.${level}`)
    },
    diamond: {
      bg: 'bg-cyan-500/10',
      border: 'border-cyan-500/30',
      text: 'text-cyan-400',
      icon: (
        <svg className={iconSizes[size]} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M10 2L2 7l8 11 8-11-8-5zM5.5 7l4.5-3 4.5 3-4.5 6L5.5 7z" clipRule="evenodd" />
        </svg>
      ),
      label: t(`membership.${level}`)
    }
  };

  const style = config[level];

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full border ${style.bg} ${style.border} ${sizeClasses[size]}`}
    >
      <span className={style.text}>
        {style.icon}
      </span>
      {showText && (
        <span className={`font-medium ${style.text}`}>
          {style.label}
        </span>
      )}
    </div>
  );
}

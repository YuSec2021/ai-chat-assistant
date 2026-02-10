'use client';

import { useI18n } from '@/lib/i18n';
import { Button } from '@/components/ui/button';
import { Languages } from 'lucide-react';

export default function LanguageToggle() {
  const { locale, setLocale } = useI18n();

  const toggleLanguage = () => {
    setLocale(locale === 'en' ? 'zh' : 'en');
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggleLanguage}
      title={`Current language: ${locale === 'en' ? 'English' : '中文'}`}
    >
      <Languages className="h-4 w-4" />
      <span className="ml-1 text-xs font-mono">
        {locale === 'en' ? 'EN' : '中'}
      </span>
    </Button>
  );
}

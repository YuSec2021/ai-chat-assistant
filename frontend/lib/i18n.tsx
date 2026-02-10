/**
 * Simple i18n provider using React Context
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Locale = 'en' | 'zh';

interface I18nContextType {
  locale: Locale;
  t: (key: string) => string;
  setLocale: (locale: Locale) => void;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

// Import translations
const translations = {
  en: () => import('../messages/en.json').then(m => m.default),
  zh: () => import('../messages/zh.json').then(m => m.default),
};

function getNestedValue(obj: any, path: string): string {
  return path.split('.').reduce((current, key) => current?.[key], obj) || path;
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('locale') as Locale;
      return saved && (saved === 'en' || saved === 'zh') ? saved : 'en';
    }
    return 'en';
  });
  const [messages, setMessages] = useState<any>({});

  useEffect(() => {
    translations[locale]().then(setMessages);
  }, [locale]);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof window !== 'undefined') {
      localStorage.setItem('locale', newLocale);
    }
  };

  const t = (key: string): string => {
    return getNestedValue(messages, key);
  };

  return (
    <I18nContext.Provider value={{ locale, t, setLocale }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) {
    throw new Error('useI18n must be used within I18nProvider');
  }
  return context;
}

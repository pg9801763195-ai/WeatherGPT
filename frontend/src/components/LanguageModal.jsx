import React from 'react';
import { useWeather } from '../context/WeatherContext';
import { LANGUAGES } from '../constants/appConfig';

export default function LanguageModal() {
  const {
    isLanguageOpen,
    setIsLanguageOpen,
    currentLanguage,
    setCurrentLanguage,
    showToast,
    t
  } = useWeather();

  if (!isLanguageOpen) return null;

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-outline-variant/20 shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant/15 bg-surface-container-low/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-lg">language</span>
            </div>
            <h3 className="font-headline-md text-base font-bold text-on-surface">{t('languageSelectorTitle')}</h3>
          </div>
          <button
            onClick={() => setIsLanguageOpen(false)}
            className="p-1.5 rounded-full text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors cursor-pointer"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Language Options */}
        <div className="p-6 space-y-2">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => {
                setCurrentLanguage(lang);
                setIsLanguageOpen(false);
                showToast(lang.code === 'hi' ? 'भाषा बदलकर हिन्दी कर दी गई है' : `Language set to ${lang.name}`);
              }}
              className={`w-full flex items-center justify-between p-3.5 rounded-2xl border transition-all cursor-pointer ${
                currentLanguage.code === lang.code
                  ? 'bg-primary/10 border-primary text-primary font-bold shadow-xs'
                  : 'bg-surface border-outline-variant/15 text-on-surface hover:bg-surface-container-low hover:border-outline-variant/30'
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-xl">{lang.flag}</span>
                <span className="font-body-md text-sm font-medium">{lang.name}</span>
              </div>
              {currentLanguage.code === lang.code && (
                <span className="material-symbols-outlined text-sm text-primary font-bold">check</span>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

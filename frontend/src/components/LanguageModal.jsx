import React from 'react';
import { useWeather } from '../context/WeatherContext';
import { LANGUAGES } from '../constants/appConfig';

export default function LanguageModal() {
  const {
    isLanguageOpen,
    setIsLanguageOpen,
    currentLanguage,
    setCurrentLanguage,
    showToast
  } = useWeather();

  if (!isLanguageOpen) return null;

  return (
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div class="bg-surface rounded-2xl border border-outline-variant/20 shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant/15">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">language</span>
            <h3 class="font-headline-md text-lg text-on-surface">Language Selector</h3>
          </div>
          <button
            onClick={() => setIsLanguageOpen(false)}
            class="p-1 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Language Options */}
        <div class="p-6 space-y-2">
          {LANGUAGES.map(lang => (
            <button
              key={lang.code}
              onClick={() => {
                setCurrentLanguage(lang);
                setIsLanguageOpen(false);
                showToast(`Language set to ${lang.name}`);
              }}
              class={`w-full flex items-center justify-between p-3 rounded-xl border transition-colors ${
                currentLanguage.code === lang.code
                  ? 'bg-primary/10 border-primary text-primary font-bold'
                  : 'bg-surface border-outline-variant/15 text-on-surface hover:bg-surface-container-low'
              }`}
            >
              <div class="flex items-center gap-3">
                <span class="text-xl">{lang.flag}</span>
                <span class="font-body-md text-sm">{lang.name}</span>
              </div>
              {currentLanguage.code === lang.code && (
                <span class="material-symbols-outlined text-sm text-primary">check</span>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function NotificationToast() {
  const { toastMessage } = useWeather();

  if (!toastMessage) return null;

  return (
    <aside 
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-8 right-6 md:right-8 z-[99999] transition-all duration-300 pointer-events-none animate-fadeIn"
    >
      <div className="bg-surface/95 dark:bg-slate-900/95 text-on-surface px-5 py-3.5 rounded-2xl shadow-2xl border border-outline-variant/30 backdrop-blur-xl flex items-center gap-3 max-w-md pointer-events-auto">
        <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/25 flex items-center justify-center text-primary flex-shrink-0">
          <span className="material-symbols-outlined text-base">info</span>
        </div>
        <span className="font-body-md text-xs sm:text-sm font-semibold tracking-wide text-on-surface">
          {toastMessage}
        </span>
      </div>
    </aside>
  );
}

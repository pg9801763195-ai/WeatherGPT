import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function MobileNav() {
  const { activeTab, setActiveTab, setIsSearchOpen, t } = useWeather();

  return (
    <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 bg-surface/95 backdrop-blur-lg border-t border-outline-variant/15 pb-6 pt-3 px-4 flex justify-around items-center shadow-lg">
      <button
        onClick={() => setActiveTab('overview')}
        className={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'overview'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span className="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'overview' ? "'FILL' 1" : "'FILL' 0" }}>cloud</span>
        <span className="font-label-caps text-label-caps text-[10px]">{t('tabOverview')}</span>
      </button>

      <button
        onClick={() => setActiveTab('forecast')}
        className={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'forecast'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span className="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'forecast' ? "'FILL' 1" : "'FILL' 0" }}>insights</span>
        <span className="font-label-caps text-label-caps text-[10px]">{t('tabForecast')}</span>
      </button>

      <button
        onClick={() => setActiveTab('map')}
        className={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'map'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span className="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'map' ? "'FILL' 1" : "'FILL' 0" }}>map</span>
        <span className="font-label-caps text-label-caps text-[10px]">{t('tabMap')}</span>
      </button>

      <button
        onClick={() => setActiveTab('assistant')}
        className={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'assistant'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span className="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'assistant' ? "'FILL' 1" : "'FILL' 0" }}>auto_awesome</span>
        <span className="font-label-caps text-label-caps text-[10px]">{t('tabAssistant')}</span>
      </button>

      <button
        onClick={() => setIsSearchOpen(true)}
        className="flex flex-col items-center justify-center text-on-surface-variant hover:text-on-surface transition-all gap-1"
      >
        <span className="material-symbols-outlined">search</span>
        <span className="font-label-caps text-label-caps text-[10px]">{t('searchCityPlaceholder')}</span>
      </button>
    </nav>
  );
}

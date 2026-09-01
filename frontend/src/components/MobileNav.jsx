import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function MobileNav() {
  const { activeTab, setActiveTab, setIsSearchOpen } = useWeather();

  return (
    <nav class="md:hidden fixed bottom-0 left-0 w-full z-50 bg-surface/95 backdrop-blur-lg border-t border-outline-variant/15 pb-6 pt-3 px-4 flex justify-around items-center shadow-lg">
      <button
        onClick={() => setActiveTab('overview')}
        class={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'overview' || activeTab === 'forecast'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span class="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'overview' ? "'FILL' 1" : "'FILL' 0" }}>cloud</span>
        <span class="font-label-caps text-label-caps text-[10px]">Forecast</span>
      </button>

      <button
        onClick={() => setActiveTab('map')}
        class={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'map'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span class="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'map' ? "'FILL' 1" : "'FILL' 0" }}>map</span>
        <span class="font-label-caps text-label-caps text-[10px]">Map</span>
      </button>

      <button
        onClick={() => setActiveTab('assistant')}
        class={`flex flex-col items-center justify-center gap-1 transition-all ${
          activeTab === 'assistant'
            ? 'text-primary font-bold'
            : 'text-on-surface-variant hover:text-on-surface'
        }`}
      >
        <span class="material-symbols-outlined" style={{ fontVariationSettings: activeTab === 'assistant' ? "'FILL' 1" : "'FILL' 0" }}>auto_awesome</span>
        <span class="font-label-caps text-label-caps text-[10px]">Assistant</span>
      </button>

      <button
        onClick={() => setIsSearchOpen(true)}
        class="flex flex-col items-center justify-center text-on-surface-variant hover:text-on-surface transition-all gap-1"
      >
        <span class="material-symbols-outlined">search</span>
        <span class="font-label-caps text-label-caps text-[10px]">Search</span>
      </button>
    </nav>
  );
}

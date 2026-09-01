import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function SettingsModal() {
  const {
    isSettingsOpen,
    setIsSettingsOpen,
    unit,
    toggleUnit,
    isHighContrast,
    setIsHighContrast,
    fontSizeMode,
    setFontSizeMode,
    notificationsEnabled,
    setNotificationsEnabled,
    showToast
  } = useWeather();

  if (!isSettingsOpen) return null;

  return (
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div class="bg-surface rounded-2xl border border-outline-variant/20 shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant/15">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">settings</span>
            <h3 class="font-headline-md text-lg text-on-surface">Settings &amp; Accessibility</h3>
          </div>
          <button
            onClick={() => setIsSettingsOpen(false)}
            class="p-1 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Settings List */}
        <div class="p-6 space-y-6">
          {/* Temperature Units */}
          <div class="flex items-center justify-between">
            <div>
              <h4 class="font-body-md text-sm font-medium text-on-surface">Temperature Unit</h4>
              <p class="text-xs text-on-surface-variant">Switch between Celsius (°C) and Fahrenheit (°F)</p>
            </div>
            <button
              onClick={toggleUnit}
              class="px-4 py-2 rounded-xl bg-primary/10 text-primary font-label-caps text-xs font-bold transition-transform active:scale-95"
            >
              °{unit} ({unit === 'C' ? 'Celsius' : 'Fahrenheit'})
            </button>
          </div>

          {/* Text Size Accessibility */}
          <div class="flex items-center justify-between pt-4 border-t border-outline-variant/10">
            <div>
              <h4 class="font-body-md text-sm font-medium text-on-surface">Font Size Scaling</h4>
              <p class="text-xs text-on-surface-variant">Adjust font scale for enhanced legibility</p>
            </div>
            <button
              onClick={() => {
                const nextMode = fontSizeMode === 'standard' ? 'large' : 'standard';
                setFontSizeMode(nextMode);
                showToast(`Font scaling set to ${nextMode}`);
              }}
              class="px-3.5 py-1.5 rounded-xl bg-surface-container text-xs font-bold text-primary hover:bg-surface-container-high transition-colors"
            >
              {fontSizeMode === 'standard' ? 'Standard (100%)' : 'Large (120%)'}
            </button>
          </div>

          {/* High Contrast Mode */}
          <div class="flex items-center justify-between pt-4 border-t border-outline-variant/10">
            <div>
              <h4 class="font-body-md text-sm font-medium text-on-surface">High Contrast Mode</h4>
              <p class="text-xs text-on-surface-variant">Enhance contrast for low-vision readability</p>
            </div>
            <button
              onClick={() => {
                setIsHighContrast(!isHighContrast);
                showToast(isHighContrast ? 'High contrast disabled' : 'High contrast enabled');
              }}
              class={`w-12 h-6 rounded-full transition-colors relative p-1 ${
                isHighContrast ? 'bg-primary' : 'bg-outline-variant/30'
              }`}
            >
              <div class={`w-4 h-4 rounded-full bg-white transition-transform ${isHighContrast ? 'translate-x-6' : 'translate-x-0'}`}></div>
            </button>
          </div>

          {/* Severe Weather Push Notifications */}
          <div class="flex items-center justify-between pt-4 border-t border-outline-variant/10">
            <div>
              <h4 class="font-body-md text-sm font-medium text-on-surface">Weather Alert Notifications</h4>
              <p class="text-xs text-on-surface-variant">Receive atmospheric advisory push alerts</p>
            </div>
            <button
              onClick={() => {
                setNotificationsEnabled(!notificationsEnabled);
                showToast(notificationsEnabled ? 'Alert notifications disabled' : 'Alert notifications enabled');
              }}
              class={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer ${
                notificationsEnabled ? 'bg-primary' : 'bg-outline-variant/30'
              }`}
            >
              <div class={`w-4 h-4 rounded-full bg-white transition-transform ${notificationsEnabled ? 'translate-x-6' : 'translate-x-0'}`}></div>
            </button>
          </div>

          {/* System Info */}
          <div class="pt-4 border-t border-outline-variant/10 text-center">
            <p class="text-xs text-on-surface-variant">WeatherGPT Atmospheric Intelligence v3.0.0</p>
            <p class="text-[10px] text-on-surface-variant/70 mt-1">Live Open-Meteo Real-Time Meteorological Telemetry</p>
          </div>
        </div>
      </div>
    </div>
  );
}

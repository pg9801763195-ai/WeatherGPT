import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function SettingsModal() {
  const {
    isSettingsOpen,
    setIsSettingsOpen,
    unit,
    toggleUnit,
    fontSizeMode,
    setFontSizeMode,
    notificationsEnabled,
    setNotificationsEnabled,
    showToast,
    t
  } = useWeather();

  if (!isSettingsOpen) return null;

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-outline-variant/20 shadow-2xl max-w-md w-full overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-outline-variant/15 bg-surface-container-low/50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-lg">settings</span>
            </div>
            <h3 className="font-headline-md text-base font-bold text-on-surface">{t('settingsTitle')}</h3>
          </div>
          <button
            onClick={() => setIsSettingsOpen(false)}
            className="p-1.5 rounded-full text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors cursor-pointer"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Settings List */}
        <div className="p-6 space-y-5">
          {/* Temperature Units */}
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-body-md text-sm font-semibold text-on-surface">{t('temperatureUnit')}</h4>
              <p className="text-xs text-on-surface-variant/80">{t('tempUnitDesc')}</p>
            </div>
            <button
              onClick={toggleUnit}
              className="px-4 py-2 rounded-xl bg-primary/10 text-primary font-label-caps text-xs font-bold transition-transform active:scale-95 cursor-pointer hover:bg-primary/20 border border-primary/25"
            >
              °{unit} ({unit === 'C' ? 'Celsius' : 'Fahrenheit'})
            </button>
          </div>

          {/* Text Size Accessibility */}
          <div className="flex items-center justify-between pt-4 border-t border-outline-variant/10">
            <div>
              <h4 className="font-body-md text-sm font-semibold text-on-surface">{t('fontSizeScaling')}</h4>
              <p className="text-xs text-on-surface-variant/80">{t('fontSizeDesc')}</p>
            </div>
            <button
              onClick={() => {
                const nextMode = fontSizeMode === 'standard' ? 'large' : 'standard';
                setFontSizeMode(nextMode);
                showToast(`Font scaling set to ${nextMode}`);
              }}
              className="px-3.5 py-1.5 rounded-xl bg-surface-container text-xs font-bold text-primary hover:bg-surface-container-high transition-colors cursor-pointer border border-outline-variant/15"
            >
              {fontSizeMode === 'standard' ? 'Standard (100%)' : 'Large (120%)'}
            </button>
          </div>

          {/* Severe Weather Push Notifications */}
          <div className="flex items-center justify-between pt-4 border-t border-outline-variant/10">
            <div>
              <h4 className="font-body-md text-sm font-semibold text-on-surface">{t('weatherAlertNotifications')}</h4>
              <p className="text-xs text-on-surface-variant/80">{t('alertNotifDesc')}</p>
            </div>
            <button
              onClick={() => {
                setNotificationsEnabled(!notificationsEnabled);
                showToast(notificationsEnabled ? 'Alert notifications disabled' : 'Alert notifications enabled');
              }}
              className={`w-12 h-6 rounded-full transition-colors relative p-1 cursor-pointer ${
                notificationsEnabled ? 'bg-primary' : 'bg-outline-variant/30'
              }`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${notificationsEnabled ? 'translate-x-6' : 'translate-x-0'}`}></div>
            </button>
          </div>

          {/* System Info */}
          <div className="pt-4 border-t border-outline-variant/10 text-center">
            <p className="text-xs font-semibold text-on-surface-variant">{t('appVersion')}</p>
            <p className="text-[10px] text-on-surface-variant/70 mt-0.5">{t('appCredit')}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

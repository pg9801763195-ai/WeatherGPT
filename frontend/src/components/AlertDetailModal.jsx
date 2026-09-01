import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function AlertDetailModal() {
  const {
    isAlertDetailOpen,
    setIsAlertDetailOpen,
    activeAlert,
    currentCity,
    showToast
  } = useWeather();

  if (!isAlertDetailOpen || !activeAlert) return null;

  return (
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div class="bg-surface rounded-2xl border border-tertiary-fixed-dim/40 shadow-2xl max-w-xl w-full overflow-hidden">
        {/* Header */}
        <div class="bg-tertiary-fixed/40 border-b border-tertiary-fixed-dim/30 p-6 flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-tertiary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-tertiary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                {activeAlert.icon || 'warning'}
              </span>
            </div>
            <div>
              <span class="font-label-caps text-xs font-bold text-tertiary tracking-wider uppercase">
                {activeAlert.severityLabel || 'Atmospheric Advisory'}
              </span>
              <h3 class="font-headline-md text-xl text-on-surface font-semibold">{activeAlert.title}</h3>
            </div>
          </div>
          <button
            onClick={() => setIsAlertDetailOpen(false)}
            class="p-1 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Modal Body */}
        <div class="p-6 space-y-6 max-h-[70vh] overflow-y-auto no-scrollbar">
          {/* Timing & Location */}
          <div class="flex flex-wrap gap-4 text-xs font-label-caps text-on-surface-variant">
            <div class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-primary text-sm">schedule</span>
              <span>{activeAlert.timing}</span>
            </div>
            <div class="flex items-center gap-1.5">
              <span class="material-symbols-outlined text-primary text-sm">location_on</span>
              <span>{currentCity.name}, {currentCity.region}</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 class="font-body-md text-sm font-semibold text-on-surface mb-1">Alert Overview</h4>
            <p class="font-body-md text-sm text-on-surface-variant leading-relaxed">
              {activeAlert.fullDesc || activeAlert.shortDesc}
            </p>
          </div>

          {/* Recommended Action */}
          <div class="bg-primary/5 rounded-xl p-4 border border-primary/20">
            <h4 class="font-label-caps text-xs text-primary uppercase tracking-wider mb-1 flex items-center gap-1">
              <span class="material-symbols-outlined text-sm">verified_user</span>
              Recommended Action
            </h4>
            <p class="font-body-md text-sm text-on-surface font-medium">
              {activeAlert.recommendedAction}
            </p>
          </div>

          {/* Affected Sub-regions */}
          {activeAlert.affectedAreas && activeAlert.affectedAreas.length > 0 && (
            <div>
              <h4 class="font-body-md text-sm font-semibold text-on-surface mb-2">Affected Areas</h4>
              <div class="flex flex-wrap gap-2">
                {activeAlert.affectedAreas.map((area, idx) => (
                  <span key={idx} class="px-3 py-1 rounded-full bg-surface-container text-on-surface-variant text-xs font-medium border border-outline-variant/10">
                    {area}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Safety Guidelines */}
          <div>
            <h4 class="font-body-md text-sm font-semibold text-on-surface mb-2">Precautionary Guidelines</h4>
            <ul class="space-y-2 text-xs text-on-surface-variant">
              <li class="flex items-start gap-2">
                <span class="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>Keep battery-powered light source available during evening hours.</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>Stay updated via WeatherGPT live assistant notifications.</span>
              </li>
              <li class="flex items-start gap-2">
                <span class="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>Secure loose outdoor furniture or balcony objects before peak storm timing.</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Modal Footer */}
        <div class="px-6 py-4 border-t border-outline-variant/15 flex justify-end gap-3 bg-surface-container-low">
          <button
            onClick={() => {
              navigator.clipboard?.writeText?.(`${activeAlert.title}: ${activeAlert.shortDesc}`);
              showToast('Alert advisory copied to clipboard!');
            }}
            class="px-4 py-2 rounded-xl bg-surface border border-outline-variant/15 text-on-surface-variant text-xs font-medium hover:text-on-surface transition-colors flex items-center gap-1.5"
          >
            <span class="material-symbols-outlined text-sm">share</span>
            Share Advisory
          </button>
          <button
            onClick={() => setIsAlertDetailOpen(false)}
            class="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary/90 transition-colors"
          >
            Acknowledge
          </button>
        </div>
      </div>
    </div>
  );
}

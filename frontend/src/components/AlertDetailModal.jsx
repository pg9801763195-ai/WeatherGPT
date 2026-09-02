import React from 'react';
import { useWeather } from '../context/WeatherContext';
import { getLocalizedAlert } from '../utils/translations';

export default function AlertDetailModal() {
  const {
    isAlertDetailOpen,
    setIsAlertDetailOpen,
    activeAlert,
    currentCity,
    currentLanguage,
    showToast,
    t
  } = useWeather();

  if (!isAlertDetailOpen || !activeAlert) return null;

  const alert = getLocalizedAlert(activeAlert, currentLanguage?.code);
  const isHi = currentLanguage?.code === 'hi';

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-tertiary-fixed-dim/40 shadow-2xl max-w-xl w-full overflow-hidden">
        {/* Header */}
        <div className="bg-tertiary-fixed/40 border-b border-tertiary-fixed-dim/30 p-6 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-tertiary/10 flex items-center justify-center shadow-xs">
              <span className="material-symbols-outlined text-tertiary text-xl" style={{ fontVariationSettings: "'FILL' 1" }}>
                {alert.icon || 'warning'}
              </span>
            </div>
            <div>
              <span className="font-label-caps text-xs font-bold text-tertiary tracking-wider uppercase">
                {alert.severityLabel || t('severeWarning')}
              </span>
              <h3 className="font-headline-md text-xl text-on-surface font-semibold">{alert.title}</h3>
            </div>
          </div>
          <button
            onClick={() => setIsAlertDetailOpen(false)}
            className="p-1.5 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors cursor-pointer"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto no-scrollbar">
          {/* Timing & Location */}
          <div className="flex flex-wrap gap-4 text-xs font-label-caps text-on-surface-variant">
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-primary text-sm">schedule</span>
              <span>{alert.timing}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="material-symbols-outlined text-primary text-sm">location_on</span>
              <span>{currentCity?.name || 'Local Area'}, {currentCity?.region || ''}</span>
            </div>
          </div>

          {/* Description */}
          <div>
            <h4 className="font-body-md text-sm font-semibold text-on-surface mb-1">
              {isHi ? 'चेतावनी विवरण' : 'Alert Overview'}
            </h4>
            <p className="font-body-md text-sm text-on-surface-variant leading-relaxed">
              {alert.fullDesc || alert.shortDesc}
            </p>
          </div>

          {/* Recommended Action */}
          <div className="bg-primary/5 rounded-2xl p-4 border border-primary/20">
            <h4 className="font-label-caps text-xs text-primary uppercase tracking-wider mb-1 flex items-center gap-1 font-bold">
              <span className="material-symbols-outlined text-sm">verified_user</span>
              {isHi ? 'सलाह व अनुशंसित सावधानियां' : 'Recommended Action'}
            </h4>
            <p className="font-body-md text-sm text-on-surface font-medium">
              {alert.recommendedAction}
            </p>
          </div>

          {/* Affected Sub-regions */}
          {alert.affectedAreas && alert.affectedAreas.length > 0 && (
            <div>
              <h4 className="font-body-md text-sm font-semibold text-on-surface mb-2">
                {isHi ? 'प्रभावित क्षेत्र' : 'Affected Areas'}
              </h4>
              <div className="flex flex-wrap gap-2">
                {alert.affectedAreas.map((area, idx) => (
                  <span key={idx} className="px-3 py-1 rounded-full bg-surface-container text-on-surface-variant text-xs font-medium border border-outline-variant/10">
                    {area}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Safety Guidelines */}
          <div>
            <h4 className="font-body-md text-sm font-semibold text-on-surface mb-2">
              {isHi ? 'सुरक्षा दिशानिर्देश' : 'Precautionary Guidelines'}
            </h4>
            <ul className="space-y-2 text-xs text-on-surface-variant">
              <li className="flex items-start gap-2">
                <span className="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>{isHi ? 'आपातकालीन प्रकाश या टॉर्च तैयार रखें।' : 'Keep battery-powered light source available during evening hours.'}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>{isHi ? 'WeatherGPT लाइव मौसम सहायक सूचनाओं से अपडेट रहें।' : 'Stay updated via WeatherGPT live assistant notifications.'}</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="material-symbols-outlined text-primary text-sm mt-0.5">check_circle</span>
                <span>{isHi ? 'तूफान के समय बालकनी व खुले स्थानों की वस्तुओं को सुरक्षित कर लें।' : 'Secure loose outdoor furniture or balcony objects before peak storm timing.'}</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 border-t border-outline-variant/15 flex justify-end gap-3 bg-surface-container-low">
          <button
            onClick={() => {
              navigator.clipboard?.writeText?.(`${alert.title}: ${alert.shortDesc}`);
              showToast(isHi ? 'चेतावनी संदेश कॉपी कर लिया गया है!' : 'Alert advisory copied to clipboard!');
            }}
            className="px-4 py-2 rounded-xl bg-surface border border-outline-variant/15 text-on-surface-variant text-xs font-medium hover:text-on-surface transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <span className="material-symbols-outlined text-sm">share</span>
            {t('shareAdvisory')}
          </button>
          <button
            onClick={() => setIsAlertDetailOpen(false)}
            className="px-5 py-2 rounded-xl bg-primary text-white text-xs font-bold hover:bg-primary/90 transition-colors cursor-pointer"
          >
            {t('acknowledge')}
          </button>
        </div>
      </div>
    </div>
  );
}

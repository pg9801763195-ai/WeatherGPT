import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function WeatherMetrics() {
  const { currentCity, formatTemp, t } = useWeather();

  const isLive = Boolean(currentCity?.isLiveLoaded && currentCity?.humidity !== null);

  const humidity = isLive ? currentCity.humidity : null;
  const uvIndex = isLive ? currentCity.uvIndex : null;
  const uvLabel = isLive 
    ? (currentCity?.uvLabel || (uvIndex === 0 ? 'Minimal' : (uvIndex >= 8 ? 'Very High' : uvIndex >= 6 ? 'High' : uvIndex >= 3 ? 'Mod' : 'Low')))
    : t('awaitingLocation');

  const windKm = isLive ? currentCity.windKm : null;
  const windDirection = isLive ? (currentCity.windDirection || 'N') : '--';
  const windDegrees = isLive ? (currentCity.windDegrees ?? 0) : 0;
  const precipProbability = isLive ? currentCity.precipProbability : null;
  const precipMm = isLive ? currentCity.precipMm : null;
  const pressureHpa = isLive ? currentCity.pressureHpa : null;
  const pressureTrend = isLive ? (currentCity.pressureTrend || 'Steady ➔') : t('pendingSelection');
  const visibilityKm = isLive ? currentCity.visibilityKm : null;
  const dewPointC = isLive ? currentCity.dewPointC : null;
  const dewPointF = isLive ? currentCity.dewPointF : null;

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-semibold">
          {t('atmosphericGauges')}
        </h2>
        <span className="text-[11px] text-on-surface-variant/75 font-medium">
          {isLive ? t('liveMetrics') : t('pendingSelection')}
        </span>
      </div>

      {/* 2-Column Spacious Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Humidity Card */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm group">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('humidity')}</span>
            <span className="material-symbols-outlined text-primary text-base">humidity_percentage</span>
          </div>

          <div className="my-3 flex items-center gap-3.5">
            <div className="relative w-12 h-12 flex-shrink-0 flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  className="text-outline-variant/15 stroke-current"
                  strokeWidth="3.5"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-primary stroke-current transition-all duration-700"
                  strokeDasharray={`${humidity ?? 0}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span className="absolute text-[10px] font-bold text-on-surface">
                {humidity !== null ? `${humidity}%` : '--'}
              </span>
            </div>
            <div>
              <span className="text-xl font-bold text-on-surface block leading-none mb-1">
                {humidity !== null ? `${humidity}%` : '--'}
              </span>
              <span className="text-[11px] text-on-surface-variant/80 font-medium block">
                {humidity !== null ? (humidity > 75 ? t('humidAir') : humidity > 60 ? t('moderate') : t('comfort')) : t('selectLocation')}
              </span>
            </div>
          </div>
        </div>

        {/* UV Index Card */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('uvIndex')}</span>
            <span className="material-symbols-outlined text-amber-500 text-base">routine</span>
          </div>

          <div className="my-3 space-y-2">
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-on-surface leading-none">
                {uvIndex !== null ? uvIndex : '--'}
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 font-label-caps">
                {uvLabel}
              </span>
            </div>
            <div className="w-full bg-outline-variant/15 h-1.5 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-500 rounded-full"
                style={{ width: `${uvIndex !== null ? Math.min((uvIndex / 12) * 100, 100) : 0}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Wind Direction Compass */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('windVector')}</span>
            <span className="material-symbols-outlined text-primary text-base">air</span>
          </div>

          <div className="my-3 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-secondary-container/40 flex items-center justify-center border border-primary/20 flex-shrink-0">
              <span
                className="material-symbols-outlined text-primary text-lg transition-transform duration-500"
                style={{ transform: `rotate(${windDegrees}deg)` }}
              >
                navigation
              </span>
            </div>
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-xl font-bold text-on-surface leading-none">
                  {windKm !== null ? windKm : '--'}
                </span>
                <span className="text-xs text-on-surface-variant/75 font-medium">km/h</span>
              </div>
              <span className="text-[11px] text-on-surface-variant/80 font-medium block mt-0.5">
                {isLive ? `${windDirection} (${windDegrees}°)` : t('pendingSelection')}
              </span>
            </div>
          </div>
        </div>

        {/* Precipitation Card */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('precipitation')}</span>
            <span className="material-symbols-outlined text-blue-500 text-base">water_drop</span>
          </div>

          <div className="my-3">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-on-surface leading-none">
                {precipProbability !== null ? `${precipProbability}%` : '--'}
              </span>
            </div>
            <span className="text-[11px] text-on-surface-variant/80 font-medium block mt-1">
              {precipMm !== null ? `${precipMm} mm/h` : t('pendingSelection')}
            </span>
          </div>
        </div>

        {/* Barometer Pressure Card */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('barometer')}</span>
            <span className="material-symbols-outlined text-primary text-base">swap_vertical_circle</span>
          </div>

          <div className="my-3">
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-on-surface leading-none">
                {pressureHpa !== null ? pressureHpa : '--'}
              </span>
              <span className="text-xs text-on-surface-variant/75 font-medium">hPa</span>
            </div>
            <span className="text-[11px] text-on-surface-variant/80 font-medium block mt-1">
              {isLive ? pressureTrend : t('pendingSelection')}
            </span>
          </div>
        </div>

        {/* Visibility Card */}
        <div className="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div className="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span className="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">{t('visibility')}</span>
            <span className="material-symbols-outlined text-primary text-base">visibility</span>
          </div>

          <div className="my-3 flex justify-between items-end">
            <div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-on-surface leading-none">
                  {visibilityKm !== null ? visibilityKm : '--'}
                </span>
                <span className="text-xs text-on-surface-variant/75 font-medium">km</span>
              </div>
              <span className="text-[11px] text-emerald-600 font-medium block mt-1">
                {isLive ? (visibilityKm >= 10 ? t('clearHorizon') : t('hazyLow')) : t('pendingSelection')}
              </span>
            </div>

            {dewPointC !== null && (
              <div className="text-right">
                <span className="text-[9px] text-on-surface-variant uppercase tracking-wider font-semibold font-label-caps block">{t('dewPoint')}</span>
                <span className="text-xs font-bold text-on-surface font-mono">
                  {formatTemp(dewPointC, dewPointF)}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

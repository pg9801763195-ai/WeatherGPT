import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function SolarCycle() {
  const { currentCity, t } = useWeather();

  const isLive = Boolean(currentCity?.isLiveLoaded && currentCity?.sunrise && currentCity.sunrise !== '--:--');

  const sunrise = isLive ? currentCity.sunrise : '--:--';
  const sunset = isLive ? currentCity.sunset : '--:--';

  // Helper to parse time string like "5:30 AM" or "05:30" into minutes from midnight
  const parseTimeToMinutes = (timeStr) => {
    if (!timeStr || timeStr === '--:--') return null;
    const match = timeStr.match(/(\d+):(\d+)\s*(AM|PM)?/i);
    if (!match) return null;
    let hours = parseInt(match[1], 10);
    const minutes = parseInt(match[2], 10);
    const meridian = match[3] ? match[3].toUpperCase() : null;

    if (meridian === 'PM' && hours < 12) hours += 12;
    if (meridian === 'AM' && hours === 12) hours = 0;

    return hours * 60 + minutes;
  };

  const sunriseMin = parseTimeToMinutes(sunrise);
  const sunsetMin = parseTimeToMinutes(sunset);

  // Total daylight duration in minutes
  const daylightMinutes = (sunriseMin !== null && sunsetMin !== null)
    ? Math.max(60, sunsetMin > sunriseMin ? sunsetMin - sunriseMin : (24 * 60 - sunriseMin + sunsetMin))
    : 0;
  const daylightHours = Math.floor(daylightMinutes / 60);
  const daylightRemMin = daylightMinutes % 60;

  // Calculate current solar position along the arc (0.0 to 1.0)
  const now = new Date();
  const currentMin = now.getHours() * 60 + now.getMinutes();

  let sunProgress = 0.5;
  let isNight = false;

  if (sunriseMin !== null && sunsetMin !== null) {
    if (currentMin < sunriseMin) {
      sunProgress = 0;
      isNight = true;
    } else if (currentMin > sunsetMin) {
      sunProgress = 1;
      isNight = true;
    } else {
      sunProgress = (currentMin - sunriseMin) / daylightMinutes;
    }
  }

  // Solar Arc Coordinates (SVG ViewBox: 400 x 140)
  const startX = 50;
  const endX = 350;
  const peakY = 25;
  const baseY = 110;

  const currentX = startX + sunProgress * (endX - startX);
  const tCoord = Math.max(0, Math.min(1, sunProgress));
  const currentY = baseY - (baseY - peakY) * (4 * tCoord * (1 - tCoord));

  return (
    <section className="bg-surface border border-outline-variant/15 rounded-2xl p-6 shadow-sm space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500">
            <span className="material-symbols-outlined text-lg">wb_twilight</span>
          </div>
          <div>
            <h2 className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-semibold">
              {t('solarCycleTitle')}
            </h2>
            <p className="text-[11px] text-on-surface-variant/70">{t('solarCycleSub')}</p>
          </div>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-amber-500/10 text-amber-600 dark:text-amber-400 font-label-caps text-[10px] font-bold tracking-wide">
          {isLive ? `${daylightHours}h ${daylightRemMin}m ${t('daylight')}` : t('awaitingLocation')}
        </span>
      </div>

      {/* Visual Solar Arc Curve Display */}
      <div className="relative w-full h-32 bg-surface-container-low rounded-xl border border-outline-variant/10 p-2 overflow-hidden flex items-center justify-center">
        <svg className="w-full h-full" viewBox="0 0 400 130" preserveAspectRatio="xMidYMid meet">
          {/* Horizon Line */}
          <line x1="20" y1={baseY} x2="380" y2={baseY} stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" className="text-outline-variant/30" />

          {/* Daylight Arc Area Gradient Fill */}
          <defs>
            <linearGradient id="solarGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
            </linearGradient>
            <radialGradient id="sunGlow">
              <stop offset="0%" stopColor="#fbbf24" stopOpacity="1" />
              <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Parabolic Sun Path Area */}
          <path
            d={`M ${startX} ${baseY} Q 200 ${peakY - 15} ${endX} ${baseY} L ${endX} ${baseY} L ${startX} ${baseY} Z`}
            fill="url(#solarGrad)"
          />

          {/* Parabolic Solar Arc Stroke */}
          <path
            d={`M ${startX} ${baseY} Q 200 ${peakY - 15} ${endX} ${baseY}`}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="2.5"
            strokeDasharray="4 2"
          />

          {/* Sunrise Point Marker */}
          <circle cx={startX} cy={baseY} r="5" fill="#f59e0b" />

          {/* Sunset Point Marker */}
          <circle cx={endX} cy={baseY} r="5" fill="#ea580c" />

          {/* Current Sun / Moon Position Marker along the Arc */}
          {isLive ? (
            !isNight ? (
              <g transform={`translate(${currentX}, ${currentY})`}>
                <circle cx="0" cy="0" r="14" fill="url(#sunGlow)" />
                <circle cx="0" cy="0" r="6" fill="#fbbf24" stroke="#ffffff" strokeWidth="2" />
              </g>
            ) : (
              <g transform={`translate(${sunProgress === 0 ? startX : endX}, ${baseY})`}>
                <circle cx="0" cy="0" r="6" fill="#818cf8" stroke="#ffffff" strokeWidth="2" />
              </g>
            )
          ) : null}
        </svg>

        {/* Floating Realtime Solar State */}
        <div className="absolute top-2 left-4 text-[10px] font-mono text-on-surface-variant font-medium">
          {isLive ? (!isNight ? t('sunInSky') : t('nightInterval')) : t('awaitingLocation')}
        </div>
      </div>

      {/* Sunrise & Sunset Data Columns */}
      <div className="grid grid-cols-2 gap-4 pt-1">
        {/* Sunrise Box */}
        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/10 flex items-center gap-3.5 hover:border-amber-500/30 transition-all">
          <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-500 flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-xl">wb_sunny</span>
          </div>
          <div>
            <span className="text-[10px] font-label-caps uppercase text-on-surface-variant font-semibold tracking-wider block">
              {t('dawnSunrise')}
            </span>
            <span className="font-tight text-lg font-bold text-on-surface leading-tight block">
              {sunrise}
            </span>
            <span className="text-[11px] text-amber-600 dark:text-amber-400 font-medium">
              {isLive ? t('goldenHourStart') : t('pendingSelection')}
            </span>
          </div>
        </div>

        {/* Sunset Box */}
        <div className="bg-surface-container-low rounded-xl p-4 border border-outline-variant/10 flex items-center gap-3.5 hover:border-orange-500/30 transition-all">
          <div className="w-10 h-10 rounded-xl bg-orange-500/15 text-orange-500 flex items-center justify-center flex-shrink-0">
            <span className="material-symbols-outlined text-xl">nights_stay</span>
          </div>
          <div>
            <span className="text-[10px] font-label-caps uppercase text-on-surface-variant font-semibold tracking-wider block">
              {t('duskSunset')}
            </span>
            <span className="font-tight text-lg font-bold text-on-surface leading-tight block">
              {sunset}
            </span>
            <span className="text-[11px] text-orange-600 dark:text-orange-400 font-medium">
              {isLive ? t('civilTwilightEnd') : t('pendingSelection')}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

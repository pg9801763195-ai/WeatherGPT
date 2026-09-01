import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function WeatherMetrics() {
  const { currentCity, formatTemp } = useWeather();

  const humidity = currentCity?.humidity ?? 65;
  const uvIndex = currentCity?.uvIndex ?? 5;
  const uvLabel = currentCity?.uvLabel || (uvIndex >= 8 ? 'Very High' : uvIndex >= 6 ? 'High' : uvIndex >= 3 ? 'Mod' : 'Low');
  const windKm = currentCity?.windKm ?? 10;
  const windDirection = currentCity?.windDirection || 'N';
  const windDegrees = currentCity?.windDegrees ?? 0;
  const precipProbability = currentCity?.precipProbability ?? 0;
  const precipMm = currentCity?.precipMm ?? 0.0;
  const pressureHpa = currentCity?.pressureHpa ?? 1013;
  const pressureTrend = currentCity?.pressureTrend || 'Steady ➔';
  const visibilityKm = currentCity?.visibilityKm ?? 10.0;
  const dewPointC = currentCity?.dewPointC ?? 18;
  const dewPointF = currentCity?.dewPointF ?? 64;

  return (
    <section class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-semibold">
          Atmospheric Conditions &amp; Gauges
        </h2>
        <span class="text-[11px] text-on-surface-variant/75 font-medium">Live Metrics</span>
      </div>

      {/* 2-Column Spacious Grid */}
      <div class="grid grid-cols-2 gap-4">
        {/* Humidity Card */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm group">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Humidity</span>
            <span class="material-symbols-outlined text-primary text-base">humidity_percentage</span>
          </div>

          <div class="my-3 flex items-center gap-3.5">
            <div class="relative w-12 h-12 flex-shrink-0 flex items-center justify-center">
              <svg class="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                <path
                  class="text-outline-variant/15 stroke-current"
                  strokeWidth="3.5"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  class="text-primary stroke-current transition-all duration-700"
                  strokeDasharray={`${humidity}, 100`}
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <span class="absolute text-[10px] font-bold text-on-surface">{humidity}%</span>
            </div>
            <div>
              <span class="text-xl font-bold text-on-surface block leading-none mb-1">{humidity}%</span>
              <span class="text-[11px] text-on-surface-variant/80 font-medium block">
                {humidity > 75 ? 'Humid Air' : humidity > 60 ? 'Moderate' : 'Comfort'}
              </span>
            </div>
          </div>
        </div>

        {/* UV Index Card */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">UV Index</span>
            <span class="material-symbols-outlined text-amber-500 text-base">routine</span>
          </div>

          <div class="my-3 space-y-2">
            <div class="flex items-baseline gap-2">
              <span class="text-2xl font-bold text-on-surface leading-none">{uvIndex}</span>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/10 text-amber-700 font-label-caps">
                {uvLabel}
              </span>
            </div>
            <div class="w-full bg-outline-variant/15 h-1.5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-500 rounded-full"
                style={{ width: `${Math.min((uvIndex / 12) * 100, 100)}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Wind Direction Compass */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Wind Vector</span>
            <span class="material-symbols-outlined text-primary text-base">air</span>
          </div>

          <div class="my-3 flex items-center gap-3">
            <div class="w-9 h-9 rounded-full bg-secondary-container/50 flex-shrink-0 flex items-center justify-center border border-outline-variant/15">
              <span
                class="material-symbols-outlined text-primary text-lg transition-transform duration-500"
                style={{ transform: `rotate(${windDegrees}deg)` }}
              >
                navigation
              </span>
            </div>
            <div>
              <span class="text-xl font-bold text-on-surface leading-none block mb-1">{windKm} <span class="text-xs font-normal text-on-surface-variant">km/h</span></span>
              <span class="text-[11px] text-on-surface-variant/80 font-medium block">From {windDirection} ({windDegrees}°)</span>
            </div>
          </div>
        </div>

        {/* Precipitation Meter */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Precipitation</span>
            <span class="material-symbols-outlined text-primary text-base">water_drop</span>
          </div>

          <div class="my-3 space-y-2">
            <div class="flex items-baseline justify-between">
              <span class="text-2xl font-bold text-on-surface leading-none">{precipProbability}%</span>
              <span class="text-[11px] text-on-surface-variant/80 font-medium">{precipMm} mm/h</span>
            </div>
            <div class="w-full bg-outline-variant/15 h-1.5 rounded-full overflow-hidden">
              <div
                class="h-full bg-primary rounded-full transition-all duration-500"
                style={{ width: `${precipProbability}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Air Pressure Barometer */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Barometer</span>
            <span class="material-symbols-outlined text-on-surface-variant text-base">compress</span>
          </div>

          <div class="my-3">
            <span class="text-xl font-bold text-on-surface leading-none block mb-1">{pressureHpa} <span class="text-xs font-normal text-on-surface-variant">hPa</span></span>
            <span class="text-[11px] text-primary font-medium block">
              Trend: {pressureTrend}
            </span>
          </div>
        </div>

        {/* Visibility & Dew Point */}
        <div class="bg-surface border border-outline-variant/15 rounded-2xl p-5 flex flex-col justify-between hover:border-primary/30 transition-all shadow-sm">
          <div class="flex justify-between items-center pb-2 border-b border-outline-variant/10">
            <span class="font-label-caps text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">Visibility</span>
            <span class="material-symbols-outlined text-on-surface-variant text-base">visibility</span>
          </div>

          <div class="my-3 flex items-end justify-between">
            <div>
              <span class="text-xl font-bold text-on-surface leading-none block mb-1">{visibilityKm} <span class="text-xs font-normal text-on-surface-variant">km</span></span>
              <span class="text-[10px] text-emerald-700 font-medium block">Clear Horizon</span>
            </div>
            <div class="text-right">
              <span class="text-[9px] text-on-surface-variant uppercase font-label-caps block">Dew Point</span>
              <span class="text-xs font-bold text-on-surface">
                {formatTemp(dewPointC, dewPointF)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

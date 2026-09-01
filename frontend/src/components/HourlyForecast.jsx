import React, { useState } from 'react';
import { useWeather } from '../context/WeatherContext';
import { resolveWeatherVisual } from '../utils/weatherVisuals';

function generateHourlySvgPath(points) {
  if (!points || points.length === 0) return '';
  if (points.length === 1) return `M ${points[0].x},${points[0].y}`;

  let path = `M ${points[0].x.toFixed(1)},${points[0].y.toFixed(1)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = i > 0 ? points[i - 1] : points[0];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = i < points.length - 2 ? points[i + 2] : p2;

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    path += ` C ${cp1x.toFixed(1)},${cp1y.toFixed(1)} ${cp2x.toFixed(1)},${cp2y.toFixed(1)} ${p2.x.toFixed(1)},${p2.y.toFixed(1)}`;
  }
  return path;
}

export default function HourlyForecast() {
  const { currentCity, formatTemp, unit } = useWeather();
  const [selectedHourIdx, setSelectedHourIdx] = useState(0);

  const fallbackHourly = [
    { time: 'Now', icon: currentCity?.conditionIcon || 'partly_cloudy_day', tempC: currentCity?.tempC || 24, tempF: currentCity?.tempF || 75, precip: 10, precipMm: 0, humidity: currentCity?.humidity || 65, windKm: currentCity?.windKm || 12, windDir: currentCity?.windDirection || 'SE', dewC: currentCity?.dewPointC || 18, dewF: currentCity?.dewPointF || 64, condition: currentCity?.condition || 'Partly Cloudy' }
  ];

  const hourlyList = (currentCity?.hourly && currentCity.hourly.length > 0) ? currentCity.hourly : fallbackHourly;
  const activeItem = hourlyList[selectedHourIdx] || hourlyList[0] || fallbackHourly[0];
  const activeHourVisual = resolveWeatherVisual(activeItem?.condition || currentCity?.condition || 'Partly Cloudy');

  // Compute dynamic points for hourly curve
  const temps = hourlyList.map(h => (unit === 'C' ? (h.tempC ?? 20) : (h.tempF ?? 68)));
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const span = Math.max(1, maxTemp - minTemp);

  const hourlyPoints = hourlyList.map((item, idx) => {
    const tempVal = unit === 'C' ? (item.tempC ?? 20) : (item.tempF ?? 68);
    const x = 25 + idx * (350 / Math.max(1, hourlyList.length - 1));
    const norm = (tempVal - minTemp) / span;
    const y = 48 - norm * 34; // maps from y=48 (low) to y=14 (high)
    return { x, y, tempVal, idx, item };
  });

  const curvePath = generateHourlySvgPath(hourlyPoints);

  return (
    <section className="bg-surface border border-outline-variant/15 rounded-2xl p-6 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-semibold">
            Today's Timeline &amp; Temp Curve
          </h2>
          <p className="text-[11px] text-on-surface-variant/70 mt-0.5">Click any hour to inspect micro-atmospheric details</p>
        </div>
        <span className="px-2.5 py-1 rounded-full bg-primary/10 text-primary font-label-caps text-[10px] font-semibold">
          Live Timeline
        </span>
      </div>

      {/* Hourly Scroll Container */}
      <div className="relative overflow-x-auto no-scrollbar pb-3 pt-2">
        {/* SVG Temperature Curve Line Overlay */}
        <div className="h-20 w-[600px] sm:w-full relative mb-2">
          <svg className="w-full h-full" viewBox="0 0 400 60" preserveAspectRatio="none">
            <defs>
              <linearGradient id="hourlyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#2a6088" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#2a6088" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Shaded Area under Hourly Curve */}
            {hourlyPoints.length > 0 && (
              <path
                d={`${curvePath} L ${hourlyPoints[hourlyPoints.length - 1].x},58 L ${hourlyPoints[0].x},58 Z`}
                fill="url(#hourlyGrad)"
              />
            )}

            {/* Dynamic Curve Stroke */}
            {curvePath && (
              <path
                d={curvePath}
                fill="none"
                stroke="#2a6088"
                strokeWidth="2.5"
                className="transition-all duration-300"
              />
            )}

            {/* Interactive Circles */}
            {hourlyPoints.map((pt) => {
              const isSelected = selectedHourIdx === pt.idx;
              return (
                <circle
                  key={pt.idx}
                  cx={pt.x}
                  cy={pt.y}
                  r={isSelected ? "5.5" : "3.5"}
                  fill={isSelected ? "#2a6088" : "#ffffff"}
                  stroke="#2a6088"
                  strokeWidth={isSelected ? "2.5" : "1.8"}
                  className="transition-all duration-300 cursor-pointer"
                  onClick={() => setSelectedHourIdx(pt.idx)}
                />
              );
            })}
          </svg>
        </div>

        {/* Hourly Cards Row */}
        <div className="flex items-center justify-between min-w-[550px] gap-2">
          {hourlyList.map((item, idx) => {
            const isSelected = selectedHourIdx === idx;
            const isCurrent = item.time === 'Now';

            return (
              <div
                key={idx}
                onClick={() => setSelectedHourIdx(idx)}
                className={`flex-1 flex flex-col items-center p-3 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-primary text-white border-primary shadow-md scale-105 font-bold'
                    : isCurrent
                    ? 'bg-surface-container border-primary/40 text-on-surface'
                    : 'bg-surface border-outline-variant/15 text-on-surface hover:bg-surface-container-low'
                }`}
              >
                <span className={`font-body-md text-xs ${isSelected ? 'text-white/90' : 'text-on-surface-variant'} ${isCurrent ? 'font-bold text-primary' : ''}`}>
                  {item.time}
                </span>

                <span className={`material-symbols-outlined text-xl my-1.5 ${isSelected ? 'text-white' : (item.precip || 0) > 50 ? 'text-primary' : 'text-on-surface'}`}>
                  {item.icon || 'partly_cloudy_day'}
                </span>

                <span className={`font-headline-md text-sm font-semibold ${isSelected ? 'text-white' : 'text-on-surface'}`}>
                  {formatTemp(item.tempC || 0, item.tempF || 32)}
                </span>

                {/* Rain probability bar */}
                <div className="w-full bg-black/10 rounded-full h-1.5 mt-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isSelected ? 'bg-white' : 'bg-primary'}`}
                    style={{ width: `${Math.min(item.precip || 0, 100)}%` }}
                  ></div>
                </div>
                <span className={`text-[10px] mt-1 font-medium ${isSelected ? 'text-white/80' : 'text-on-surface-variant'}`}>
                  {item.precip || 0}%
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Hour Detail Drawer */}
      <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/10 flex flex-wrap items-center justify-between gap-4 text-xs animate-fadeIn">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/15 flex-shrink-0">
            <span className="material-symbols-outlined text-lg">{activeItem.icon || 'partly_cloudy_day'}</span>
          </div>
          <div>
            <h4 className="font-body-md font-semibold text-on-surface">
              {activeItem.time} · {activeItem.condition}
            </h4>
            <p className="text-on-surface-variant text-[11px]">
              Precipitation: {activeItem.precip || 0}% ({activeItem.precipMm || 0.0} mm/h)
            </p>
          </div>
        </div>

        <div className="flex gap-6 text-on-surface-variant">
          <div>
            <span className="text-[10px] block text-on-surface-variant/70 uppercase font-label-caps">Humidity</span>
            <span className="font-bold text-on-surface">{activeItem.humidity || currentCity?.humidity || 65}%</span>
          </div>
          <div>
            <span className="text-[10px] block text-on-surface-variant/70 uppercase font-label-caps">Wind</span>
            <span className="font-bold text-on-surface">{activeItem.windKm || currentCity?.windKm || 10} km/h {activeItem.windDir || currentCity?.windDirection || 'N'}</span>
          </div>
          <div>
            <span className="text-[10px] block text-on-surface-variant/70 uppercase font-label-caps">Dew Point</span>
            <span className="font-bold text-on-surface">{formatTemp(activeItem.dewC || currentCity?.dewPointC || 18, activeItem.dewF || currentCity?.dewPointF || 64)}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

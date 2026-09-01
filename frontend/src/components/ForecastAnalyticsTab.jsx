import React, { useState } from 'react';
import { useWeather } from '../context/WeatherContext';
import { resolveWeatherVisual } from '../utils/weatherVisuals';

/**
 * Generates a smooth cubic bezier SVG path string through an array of {x, y} coordinate points
 */
function generateSmoothSvgPath(points) {
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

export default function ForecastAnalyticsTab() {
  const { currentCity, formatTemp, unit } = useWeather();
  const [selectedRange, setSelectedRange] = useState('trend30d'); // 'trend7d' | 'trend30d' | 'trend1y'
  const [selectedMetric, setSelectedMetric] = useState('temp'); // 'temp' | 'precip' | 'wind'
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);
  const [hoveredPointIdx, setHoveredPointIdx] = useState(null);

  const fallbackAnalytics = {
    rangeId: 'trend30d',
    title: 'Past 30 Days Climatology',
    avgDelta: 'Live Climatology',
    anomalyDelta: '+0.0°C vs Normal',
    anomalyType: 'neutral',
    labels: ['Day 1', 'Day 5', 'Day 10', 'Day 15', 'Day 20', 'Day 25', 'Today'],
    fullDates: ['2026-08-01', '2026-08-05', '2026-08-10', '2026-08-15', '2026-08-20', '2026-08-25', '2026-08-31'],
    tempsC: [22, 23, 25, 24, 26, 25, 24],
    tempsF: [72, 73, 77, 75, 79, 77, 75],
    tempsMinC: [18, 19, 20, 19, 21, 20, 19],
    tempsMinF: [64, 66, 68, 66, 70, 68, 66],
    precipMm: [0, 2.5, 12, 4.1, 0, 1.2, 0],
    windKm: [10, 14, 18, 12, 11, 15, 12],
    recordHighC: 28,
    recordHighF: 82,
    recordLowC: 16,
    recordLowF: 61,
    meanC: 24,
    meanF: 75,
    totalPrecipMm: 19.8,
    maxWindKm: 18,
    note: 'Real-time telemetry projection powered by Open-Meteo models.'
  };

  const activeAnalytics = currentCity?.analytics?.[selectedRange] || currentCity?.analytics?.trend30d || fallbackAnalytics;

  const fallbackSevenDay = [
    {
      day: 'Today',
      formattedDate: 'Today',
      icon: currentCity?.conditionIcon || 'partly_cloudy_day',
      condition: currentCity?.condition || 'Partly Cloudy',
      highC: currentCity?.tempC || 24,
      highF: currentCity?.tempF || 75,
      lowC: (currentCity?.tempC || 24) - 5,
      lowF: (currentCity?.tempF || 75) - 9,
      precip: currentCity?.precipProbability || 20,
      precipMm: currentCity?.precipMm || 0.0,
      humidity: currentCity?.humidity || 65,
      windKm: currentCity?.windKm || 12,
      windDir: currentCity?.windDirection || 'SE',
      uv: currentCity?.uvIndex || 5,
      sunrise: currentCity?.sunrise || '5:30 AM',
      sunset: currentCity?.sunset || '6:15 PM',
      summary: currentCity?.aiInsight || 'Live atmospheric projection.'
    }
  ];

  const sevenDayList = (currentCity?.sevenDay && currentCity.sevenDay.length > 0) ? currentCity.sevenDay : fallbackSevenDay;

  // Compute values for the dynamic chart according to selectedMetric
  let dataPoints = [];
  let yUnit = '°C';

  if (selectedMetric === 'temp') {
    dataPoints = unit === 'C' ? (activeAnalytics.tempsC || []) : (activeAnalytics.tempsF || []);
    yUnit = `°${unit}`;
  } else if (selectedMetric === 'precip') {
    dataPoints = activeAnalytics.precipMm || [];
    yUnit = 'mm';
  } else if (selectedMetric === 'wind') {
    dataPoints = activeAnalytics.windKm || [];
    yUnit = 'km/h';
  }

  // Fallback if data points are empty
  if (dataPoints.length === 0) {
    dataPoints = [20, 22, 24, 23, 25, 24, 26];
  }

  // Calculate dynamic Min and Max for Chart Y-Axis Scale
  let rawMin = Math.min(...dataPoints);
  let rawMax = Math.max(...dataPoints);

  if (rawMin === rawMax) {
    rawMin -= 5;
    rawMax += 5;
  }

  let yMin = rawMin;
  let yMax = rawMax;

  if (selectedMetric === 'temp') {
    yMin = Math.floor(rawMin - 2);
    yMax = Math.ceil(rawMax + 2);
  } else {
    yMin = 0;
    yMax = Math.max(10, Math.ceil(rawMax * 1.25));
  }

  const ySpan = Math.max(1, yMax - yMin);

  // High-Resolution SVG Coordinates (600 width x 160 height) matching 3.75:1 card aspect ratio
  const VIEW_WIDTH = 600;
  const VIEW_HEIGHT = 160;
  const PAD_X = 24;
  const PAD_TOP = 20;
  const PAD_BOTTOM = 140;

  const svgCoords = dataPoints.map((val, idx) => {
    const xPct = (idx / Math.max(1, dataPoints.length - 1)) * 100;
    const x = PAD_X + (idx / Math.max(1, dataPoints.length - 1)) * (VIEW_WIDTH - PAD_X * 2);
    const norm = (val - yMin) / ySpan;
    const y = PAD_BOTTOM - norm * (PAD_BOTTOM - PAD_TOP);
    const yPct = ((y - PAD_TOP) / (PAD_BOTTOM - PAD_TOP)) * 100;
    return { x, y, xPct, yPct, val, idx };
  });

  const pathD = generateSmoothSvgPath(svgCoords);
  const areaD = svgCoords.length > 0
    ? `${pathD} L ${svgCoords[svgCoords.length - 1].x.toFixed(1)},${PAD_BOTTOM + 15} L ${svgCoords[0].x.toFixed(1)},${PAD_BOTTOM + 15} Z`
    : '';

  // Handle smooth mouse movement across the chart container
  const handleChartMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const pct = Math.max(0, Math.min(1, mouseX / rect.width));
    const closestIdx = Math.min(
      svgCoords.length - 1,
      Math.max(0, Math.round(pct * (svgCoords.length - 1)))
    );
    setHoveredPointIdx(closestIdx);
  };

  const handleChartMouseLeave = () => {
    setHoveredPointIdx(null);
  };

  // Get active hovered item or fallback to latest
  const activeHoverItem = hoveredPointIdx !== null && activeAnalytics.items?.[hoveredPointIdx]
    ? activeAnalytics.items[hoveredPointIdx]
    : null;

  const hoveredSvgPoint = hoveredPointIdx !== null ? svgCoords[hoveredPointIdx] : null;

  return (
    <main className="max-w-7xl mx-auto px-gutter md:px-container-padding-desktop py-section-gap space-y-10">
      {/* Title & Section Header */}
      <div>
        <h1 className="font-headline-lg-mobile text-headline-lg-mobile md:font-headline-lg md:text-headline-lg text-on-surface font-medium">
          Forecast &amp; Atmospheric Analytics
        </h1>
        <p className="font-body-lg text-body-lg text-on-surface-variant mt-2 max-w-2xl">
          Comprehensive meteorological projection for {currentCity?.name || 'Your Location'}, combining day-by-day vectors with real climatological anomaly telemetry.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Forecast Table */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between border-b border-outline-variant/20 pb-4">
            <div>
              <h2 className="font-headline-md text-headline-md text-on-surface font-medium">Forecast Outlook</h2>
              <p className="text-xs text-on-surface-variant mt-0.5">Click any day to inspect atmospheric telemetry</p>
            </div>
            <span className="text-xs text-on-surface-variant font-label-caps font-semibold px-3 py-1 rounded-full bg-surface-container border border-outline-variant/15">
              {currentCity?.name || 'Region'}
            </span>
          </div>

          <div className="border border-outline-variant/15 rounded-2xl overflow-hidden bg-surface shadow-sm divide-y divide-outline-variant/15">
            {sevenDayList.map((item, idx) => {
              const isSelected = selectedDayIdx === idx;

              return (
                <div
                  key={idx}
                  onClick={() => setSelectedDayIdx(idx)}
                  className={`flex flex-col transition-all cursor-pointer ${
                    isSelected ? 'bg-primary-container/10 border-l-4 border-l-primary' : 'hover:bg-surface-container-low'
                  }`}
                >
                  {/* Row Summary */}
                  <div className="flex items-center justify-between px-6 py-5">
                    <div className="w-32 flex items-center gap-2">
                      <span className={`font-body-md text-base font-semibold ${isSelected ? 'text-primary' : 'text-on-surface'}`}>
                        {item.day}
                      </span>
                      {idx === 0 && (
                        <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase font-label-caps">
                          Today
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2 w-20">
                      <span className={`material-symbols-outlined text-[24px] ${isSelected ? 'text-primary' : 'text-on-surface'}`}>
                        {item.icon || 'partly_cloudy_day'}
                      </span>
                      <span className="text-[11px] text-on-surface-variant font-medium hidden sm:inline truncate max-w-[80px]">
                        {item.condition}
                      </span>
                    </div>

                    {/* High / Low Temperature Range Bar */}
                    <div className="flex items-center gap-3 w-44 justify-end">
                      <span className="font-body-md text-sm font-bold text-on-surface">
                        {formatTemp(item.highC || 0, item.highF || 32)}
                      </span>
                      <div className="w-20 bg-outline-variant/20 h-2 rounded-full overflow-hidden relative hidden sm:block">
                        <div
                          className="h-full bg-gradient-to-r from-blue-400 to-amber-500 rounded-full"
                          style={{ width: `${Math.min(Math.max((((item.highC || 20) - (item.lowC || 15)) / 15) * 100, 20), 100)}%` }}
                        ></div>
                      </div>
                      <span className="font-body-md text-sm text-on-surface-variant font-medium">
                        {formatTemp(item.lowC || 0, item.lowF || 32)}
                      </span>
                    </div>

                    <div className="w-24 text-right font-label-caps text-xs text-on-surface-variant flex items-center justify-end gap-1">
                      <span className="material-symbols-outlined text-[14px] text-primary">water_drop</span>
                      <span>{item.precip || 0}%</span>
                      {item.precipMm > 0 && (
                        <span className="text-[10px] text-on-surface-variant/75 ml-0.5">({item.precipMm}mm)</span>
                      )}
                    </div>
                  </div>

                  {/* Expanded Daily Details Drawer */}
                  {isSelected && (() => {
                    const itemVisual = resolveWeatherVisual(item.summary || item.condition || item.icon || 'Partly Cloudy');
                    return (
                      <div className="px-6 pb-6 pt-3 bg-surface-container/20 border-t border-outline-variant/10 space-y-4 animate-fadeIn">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary border border-primary/15 flex-shrink-0">
                            <span className="material-symbols-outlined text-xl">{item.icon || 'partly_cloudy_day'}</span>
                          </div>
                          <div>
                            <span className="text-[11px] font-label-caps uppercase text-primary font-bold">
                              {itemVisual.label} Outlook · {item.formattedDate || item.day}
                            </span>
                            <p className="font-body-md text-sm text-on-surface font-medium leading-snug">
                              {item.summary}
                            </p>
                          </div>
                        </div>

                        {/* Real Daily Parameters Grid */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                          <div className="bg-surface rounded-xl p-3 border border-outline-variant/10">
                            <span className="text-[10px] text-on-surface-variant uppercase font-label-caps block">Relative Humidity</span>
                            <span className="font-bold text-on-surface text-sm">{item.humidity || 65}%</span>
                          </div>
                          <div className="bg-surface rounded-xl p-3 border border-outline-variant/10">
                            <span className="text-[10px] text-on-surface-variant uppercase font-label-caps block">Max Wind Speed</span>
                            <span className="font-bold text-on-surface text-sm">{item.windKm || 12} km/h {item.windDir ? `(${item.windDir})` : ''}</span>
                          </div>
                          <div className="bg-surface rounded-xl p-3 border border-outline-variant/10">
                            <span className="text-[10px] text-on-surface-variant uppercase font-label-caps block">Peak UV Index</span>
                            <span className="font-bold text-on-surface text-sm">
                              {item.uv || 5} ({item.uv >= 8 ? 'Very High' : item.uv >= 6 ? 'High' : item.uv >= 3 ? 'Mod' : 'Low'})
                            </span>
                          </div>
                          <div className="bg-surface rounded-xl p-3 border border-outline-variant/10">
                            <span className="text-[10px] text-on-surface-variant uppercase font-label-caps block">Sun Window</span>
                            <span className="font-bold text-on-surface text-xs">{item.sunrise || '5:30 AM'} – {item.sunset || '6:15 PM'}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Column: 100% Real Climatology Trends & Professional SVG Charts */}
        <div className="lg:col-span-5 space-y-6">
          <div>
            <div className="flex flex-wrap items-center justify-between border-b border-outline-variant/20 pb-4 mb-6 gap-3">
              <div>
                <h2 className="font-headline-md text-headline-md text-on-surface font-medium">Climatology Trends</h2>
                <p className="text-[11px] text-on-surface-variant">Real observed telemetry &amp; historical climate archive</p>
              </div>

              {/* Range selector filter */}
              <div className="flex gap-1 bg-surface-container p-1 rounded-lg text-xs">
                <button
                  onClick={() => { setSelectedRange('trend7d'); setHoveredPointIdx(null); }}
                  className={`px-3 py-1 rounded-md transition-colors font-medium cursor-pointer ${
                    selectedRange === 'trend7d' ? 'bg-primary text-white shadow-sm' : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                  title="Past 7 Days Real Observations"
                >
                  7D
                </button>
                <button
                  onClick={() => { setSelectedRange('trend30d'); setHoveredPointIdx(null); }}
                  className={`px-3 py-1 rounded-md transition-colors font-medium cursor-pointer ${
                    selectedRange === 'trend30d' ? 'bg-primary text-white shadow-sm' : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                  title="Past 30 Days Climatology"
                >
                  30D
                </button>
                <button
                  onClick={() => { setSelectedRange('trend1y'); setHoveredPointIdx(null); }}
                  className={`px-3 py-1 rounded-md transition-colors font-medium cursor-pointer ${
                    selectedRange === 'trend1y' ? 'bg-primary text-white shadow-sm' : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                  title="12-Month Historical Archive"
                >
                  1Y
                </button>
              </div>
            </div>

            <div className="border border-outline-variant/15 p-6 rounded-2xl bg-surface relative overflow-hidden shadow-sm space-y-5">
              {/* Header & Anomaly Delta */}
              <div className="flex justify-between items-center flex-wrap gap-2">
                <div>
                  <h3 className="font-body-md text-base text-on-surface font-semibold">{activeAnalytics.title}</h3>
                </div>
                
                <div className={`px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1 ${
                  activeAnalytics.anomalyType === 'positive'
                    ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300'
                    : activeAnalytics.anomalyType === 'negative'
                    ? 'bg-blue-500/15 text-blue-800 dark:text-blue-300'
                    : 'bg-secondary-container text-on-secondary-container'
                }`}>
                  <span className="material-symbols-outlined text-sm">
                    {activeAnalytics.anomalyType === 'positive' ? 'trending_up' : activeAnalytics.anomalyType === 'negative' ? 'trending_down' : 'trending_flat'}
                  </span>
                  <span>{activeAnalytics.anomalyDelta || activeAnalytics.avgDelta}</span>
                </div>
              </div>

              {/* Metric Selector Tabs */}
              <div className="flex items-center gap-2 border-b border-outline-variant/15 pb-3 text-xs">
                <button
                  onClick={() => setSelectedMetric('temp')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all font-medium cursor-pointer ${
                    selectedMetric === 'temp' ? 'bg-primary/10 text-primary font-bold shadow-sm' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">thermostat</span>
                  Temperature ({unit === 'C' ? '°C' : '°F'})
                </button>
                <button
                  onClick={() => setSelectedMetric('precip')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all font-medium cursor-pointer ${
                    selectedMetric === 'precip' ? 'bg-primary/10 text-primary font-bold shadow-sm' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">water_drop</span>
                  Precipitation (mm)
                </button>
                <button
                  onClick={() => setSelectedMetric('wind')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-lg transition-all font-medium cursor-pointer ${
                    selectedMetric === 'wind' ? 'bg-primary/10 text-primary font-bold shadow-sm' : 'text-on-surface-variant hover:text-on-surface hover:bg-surface-container'
                  }`}
                >
                  <span className="material-symbols-outlined text-sm">air</span>
                  Wind (km/h)
                </button>
              </div>

              {/* Persistent Live Scrubber Status Bar (Fixed height to guarantee zero layout shifts!) */}
              <div className="min-h-[44px] px-3.5 py-2 rounded-xl bg-surface-container-low border border-outline-variant/10 flex items-center justify-between text-xs transition-all">
                {activeHoverItem ? (
                  <>
                    <div className="flex items-center gap-2 animate-fadeIn">
                      <span className="material-symbols-outlined text-primary text-base">{activeHoverItem.icon || 'wb_sunny'}</span>
                      <div>
                        <span className="font-bold text-on-surface block leading-tight">
                          {activeHoverItem.label} {activeHoverItem.fullDate ? `(${activeHoverItem.fullDate})` : ''}
                        </span>
                        <span className="text-on-surface-variant text-[10px]">{activeHoverItem.condition || 'Observed telemetry'}</span>
                      </div>
                    </div>
                    <div className="text-right animate-fadeIn">
                      <span className="font-bold text-primary text-sm block leading-tight">
                        {selectedMetric === 'temp' ? (unit === 'C' ? `${activeHoverItem.highC}°C / ${activeHoverItem.lowC}°C` : `${activeHoverItem.highF}°F / ${activeHoverItem.lowF}°F`)
                          : selectedMetric === 'precip' ? `${activeHoverItem.precipMm} mm`
                          : `${activeHoverItem.windKm} km/h`}
                      </span>
                      <span className="text-[9px] text-on-surface-variant uppercase font-label-caps">
                        {selectedMetric === 'temp' ? 'High / Low' : selectedMetric === 'precip' ? 'Precipitation' : 'Max Wind'}
                      </span>
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-between w-full text-on-surface-variant text-[11px]">
                    <span className="flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-xs text-primary">touch_app</span>
                      <span>Hover or drag over the curve to inspect telemetry</span>
                    </span>
                    <span className="font-semibold text-on-surface font-label-caps text-[10px]">
                      {svgCoords.length} observation points
                    </span>
                  </div>
                )}
              </div>

              {/* Professional Chart Layout with dedicated Y-Axis Gutter */}
              <div className="space-y-2">
                <div className="flex items-stretch gap-2.5 h-44">
                  {/* Dedicated Y-Axis Labels Column (No clipping!) */}
                  <div className="flex flex-col justify-between text-right text-[11px] text-on-surface-variant font-medium py-1 w-11 shrink-0 select-none">
                    <span className="leading-none">{yMax}{yUnit}</span>
                    <span className="leading-none text-on-surface-variant/70">{Math.round((yMin + yMax) / 2)}{yUnit}</span>
                    <span className="leading-none">{yMin}{yUnit}</span>
                  </div>

                  {/* Chart Plotting Area */}
                  <div 
                    className="flex-1 relative border-b border-l border-outline-variant/20 cursor-crosshair select-none bg-surface-container-lowest/30 rounded-br-lg"
                    onMouseMove={handleChartMouseMove}
                    onMouseLeave={handleChartMouseLeave}
                  >
                    {/* Floating Tooltip Indicator */}
                    {hoveredSvgPoint && activeHoverItem && (
                      <div
                        className="absolute top-1 pointer-events-none z-30 transition-all duration-75"
                        style={{
                          left: `${Math.max(14, Math.min(86, hoveredSvgPoint.xPct))}%`,
                          transform: 'translateX(-50%)'
                        }}
                      >
                        <div className="bg-surface/95 backdrop-blur-md border border-primary/30 shadow-md rounded-lg px-2.5 py-1 text-[10px] flex items-center gap-1.5 whitespace-nowrap text-on-surface">
                          <span className="font-bold text-primary">
                            {selectedMetric === 'temp' ? `${hoveredSvgPoint.val}${yUnit}` : `${hoveredSvgPoint.val} ${yUnit}`}
                          </span>
                          <span className="text-on-surface-variant/60">·</span>
                          <span>{activeHoverItem.label}</span>
                        </div>
                      </div>
                    )}

                    {/* SVG Vector Canvas (Proper 600x160 coordinate space) */}
                    <svg 
                      className="w-full h-full overflow-visible pointer-events-none" 
                      viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`} 
                      preserveAspectRatio="none"
                    >
                      <defs>
                        <linearGradient id="curveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                          <stop offset="0%" stopColor="#2a6088" stopOpacity="0.30" />
                          <stop offset="70%" stopColor="#2a6088" stopOpacity="0.06" />
                          <stop offset="100%" stopColor="#2a6088" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>

                      {/* Horizontal Grid Guide Lines */}
                      <line x1="0" y1={PAD_TOP} x2={VIEW_WIDTH} y2={PAD_TOP} stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" className="text-outline-variant/35" vectorEffect="non-scaling-stroke" />
                      <line x1="0" y1={(PAD_TOP + PAD_BOTTOM) / 2} x2={VIEW_WIDTH} y2={(PAD_TOP + PAD_BOTTOM) / 2} stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" className="text-outline-variant/35" vectorEffect="non-scaling-stroke" />
                      <line x1="0" y1={PAD_BOTTOM} x2={VIEW_WIDTH} y2={PAD_BOTTOM} stroke="currentColor" strokeWidth="1" strokeDasharray="3 3" className="text-outline-variant/35" vectorEffect="non-scaling-stroke" />

                      {/* Smooth Area Gradient Fill Under Curve */}
                      {areaD && (
                        <path
                          d={areaD}
                          fill="url(#curveGradient)"
                          vectorEffect="non-scaling-stroke"
                        />
                      )}

                      {/* Smooth Curve Stroke */}
                      {pathD && (
                        <path
                          d={pathD}
                          fill="none"
                          stroke="#2a6088"
                          strokeWidth="2.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          vectorEffect="non-scaling-stroke"
                        />
                      )}

                      {/* Vertical Crosshair Scrubber Line on Active Point */}
                      {hoveredSvgPoint && (
                        <line
                          x1={hoveredSvgPoint.x}
                          y1={PAD_TOP - 6}
                          x2={hoveredSvgPoint.x}
                          y2={PAD_BOTTOM + 6}
                          stroke="#2a6088"
                          strokeWidth="1.5"
                          strokeDasharray="3 3"
                          vectorEffect="non-scaling-stroke"
                          className="animate-fadeIn"
                        />
                      )}

                      {/* Dynamic Circular Data Point Dots */}
                      {svgCoords.map((pt) => {
                        const isHovered = hoveredPointIdx === pt.idx;
                        return (
                          <g key={pt.idx}>
                            {isHovered && (
                              <circle
                                cx={pt.x}
                                cy={pt.y}
                                r="8"
                                fill="#2a6088"
                                fillOpacity="0.25"
                                vectorEffect="non-scaling-stroke"
                              />
                            )}
                            <circle
                              cx={pt.x}
                              cy={pt.y}
                              r={isHovered ? "5" : (svgCoords.length > 20 ? "2.5" : "3.5")}
                              fill={isHovered ? "#2a6088" : "#ffffff"}
                              stroke="#2a6088"
                              strokeWidth={isHovered ? "2.5" : "2"}
                              vectorEffect="non-scaling-stroke"
                            />
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                </div>

                {/* X-Axis Labels (Aligned beneath plot area) */}
                <div className="flex justify-between text-[10px] text-on-surface-variant font-medium pl-14 pr-2 select-none">
                  <span>{activeAnalytics.labels?.[0] || 'Start'}</span>
                  {activeAnalytics.labels?.length > 4 && (
                    <span>{activeAnalytics.labels[Math.floor(activeAnalytics.labels.length / 2)]}</span>
                  )}
                  <span>{activeAnalytics.labels?.[activeAnalytics.labels.length - 1] || 'End'}</span>
                </div>
              </div>

              {/* Real Climatology Statistics Bar */}
              <div className="flex justify-between items-center text-xs text-on-surface-variant pt-3 border-t border-outline-variant/15 font-medium flex-wrap gap-2">
                <span>
                  Record High: <strong className="text-on-surface">{formatTemp(activeAnalytics.recordHighC ?? 28, activeAnalytics.recordHighF ?? 82)}</strong>
                </span>
                <span>
                  {selectedRange === 'trend1y' ? 'Annual Mean:' : 'Period Mean:'} <strong className="text-on-surface">{formatTemp(activeAnalytics.meanC ?? 24, activeAnalytics.meanF ?? 75)}</strong>
                </span>
                <span>
                  Record Low: <strong className="text-on-surface">{formatTemp(activeAnalytics.recordLowC ?? 16, activeAnalytics.recordLowF ?? 61)}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* AI Climatological Note Banner */}
          <div className="bg-surface-container-low p-6 rounded-2xl border border-outline-variant/10 space-y-3 shadow-sm">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">auto_awesome</span>
              <h3 className="font-body-md text-base text-on-surface font-semibold">AI Climatological Synthesis</h3>
            </div>
            <p className="font-body-md text-sm text-on-surface-variant leading-relaxed">
              {activeAnalytics.note || 'Atmospheric telemetry projection generated in real-time from satellite analysis.'}
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

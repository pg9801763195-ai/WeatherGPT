import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import { useWeather } from '../context/WeatherContext';
import { MAP_LAYERS, DEFAULT_CITIES } from '../constants/appConfig';
import { reverseGeocodeCoords } from '../services/weatherApi';

export default function MapAlertCenterTab() {
  const { currentCity, openAlertModal, loadLiveWeather, formatTemp, unit, showToast, t, translateCondition } = useWeather();
  
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const radarLayerRef = useRef(null);
  const regionalLayerGroupRef = useRef(null);
  const canvasWindLayerRef = useRef(null);
  const windAnimFrameRef = useRef(null);

  const [activeLayer, setActiveLayer] = useState('rain'); // 'rain' | 'temperature' | 'wind' | 'clouds'
  const [currentFrameIdx, setCurrentFrameIdx] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [radarFrames, setRadarFrames] = useState([
    { time: 'Now', label: 'Now', path: '' }
  ]);
  const [radarHost, setRadarHost] = useState('https://tilecache.rainviewer.com');
  const [regionalWeatherData, setRegionalWeatherData] = useState([]);

  // 1. Fetch Real-time RainViewer Radar Metadata (100% Keyless)
  useEffect(() => {
    let isMounted = true;
    async function loadRainViewerData() {
      try {
        const res = await fetch('https://api.rainviewer.com/public/weather-maps.json');
        if (!res.ok) throw new Error('Failed to load radar');
        const data = await res.json();
        if (!isMounted) return;

        if (data.host) setRadarHost(data.host);

        const past = data.radar?.past || [];
        const nowcast = data.radar?.nowcast || [];
        const allRadar = [...past, ...nowcast];

        if (allRadar.length > 0) {
          const parsedRadar = allRadar.map((f, i) => {
            const date = new Date(f.time * 1000);
            const isNow = i === past.length - 1;
            const timeLabel = isNow ? 'Now' : date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true });
            const diffMin = Math.round((date.getTime() - Date.now()) / 60000);
            const timeTag = isNow ? 'Now' : diffMin > 0 ? `+${diffMin}m` : `${diffMin}m`;

            return {
              time: timeTag,
              label: timeLabel,
              path: f.path,
              timestamp: f.time
            };
          });

          setRadarFrames(parsedRadar);
          setCurrentFrameIdx(Math.max(0, past.length - 1));
        }
      } catch (err) {
        console.warn('RainViewer API error:', err);
      }
    }

    loadRainViewerData();
    return () => {
      isMounted = false;
    };
  }, []);

  // 2. Fetch Live Real Multi-Point Regional Grid from Open-Meteo for Surrounding Area
  useEffect(() => {
    let isMounted = true;
    async function fetchRegionalPoints() {
      if (!currentCity?.lat || !currentCity?.lon) return;

      const centerLat = currentCity.lat;
      const centerLon = currentCity.lon;

      // Sample 8 regional points around the current active city
      const offsets = [
        { dLat: 0.8, dLon: 0.0, name: 'North Corridor' },
        { dLat: -0.8, dLon: 0.0, name: 'South Valley' },
        { dLat: 0.0, dLon: 0.9, name: 'Eastern Plateau' },
        { dLat: 0.0, dLon: -0.9, name: 'Western Ridge' },
        { dLat: 0.6, dLon: 0.6, name: 'NE Highlands' },
        { dLat: -0.6, dLon: 0.6, name: 'SE Sector' },
        { dLat: -0.6, dLon: -0.6, name: 'SW Sector' },
        { dLat: 0.6, dLon: -0.6, name: 'NW Sector' }
      ];

      const lats = [centerLat, ...offsets.map(o => centerLat + o.dLat)];
      const lons = [centerLon, ...offsets.map(o => centerLon + o.dLon)];

      try {
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lats.map(l => l.toFixed(4)).join(',')}&longitude=${lons.map(l => l.toFixed(4)).join(',')}&current=temperature_2m,relative_humidity_2m,precipitation,rain,showers,cloud_cover,wind_speed_10m,wind_direction_10m,weather_code&timezone=auto`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed regional fetch');
        const data = await res.json();
        if (!isMounted) return;

        const results = Array.isArray(data) ? data : [data];
        const points = results.map((item, idx) => {
          const lat = lats[idx];
          const lon = lons[idx];
          const curr = item.current || {};
          const label = idx === 0 ? currentCity.name : offsets[idx - 1].name;
          const tC = Math.round(curr.temperature_2m ?? currentCity.tempC ?? 24);
          const tF = Math.round((tC * 9) / 5 + 32);

          // Get authoritative precipitation reading combining Open-Meteo & live station data
          const directPrecip = curr.precipitation ?? curr.rain ?? curr.showers ?? 0;
          const cityPrecip = idx === 0 ? (currentCity?.precipMm ?? 0) : 0;
          const isRainingDesc = idx === 0 && currentCity?.condition && /rain|drizzle|shower|thunderstorm/i.test(currentCity.condition);
          const finalPrecip = Math.max(
            Number(directPrecip.toFixed(1)),
            Number(cityPrecip.toFixed(1)),
            isRainingDesc && directPrecip === 0 && cityPrecip === 0 ? 0.3 : 0
          );

          return {
            id: `reg-${idx}`,
            lat,
            lon,
            name: label,
            isCenter: idx === 0,
            tempC: tC,
            tempF: tF,
            humidity: Math.round(curr.relative_humidity_2m ?? 65),
            precipMm: finalPrecip,
            cloudCover: Math.round(curr.cloud_cover ?? 45),
            windKm: Math.round(curr.wind_speed_10m ?? 12),
            windDeg: Math.round(curr.wind_direction_10m ?? 0)
          };
        });

        setRegionalWeatherData(points);
      } catch (err) {
        console.warn('Regional weather fetch warning:', err);
      }
    }

    fetchRegionalPoints();
    return () => {
      isMounted = false;
    };
  }, [currentCity?.lat, currentCity?.lon, currentCity?.name, currentCity?.condition, currentCity?.precipMm]);


  // 3. Initialize Real Leaflet Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return;
    if (mapInstanceRef.current) return;

    const initialLat = currentCity?.lat || 20.5937;
    const initialLon = currentCity?.lon || 78.9629;

    const map = L.map(mapContainerRef.current, {
      center: [initialLat, initialLon],
      zoom: 9,
      zoomControl: false,
      attributionControl: false
    });

    // Unrestricted OpenStreetMap Tiles (No API key, zero restrictions)
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      subdomains: 'abc'
    }).addTo(map);

    // Layer group for dynamic weather markers
    const group = L.layerGroup().addTo(map);
    regionalLayerGroupRef.current = group;

    // Click anywhere on map to inspect weather
    map.on('click', async (e) => {
      const { lat, lng } = e.latlng;
      showToast('Resolving location from map coordinates...');
      try {
        const geoInfo = await reverseGeocodeCoords(lat, lng);
        await loadLiveWeather({
          lat,
          lon: lng,
          name: geoInfo.name,
          region: geoInfo.region,
          country: geoInfo.country
        });
      } catch (err) {
        console.error('Map click error:', err);
      }
    });

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 4. Update Main Center Marker when City Changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    if (!currentCity?.lat || !currentCity?.lon) return;

    const lat = currentCity.lat;
    const lon = currentCity.lon;

    mapInstanceRef.current.flyTo([lat, lon], 9, {
      duration: 1.2
    });

    if (markerRef.current) {
      markerRef.current.setLatLng([lat, lon]);
    } else {
      const customIcon = L.divIcon({
        className: 'custom-weather-pin',
        html: `
          <div class="relative flex items-center justify-center cursor-pointer group">
            <span class="absolute w-9 h-9 rounded-full bg-primary/35 animate-ping"></span>
            <div class="relative w-7 h-7 rounded-full bg-primary border-2 border-white shadow-xl flex items-center justify-center text-white">
              <span class="material-symbols-outlined text-sm">location_on</span>
            </div>
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14]
      });

      const marker = L.marker([lat, lon], { icon: customIcon }).addTo(mapInstanceRef.current);
      markerRef.current = marker;
    }

    if (markerRef.current) {
      const tempDisplay = currentCity?.tempC !== null && currentCity?.tempC !== undefined ? formatTemp(currentCity.tempC, currentCity.tempF) : '--°';
      markerRef.current.bindPopup(`
        <div style="font-family: 'Inter', sans-serif; padding: 4px; min-width: 140px;">
          <div style="font-weight: 700; font-size: 13px; color: #191c1f;">${currentCity.name}</div>
          <div style="font-size: 11px; color: #72787f; margin-bottom: 4px;">${currentCity.region || currentCity.country || ''}</div>
          <div style="display: flex; align-items: center; justify-content: space-between; font-weight: 700; font-size: 14px; color: #2a6088; border-top: 1px solid #e2e8f0; padding-top: 4px;">
            <span>${tempDisplay}</span>
            <span style="font-size: 11px; font-weight: 500; color: #475569;">${currentCity.condition || ''}</span>
          </div>
        </div>
      `, { closeButton: false, offset: [0, -8] });
    }
  }, [currentCity?.lat, currentCity?.lon, currentCity?.tempC, currentCity?.tempF, currentCity?.condition, unit]);

  // 5. Render Dynamic Layer Overlays & Real Regional Data Markers
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const map = mapInstanceRef.current;

    // Clean radar tile overlay
    if (radarLayerRef.current) {
      map.removeLayer(radarLayerRef.current);
      radarLayerRef.current = null;
    }

    // Clean regional markers
    if (regionalLayerGroupRef.current) {
      regionalLayerGroupRef.current.clearLayers();
    }

    // LAYER 1: RAINFALL RADAR
    if (activeLayer === 'rain') {
      if (radarFrames.length > 0) {
        const activeFrame = radarFrames[currentFrameIdx] || radarFrames[radarFrames.length - 1];
        if (activeFrame?.path) {
          const tileUrl = `${radarHost}${activeFrame.path}/256/{z}/{x}/{y}/2/1_1.png`;
          const layer = L.tileLayer(tileUrl, {
            opacity: 0.85,
            zIndex: 10,
            maxNativeZoom: 6,
            maxZoom: 19,
            errorTileUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='
          }).addTo(map);
          radarLayerRef.current = layer;
        }
      }

      // Add real precipitation telemetry badges for regional points
      regionalWeatherData.forEach(pt => {
        const hasRain = pt.precipMm > 0;
        const icon = L.divIcon({
          className: 'precip-marker',
          html: `
            <div class="px-2 py-1 rounded-full text-[10px] font-bold shadow-md border flex items-center gap-1 backdrop-blur-md transition-transform hover:scale-110 cursor-pointer ${
              hasRain ? 'bg-blue-600/90 text-white border-blue-400' : 'bg-surface/90 text-on-surface border-outline-variant/30'
            }">
              <span class="material-symbols-outlined text-[12px]">${hasRain ? 'water_drop' : 'grain'}</span>
              <span>${pt.precipMm} mm/h</span>
            </div>
          `,
          iconSize: [80, 24],
          iconAnchor: [40, 12]
        });
        L.marker([pt.lat, pt.lon], { icon }).addTo(regionalLayerGroupRef.current);
      });
    }

    // LAYER 2: TEMPERATURE THERMAL
    if (activeLayer === 'temperature') {
      regionalWeatherData.forEach(pt => {
        const tVal = unit === 'C' ? pt.tempC : pt.tempF;
        const colorClass = pt.tempC > 32 
          ? 'bg-red-500 text-white border-red-300'
          : pt.tempC > 25
          ? 'bg-amber-500 text-white border-amber-300'
          : pt.tempC > 15
          ? 'bg-emerald-600 text-white border-emerald-400'
          : 'bg-blue-600 text-white border-blue-400';

        // Thermal circle radius
        L.circle([pt.lat, pt.lon], {
          radius: 35000,
          color: pt.tempC > 30 ? '#ef4444' : pt.tempC > 22 ? '#f59e0b' : '#10b981',
          fillColor: pt.tempC > 30 ? '#ef4444' : pt.tempC > 22 ? '#f59e0b' : '#10b981',
          fillOpacity: 0.18,
          weight: 1
        }).addTo(regionalLayerGroupRef.current);

        const icon = L.divIcon({
          className: 'thermal-marker',
          html: `
            <div class="px-2.5 py-1 rounded-full text-xs font-bold shadow-lg border flex items-center gap-1.5 backdrop-blur-md transition-transform hover:scale-110 cursor-pointer ${colorClass}">
              <span class="material-symbols-outlined text-sm">thermostat</span>
              <span>${tVal}°</span>
            </div>
          `,
          iconSize: [60, 26],
          iconAnchor: [30, 13]
        });
        L.marker([pt.lat, pt.lon], { icon }).addTo(regionalLayerGroupRef.current);
      });
    }

    // LAYER 3: WIND VELOCITY STREAM
    if (activeLayer === 'wind') {
      regionalWeatherData.forEach(pt => {
        const icon = L.divIcon({
          className: 'wind-marker',
          html: `
            <div class="px-2.5 py-1 rounded-full bg-slate-900/90 text-white border border-slate-700 text-xs font-bold shadow-lg flex items-center gap-1.5 backdrop-blur-md transition-transform hover:scale-110 cursor-pointer">
              <span class="material-symbols-outlined text-sm text-sky-400 transition-transform" style="transform: rotate(${pt.windDeg}deg)">
                navigation
              </span>
              <span>${pt.windKm} km/h</span>
            </div>
          `,
          iconSize: [84, 26],
          iconAnchor: [42, 13]
        });
        L.marker([pt.lat, pt.lon], { icon }).addTo(regionalLayerGroupRef.current);
      });
    }

    // LAYER 4: CLOUD COVERAGE SATELLITE
    if (activeLayer === 'clouds') {
      regionalWeatherData.forEach(pt => {
        // Cloud coverage radius area
        L.circle([pt.lat, pt.lon], {
          radius: 42000,
          color: '#64748b',
          fillColor: '#94a3b8',
          fillOpacity: (pt.cloudCover / 100) * 0.40,
          weight: 1
        }).addTo(regionalLayerGroupRef.current);

        const icon = L.divIcon({
          className: 'cloud-marker',
          html: `
            <div class="px-2.5 py-1 rounded-full bg-slate-800/85 text-white border border-slate-600 text-[11px] font-bold shadow-lg flex items-center gap-1.5 backdrop-blur-md transition-transform hover:scale-110 cursor-pointer">
              <span class="material-symbols-outlined text-sm text-slate-300">cloud</span>
              <span>${pt.cloudCover}% Cover</span>
            </div>
          `,
          iconSize: [95, 26],
          iconAnchor: [47, 13]
        });
        L.marker([pt.lat, pt.lon], { icon }).addTo(regionalLayerGroupRef.current);
      });
    }
  }, [activeLayer, currentFrameIdx, radarFrames, radarHost, regionalWeatherData, unit]);

  // 6. Radar Animation Loop Playback Controller
  useEffect(() => {
    let interval = null;
    if (isPlaying && radarFrames.length > 1) {
      interval = setInterval(() => {
        setCurrentFrameIdx(prev => (prev + 1) % radarFrames.length);
      }, 750);
    }
    return () => clearInterval(interval);
  }, [isPlaying, radarFrames.length]);

  const activeFrame = radarFrames[currentFrameIdx] || radarFrames[0] || { time: 'Now', label: 'Now' };

  // Generate dynamic contextual advisories for active city
  const generatedAdvisories = [];

  if (currentCity?.alert) {
    generatedAdvisories.push(currentCity.alert);
  }

  // Secondary dynamic atmospheric advisories based on real metrics
  if (currentCity?.precipProbability >= 50 || currentCity?.precipMm > 0) {
    generatedAdvisories.push({
      id: 'advisory-rain',
      title: 'Active Precipitation & Roadway Surface Advisory',
      severityLabel: 'Rain Advisory',
      severity: 'advisory',
      timing: 'Active Doppler Projection',
      shortDesc: `Elevated precipitation likelihood (${currentCity.precipProbability}%, ${currentCity.precipMm} mm/h) across ${currentCity.name}. Reduced roadway friction and braking distance.`,
      recommendedAction: 'Drive with low beams, reduce transit speeds on wet pavement, and carry rain gear.',
      affectedAreas: [currentCity.name, currentCity.region || 'Metropolitan Zone'],
      likelyImpact: 'Localized road spray and surface runoff.',
      icon: 'water_drop'
    });
  }

  if (currentCity?.windKm >= 20) {
    generatedAdvisories.push({
      id: 'advisory-wind',
      title: 'Wind Vector & Velocity Advisory',
      severityLabel: 'Breeze Warning',
      severity: 'advisory',
      timing: 'Next 3-6 Hours',
      shortDesc: `Sustained wind velocity of ${currentCity.windKm} km/h from ${currentCity.windDirection} (${currentCity.windDegrees}°). Minor convective gusts possible.`,
      recommendedAction: 'Secure lightweight patio items and exercise caution on elevated bridges.',
      affectedAreas: [currentCity.name],
      likelyImpact: 'Crosswinds on open transit corridors.',
      icon: 'air'
    });
  }

  if (currentCity?.uvIndex >= 6) {
    generatedAdvisories.push({
      id: 'advisory-uv',
      title: 'Solar Irradiance & UV Radiation Advisory',
      severityLabel: 'UV Alert',
      severity: 'advisory',
      timing: '10:00 AM – 4:00 PM',
      shortDesc: `Peak UV Index reached ${currentCity.uvIndex} (${currentCity.uvLabel || 'High'}). Direct sunlight exposure can cause skin irritation within 20 minutes.`,
      recommendedAction: 'Apply SPF 30+ sunscreen, wear protective sunglasses, and seek shade during midday.',
      affectedAreas: [currentCity.name],
      likelyImpact: 'Elevated solar radiation index.',
      icon: 'wb_sunny'
    });
  }

  if (generatedAdvisories.length === 0) {
    generatedAdvisories.push({
      id: 'advisory-nominal',
      title: 'Stable Atmospheric Gradient',
      severityLabel: 'All Clear',
      severity: 'info',
      timing: 'Current Interval',
      shortDesc: `Nominal atmospheric pressure (${currentCity?.pressureHpa || 1013} hPa) and clear horizon visibility (${currentCity?.visibilityKm || 10} km) across ${currentCity?.name}.`,
      recommendedAction: 'Optimal conditions for outdoor activities, travel, and aviation.',
      affectedAreas: [currentCity?.name || 'Region'],
      likelyImpact: 'No active severe meteorological threats.',
      icon: 'check_circle'
    });
  }

  return (
    <main className="flex-1 flex flex-col md:flex-row relative z-0 h-[calc(100vh-73px)] pb-[88px] md:pb-0 overflow-hidden">
      {/* Real Interactive Map Canvas */}
      <section className="flex-1 relative h-[500px] md:h-full flex flex-col bg-surface-container-low overflow-hidden">
        {/* Leaflet Real Map Container */}
        <div ref={mapContainerRef} className="absolute inset-0 z-0 bg-slate-100 dark:bg-slate-900" />

        {/* Map Location Pin & Active Layer Badge */}
        <div className="absolute top-6 left-6 z-10 bg-surface/90 backdrop-blur-md px-4 py-2.5 rounded-2xl border border-outline-variant/20 shadow-md flex items-center gap-3">
          <span className="material-symbols-outlined text-primary text-xl">
            {activeLayer === 'rain' ? 'water_drop' : activeLayer === 'temperature' ? 'thermostat' : activeLayer === 'wind' ? 'air' : 'cloud'}
          </span>
          <div>
            <h4 className="font-headline-md text-sm font-semibold text-on-surface">
              {currentCity?.name || 'Selected City'}, {currentCity?.country || ''}
            </h4>
            <p className="text-xs text-on-surface-variant font-medium flex items-center gap-1.5">
              <span>Mode:</span>
              <strong className="text-primary uppercase tracking-wide font-bold">
                {activeLayer === 'rain' ? `Radar (${activeFrame.label})` : activeLayer === 'temperature' ? 'Thermal Isotherms' : activeLayer === 'wind' ? 'Wind Vectors' : 'Satellite Cloud Cover'}
              </strong>
            </p>
          </div>
        </div>

        {/* Dynamic Contextual Layer Legend */}
        <div className="absolute top-6 right-20 z-10 hidden sm:flex items-center gap-2 bg-surface/90 backdrop-blur-md px-3.5 py-2 rounded-xl border border-outline-variant/20 text-[10px] font-medium shadow-sm">
          {activeLayer === 'rain' && (
            <>
              <span className="text-on-surface-variant font-semibold">Doppler:</span>
              <span className="w-2.5 h-2.5 rounded-full bg-blue-300"></span> <span>Light</span>
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500"></span> <span>Mod</span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> <span>Heavy</span>
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> <span>Severe</span>
            </>
          )}
          {activeLayer === 'temperature' && (
            <>
              <span className="text-on-surface-variant font-semibold">Thermal:</span>
              <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span> <span>&lt;15°C</span>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600"></span> <span>15–25°C</span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> <span>25–32°C</span>
              <span className="w-2.5 h-2.5 rounded-full bg-red-500"></span> <span>&gt;32°C</span>
            </>
          )}
          {activeLayer === 'wind' && (
            <>
              <span className="text-on-surface-variant font-semibold">Velocity:</span>
              <span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span> <span>&lt;15 km/h</span>
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> <span>15–30 km/h</span>
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span> <span>&gt;30 km/h</span>
            </>
          )}
          {activeLayer === 'clouds' && (
            <>
              <span className="text-on-surface-variant font-semibold">Cloud Cover:</span>
              <span className="w-2.5 h-2.5 rounded-full bg-slate-300"></span> <span>Clear</span>
              <span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span> <span>Scattered</span>
              <span className="w-2.5 h-2.5 rounded-full bg-slate-600"></span> <span>Overcast</span>
            </>
          )}
        </div>

        {/* Radar Timeline Controller (Active during Rainfall Radar mode) */}
        {activeLayer === 'rain' && (
          <div className="absolute bottom-20 left-6 right-6 md:left-auto md:right-6 md:w-96 z-20 bg-surface/95 backdrop-blur-xl border border-outline-variant/20 p-4 rounded-2xl shadow-xl space-y-3 animate-fadeIn">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary text-white text-xs font-bold transition-transform active:scale-95 shadow-sm cursor-pointer hover:bg-primary/90"
                >
                  <span className="material-symbols-outlined text-base">
                    {isPlaying ? 'pause' : 'play_arrow'}
                  </span>
                  {isPlaying ? 'Pause' : 'Loop 2h'}
                </button>

                <button
                  onClick={() => {
                    setIsPlaying(false);
                    setCurrentFrameIdx(Math.max(0, radarFrames.length - 1));
                  }}
                  className={`px-2.5 py-1.5 rounded-full text-xs font-bold transition-all active:scale-95 cursor-pointer flex items-center gap-1 ${
                    currentFrameIdx === radarFrames.length - 1 && !isPlaying
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'bg-surface-container-high text-on-surface hover:bg-surface-variant'
                  }`}
                  title="Jump to real-time Doppler radar observation"
                >
                  <span className={`w-2 h-2 rounded-full ${currentFrameIdx === radarFrames.length - 1 ? 'bg-white animate-ping' : 'bg-emerald-500'}`}></span>
                  Live Now
                </button>
              </div>

              <span className={`text-xs font-bold flex items-center gap-1.5 ${currentFrameIdx === radarFrames.length - 1 ? 'text-emerald-600' : 'text-on-surface-variant'}`}>
                {currentFrameIdx === radarFrames.length - 1 ? '🔴 LIVE (Now)' : `Frame ${currentFrameIdx + 1}/${radarFrames.length} (${activeFrame.label})`}
              </span>
            </div>

            <input
              type="range"
              min="0"
              max={Math.max(0, radarFrames.length - 1)}
              value={currentFrameIdx}
              onChange={(e) => {
                setIsPlaying(false);
                setCurrentFrameIdx(parseInt(e.target.value, 10));
              }}
              className="w-full h-1.5 bg-outline-variant/30 rounded-lg appearance-none cursor-pointer accent-primary"
            />

            <div className="flex justify-between text-[10px] text-on-surface-variant font-medium">
              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentFrameIdx(0);
                }}
                className="hover:text-primary transition-colors cursor-pointer"
              >
                {radarFrames[0]?.time || 'Start (-2h)'}
              </button>
              <span>{radarFrames[Math.floor(radarFrames.length / 2)]?.time || ''}</span>
              <button
                type="button"
                onClick={() => {
                  setIsPlaying(false);
                  setCurrentFrameIdx(Math.max(0, radarFrames.length - 1));
                }}
                className="text-primary font-bold hover:underline cursor-pointer flex items-center gap-0.5"
              >
                {radarFrames[radarFrames.length - 1]?.time || 'Now'} ⚡
              </button>
            </div>
          </div>
        )}

        {/* Map Layer Switcher Floating Bar */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 md:translate-x-0 md:left-gutter w-[calc(100%-48px)] md:w-auto overflow-x-auto no-scrollbar flex items-center gap-2.5 p-2 bg-surface/90 backdrop-blur-xl border border-outline-variant/20 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.06)] z-20">
          {MAP_LAYERS.map(layer => (
            <button
              key={layer.id}
              onClick={() => setActiveLayer(layer.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-full font-label-caps text-xs transition-all active:scale-95 whitespace-nowrap cursor-pointer ${
                activeLayer === layer.id
                  ? 'bg-primary text-white shadow-sm font-bold'
                  : 'bg-transparent text-on-surface hover:bg-surface-variant/40 border border-outline-variant/10'
              }`}
            >
              <span className="material-symbols-outlined text-[17px]">{layer.icon}</span>
              {layer.name}
            </button>
          ))}
        </div>

        {/* Map Zoom Controls */}
        <div className="absolute top-6 right-6 z-20 flex flex-col gap-2 bg-surface/80 backdrop-blur-md p-1.5 rounded-xl border border-outline-variant/20 shadow-md">
          <button
            onClick={() => mapInstanceRef.current?.zoomIn()}
            className="p-2 text-on-surface hover:text-primary hover:bg-surface-container rounded-lg transition-colors cursor-pointer"
            title="Zoom In"
          >
            <span className="material-symbols-outlined text-lg">add</span>
          </button>
          <button
            onClick={() => mapInstanceRef.current?.zoomOut()}
            className="p-2 text-on-surface hover:text-primary hover:bg-surface-container rounded-lg transition-colors cursor-pointer"
            title="Zoom Out"
          >
            <span className="material-symbols-outlined text-lg">remove</span>
          </button>
        </div>
      </section>

      {/* Weather Alert Center Sidebar */}
      <aside className="w-full md:w-[420px] lg:w-[460px] flex-shrink-0 h-full bg-surface border-t md:border-t-0 md:border-l border-outline-variant/10 flex flex-col z-10 shadow-[-8px_0_32px_rgba(0,0,0,0.02)]">
        <div className="p-gutter border-b border-outline-variant/10 shrink-0">
          <h2 className="font-headline-md text-headline-md text-on-surface flex items-center gap-3">
            <span className="material-symbols-outlined text-primary text-xl">notifications_active</span>
            Weather Alert Center
          </h2>
          <p className="font-body-md text-xs text-on-surface-variant mt-0.5">
            Active Severe Hazards &amp; Advisories for {currentCity?.name || 'Region'}
          </p>
        </div>

        <div className="flex-1 overflow-y-auto no-scrollbar p-gutter space-y-4">
          {generatedAdvisories.map((adv, idx) => {
            const isSevere = adv.severity === 'severe';
            const isWarning = adv.severity === 'warning';
            const isInfo = adv.severity === 'info';

            return (
              <article 
                key={adv.id || idx}
                onClick={() => openAlertModal(adv)}
                className={`border rounded-2xl p-5 relative overflow-hidden group transition-all cursor-pointer shadow-sm space-y-3 ${
                  isSevere 
                    ? 'bg-error-container/10 border-error/30 hover:border-error/60'
                    : isWarning
                    ? 'bg-amber-500/10 border-amber-500/30 hover:border-amber-500/60'
                    : isInfo
                    ? 'bg-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40'
                    : 'bg-tertiary-container/5 border-tertiary/20 hover:border-tertiary/40'
                }`}
              >
                <div className={`absolute top-0 left-0 w-1.5 h-full ${
                  isSevere ? 'bg-error' : isWarning ? 'bg-amber-500' : isInfo ? 'bg-emerald-500' : 'bg-tertiary'
                }`}></div>

                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`material-symbols-outlined text-xl ${
                      isSevere ? 'text-error' : isWarning ? 'text-amber-600' : isInfo ? 'text-emerald-600' : 'text-tertiary'
                    }`}>
                      {adv.icon || 'warning'}
                    </span>
                    <span className={`font-label-caps text-[11px] font-bold tracking-wider uppercase ${
                      isSevere ? 'text-error' : isWarning ? 'text-amber-700' : isInfo ? 'text-emerald-700' : 'text-tertiary'
                    }`}>
                      {adv.severityLabel || 'Advisory'}
                    </span>
                  </div>
                  <span className="text-[11px] text-on-surface-variant font-medium">{adv.timing}</span>
                </div>

                <div>
                  <h3 className="font-headline-md text-base text-on-surface font-semibold group-hover:text-primary transition-colors">
                    {adv.title}
                  </h3>
                  <p className="font-body-md text-xs text-on-surface-variant mt-1 leading-relaxed">
                    {adv.shortDesc}
                  </p>
                </div>

                {/* Recommended Action */}
                {adv.recommendedAction && (
                  <div className="bg-surface/70 rounded-xl p-3 border border-outline-variant/10 text-xs">
                    <span className="font-bold text-on-surface block mb-0.5">Recommended Action</span>
                    <p className="text-on-surface-variant leading-relaxed">{adv.recommendedAction}</p>
                  </div>
                )}

                <div className="flex justify-end pt-1">
                  <span className="text-xs text-primary font-medium group-hover:underline flex items-center gap-1">
                    View diagnostic details <span className="material-symbols-outlined text-sm">arrow_forward</span>
                  </span>
                </div>
              </article>
            );
          })}
        </div>
      </aside>
    </main>
  );
}

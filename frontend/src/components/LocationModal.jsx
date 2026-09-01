import React from 'react';
import { useWeather } from '../context/WeatherContext';
import { resolveWeatherVisual } from '../utils/weatherVisuals';

export default function LocationModal() {
  const {
    isLocationOpen,
    setIsLocationOpen,
    currentCity,
    switchCity,
    savedCities,
    toggleSavedCity,
    formatTemp,
    setIsSearchOpen,
    detectCurrentLocation,
    isDetectingLocation
  } = useWeather();

  if (!isLocationOpen) return null;

  return (
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div class="bg-surface rounded-2xl border border-outline-variant/20 shadow-2xl max-w-lg w-full overflow-hidden">
        {/* Header */}
        <div class="flex items-center justify-between px-6 py-4 border-b border-outline-variant/15">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">location_on</span>
            <h3 class="font-headline-md text-lg text-on-surface">Location Selector</h3>
          </div>
          <button
            onClick={() => setIsLocationOpen(false)}
            class="p-1 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* Content */}
        <div class="p-6 space-y-6 max-h-[70vh] overflow-y-auto no-scrollbar">
          {/* GPS Auto-Detect Button */}
          <button
            onClick={detectCurrentLocation}
            disabled={isDetectingLocation}
            class="w-full flex items-center justify-center gap-2.5 p-3.5 rounded-xl bg-primary/10 hover:bg-primary/20 text-primary border border-primary/25 font-semibold text-sm transition-all active:scale-98 cursor-pointer disabled:opacity-50"
          >
            <span class={`material-symbols-outlined text-lg ${isDetectingLocation ? 'animate-spin' : ''}`}>
              {isDetectingLocation ? 'sync' : 'my_location'}
            </span>
            <span>{isDetectingLocation ? 'Detecting GPS Coordinates...' : 'Use My Current Location (GPS)'}</span>
          </button>

          {/* Active location summary */}
          <div>
            <span class="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider block mb-2 font-mono">Current Active Location</span>
            <div class="bg-secondary-container/30 border border-primary/20 rounded-xl p-4 flex items-center justify-between">
              <div>
                <h4 class="font-headline-md text-lg text-primary font-semibold">{currentCity.name}{currentCity.country ? `, ${currentCity.country}` : ''}</h4>
                <p class="text-xs text-on-surface-variant">{currentCity.condition} · Humidity {currentCity.humidity}% · Wind {currentCity.windKm} km/h</p>
              </div>
              <span class="text-3xl font-light text-on-surface font-mono">
                {formatTemp(currentCity.tempC, currentCity.tempF)}
              </span>
            </div>
          </div>

          {/* Saved Favorites */}
          <div>
            <div class="flex items-center justify-between mb-3">
              <span class="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-mono">Saved Locations</span>
              <button
                onClick={() => {
                  setIsLocationOpen(false);
                  setIsSearchOpen(true);
                }}
                class="text-xs text-primary hover:underline font-medium flex items-center gap-1 cursor-pointer"
              >
                <span class="material-symbols-outlined text-sm">search</span> Search New City
              </button>
            </div>

            <div class="space-y-2">
              {savedCities.map(city => {
                const isSelected = city.id === currentCity.id || (city.lat === currentCity.lat && city.lon === currentCity.lon);
                const visual = resolveWeatherVisual(city.condition || 'Partly Cloudy');

                return (
                  <div
                    key={city.id || `${city.lat}-${city.lon}`}
                    class={`flex items-center justify-between p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-primary/5 border-primary/40 shadow-xs'
                        : 'bg-surface border-outline-variant/15 hover:border-outline-variant/30'
                    }`}
                    onClick={() => {
                      switchCity(city);
                      setIsLocationOpen(false);
                    }}
                  >
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 rounded-lg bg-primary/10 border border-primary/15 flex items-center justify-center text-primary flex-shrink-0">
                        <span class="material-symbols-outlined text-base">location_on</span>
                      </div>
                      <div>
                        <h5 class="font-body-md text-sm font-medium text-on-surface">{city.name}</h5>
                        <p class="text-xs text-on-surface-variant">{city.region ? `${city.region}, ` : ''}{city.country}</p>
                      </div>
                    </div>

                    <div class="flex items-center gap-3">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleSavedCity(city);
                        }}
                        class="text-amber-500 hover:opacity-80 p-1 cursor-pointer"
                        title="Toggle bookmark"
                      >
                        <span class="material-symbols-outlined text-lg" style={{ fontVariationSettings: "'FILL' 1" }}>
                          bookmark
                        </span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { useWeather } from '../context/WeatherContext';
import { searchLocations } from '../services/weatherApi';
import { DEFAULT_CITIES } from '../constants/appConfig';
import { resolveWeatherVisual } from '../utils/weatherVisuals';

export default function SearchModal() {
  const {
    isSearchOpen,
    setIsSearchOpen,
    switchCity,
    savedCities,
    toggleSavedCity,
    detectCurrentLocation,
    isDetectingLocation
  } = useWeather();

  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const debounceRef = useRef(null);

  // Debounced search query against Open-Meteo Geocoding API
  useEffect(() => {
    if (!query || query.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    if (debounceRef.current) clearTimeout(debounceRef.current);

    debounceRef.current = setTimeout(async () => {
      try {
        const results = await searchLocations(query.trim());
        setSearchResults(results);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setIsSearching(false);
      }
    }, 350);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  if (!isSearchOpen) return null;

  const handleSelect = (cityObj) => {
    switchCity(cityObj);
    setIsSearchOpen(false);
    setQuery('');
  };

  const displayList = query.trim().length >= 2 ? searchResults : DEFAULT_CITIES;

  return (
    <div class="fixed inset-0 z-50 flex items-start justify-center pt-16 px-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div class="bg-surface rounded-2xl border border-outline-variant/20 shadow-2xl max-w-xl w-full overflow-hidden">
        {/* Search Header Input */}
        <div class="flex items-center px-6 py-4 border-b border-outline-variant/15 gap-3">
          <span class={`material-symbols-outlined text-primary text-xl ${isSearching ? 'animate-spin' : ''}`}>
            {isSearching ? 'sync' : 'search'}
          </span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search any global city, region, or country (e.g. Mumbai, Berlin, Tokyo)..."
            class="w-full bg-transparent border-none text-on-surface font-body-md placeholder:text-on-surface-variant/50 focus:outline-none focus:ring-0 text-base"
            autoFocus
          />
          {query && (
            <button 
              onClick={() => setQuery('')}
              class="text-on-surface-variant hover:text-on-surface text-sm font-medium cursor-pointer"
            >
              Clear
            </button>
          )}
          <button
            onClick={() => setIsSearchOpen(false)}
            class="p-1 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors cursor-pointer"
          >
            <span class="material-symbols-outlined text-lg">close</span>
          </button>
        </div>

        {/* GPS Location Button */}
        <div class="p-3 bg-secondary-container/20 border-b border-outline-variant/10">
          <button
            onClick={detectCurrentLocation}
            disabled={isDetectingLocation}
            class="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-surface hover:bg-primary/10 text-on-surface hover:text-primary border border-outline-variant/15 text-xs font-semibold transition-all cursor-pointer disabled:opacity-50"
          >
            <div class="flex items-center gap-2">
              <span class={`material-symbols-outlined text-primary text-base ${isDetectingLocation ? 'animate-spin' : ''}`}>
                {isDetectingLocation ? 'sync' : 'my_location'}
              </span>
              <span>{isDetectingLocation ? 'Detecting your GPS location...' : 'Use My Current Location (GPS Auto-Detect)'}</span>
            </div>
            <span class="text-[10px] text-primary font-bold uppercase font-label-caps">Auto-Detect</span>
          </button>
        </div>

        {/* Results List */}
        <div class="max-h-96 overflow-y-auto p-4 space-y-2 no-scrollbar">
          {query.trim().length < 2 && (
            <div class="px-2 pb-1 text-[11px] font-label-caps uppercase text-on-surface-variant/70 font-semibold">
              Popular Global Cities
            </div>
          )}

          {query.trim().length >= 2 && !isSearching && searchResults.length === 0 ? (
            <div class="text-center py-8 text-on-surface-variant">
              <span class="material-symbols-outlined text-3xl mb-2 text-primary">travel_explore</span>
              <p>No locations found matching "{query}"</p>
              <p class="text-xs text-on-surface-variant/70 mt-1">Try searching another spelling or major city name</p>
            </div>
          ) : (
            displayList.map(city => {
              const isSaved = savedCities.some(c => c.id === city.id || (c.lat === city.lat && c.lon === city.lon));
              const visual = resolveWeatherVisual(city.condition || 'Sunny & Clear');

              return (
                <div
                  key={city.id || `${city.lat}-${city.lon}`}
                  onClick={() => handleSelect(city)}
                  class="flex items-center justify-between p-3.5 rounded-xl hover:bg-surface-container-low transition-colors cursor-pointer group"
                >
                  <div class="flex-1 flex items-center gap-3">
                    <div class="w-9 h-9 rounded-xl bg-primary/10 border border-primary/15 flex items-center justify-center text-primary flex-shrink-0">
                      <span class="material-symbols-outlined text-lg">location_city</span>
                    </div>
                    <div>
                      <h4 class="font-headline-md text-base font-medium text-on-surface group-hover:text-primary transition-colors">
                        {city.name}{city.country ? `, ${city.country}` : ''}
                      </h4>
                      <p class="text-xs text-on-surface-variant">
                        {city.region ? `${city.region} · ` : ''}Lat: {city.lat.toFixed(2)}°, Lon: {city.lon.toFixed(2)}°
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleSavedCity(city);
                    }}
                    class={`p-2 rounded-full transition-colors cursor-pointer ${
                      isSaved ? 'text-amber-500' : 'text-on-surface-variant/40 hover:text-amber-500'
                    }`}
                    title={isSaved ? 'Remove from favorites' : 'Save to favorites'}
                  >
                    <span class="material-symbols-outlined text-lg" style={{ fontVariationSettings: isSaved ? "'FILL' 1" : "'FILL' 0" }}>
                      bookmark
                    </span>
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { useWeather } from '../context/WeatherContext';
import { resolveWeatherVisual } from '../utils/weatherVisuals';
import { POPULAR_CITIES } from '../constants/appConfig';
import { searchLocations } from '../services/weatherApi';

export default function LocationModal() {
  const {
    isLocationOpen,
    setIsLocationOpen,
    currentCity,
    switchCity,
    savedCities,
    toggleSavedCity,
    formatTemp,
    detectCurrentLocation,
    isDetectingLocation,
    t,
    translateCondition
  } = useWeather();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const debounceTimerRef = useRef(null);

  // Debounced search on user input
  useEffect(() => {
    if (!searchQuery || searchQuery.trim().length < 2) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);

    debounceTimerRef.current = setTimeout(async () => {
      try {
        const results = await searchLocations(searchQuery.trim());
        setSearchResults(results);
      } catch (err) {
        console.error('Location search failed:', err);
      } finally {
        setIsSearching(false);
      }
    }, 350);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [searchQuery]);

  if (!isLocationOpen) return null;

  const handleSelectCity = (cityObj) => {
    switchCity(cityObj);
    setIsLocationOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-outline-variant/20 shadow-2xl max-w-xl w-full overflow-hidden transition-all">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-outline-variant/15 bg-surface-container-low/50">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary">
              <span className="material-symbols-outlined text-xl">location_on</span>
            </div>
            <div>
              <h3 className="font-headline-md text-lg text-on-surface font-bold">{t('chooseYourLocation')}</h3>
              <p className="text-xs text-on-surface-variant/80">{t('locationModalSubtitle')}</p>
            </div>
          </div>
          <button
            onClick={() => setIsLocationOpen(false)}
            className="p-1.5 rounded-full text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-colors cursor-pointer"
            aria-label="Close"
          >
            <span className="material-symbols-outlined text-xl">close</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto no-scrollbar">
          {/* GPS Auto-Detect Button */}
          <button
            onClick={detectCurrentLocation}
            disabled={isDetectingLocation}
            className="w-full flex items-center justify-between p-4 rounded-2xl bg-gradient-to-r from-primary/15 via-primary/10 to-transparent hover:from-primary/25 hover:via-primary/15 border border-primary/30 text-on-surface transition-all active:scale-98 cursor-pointer disabled:opacity-60 shadow-sm hover:shadow group"
          >
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-xl bg-primary text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
                <span className={`material-symbols-outlined text-xl ${isDetectingLocation ? 'animate-spin' : ''}`}>
                  {isDetectingLocation ? 'sync' : 'my_location'}
                </span>
              </div>
              <div className="text-left">
                <span className="block font-headline-md text-sm font-bold text-primary">
                  {isDetectingLocation ? t('detectingGps') : t('useCurrentLocationGps')}
                </span>
                <span className="block text-xs text-on-surface-variant/75">
                  {t('autoDetectDesc')}
                </span>
              </div>
            </div>
            <span className="material-symbols-outlined text-primary text-xl group-hover:translate-x-1 transition-transform">
              arrow_forward
            </span>
          </button>

          {/* Search Input */}
          <div className="relative">
            <div className="flex items-center px-4 py-3 rounded-2xl bg-surface-container-low border border-outline-variant/20 focus-within:border-primary/50 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
              <span className={`material-symbols-outlined text-on-surface-variant/70 text-lg mr-2.5 ${isSearching ? 'animate-spin' : ''}`}>
                {isSearching ? 'sync' : 'search'}
              </span>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={t('searchAnyCityPlaceholder')}
                className="w-full bg-transparent border-none text-on-surface text-sm placeholder:text-on-surface-variant/50 focus:outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="text-xs text-on-surface-variant hover:text-on-surface font-medium px-2 py-1 cursor-pointer"
                >
                  {t('clearSearch')}
                </button>
              )}
            </div>

            {/* Live Search Results */}
            {searchQuery.trim().length >= 2 && (
              <div className="mt-2 space-y-1.5 border border-outline-variant/15 rounded-2xl p-2 bg-surface shadow-lg max-h-52 overflow-y-auto">
                {isSearching && searchResults.length === 0 ? (
                  <div className="p-4 text-center text-xs text-on-surface-variant/70">Searching global satellites...</div>
                ) : searchResults.length > 0 ? (
                  searchResults.map((city) => (
                    <div
                      key={city.id}
                      onClick={() => handleSelectCity(city)}
                      className="flex items-center justify-between p-3 rounded-xl hover:bg-primary/10 border border-transparent hover:border-primary/20 transition-all cursor-pointer group"
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="material-symbols-outlined text-primary text-lg">location_city</span>
                        <div>
                          <p className="text-sm font-semibold text-on-surface group-hover:text-primary">{city.name}</p>
                          <p className="text-xs text-on-surface-variant/70">{city.region ? `${city.region}, ` : ''}{city.country}</p>
                        </div>
                      </div>
                      <span className="text-xs font-mono text-on-surface-variant/60">{city.lat.toFixed(2)}°, {city.lon.toFixed(2)}°</span>
                    </div>
                  ))
                ) : (
                  <div className="p-4 text-center text-xs text-on-surface-variant/70">No matching locations found for "{searchQuery}"</div>
                )}
              </div>
            )}
          </div>

          {/* Popular Cities Grid */}
          <div>
            <span className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider block mb-2.5 font-semibold font-mono">
              {t('popularCities')}
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {POPULAR_CITIES.map((city) => {
                const isSelected = currentCity?.name === city.name;
                return (
                  <button
                    key={city.id}
                    onClick={() => handleSelectCity(city)}
                    className={`p-3 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                      isSelected
                        ? 'bg-primary/10 border-primary text-primary font-bold shadow-xs'
                        : 'bg-surface-container-lowest border-outline-variant/15 hover:border-primary/30 hover:bg-surface-container-low text-on-surface'
                    }`}
                  >
                    <span className="text-xs font-bold block truncate">{city.name}</span>
                    <span className="text-[10px] text-on-surface-variant/70 block truncate">{city.country}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Current Active Location Summary */}
          {currentCity?.name && currentCity.name !== 'Select Location' && (
            <div>
              <span className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider block mb-2 font-mono font-semibold">
                {t('currentlyActive')}
              </span>
              <div className="bg-secondary-container/30 border border-primary/20 rounded-2xl p-4 flex items-center justify-between">
                <div>
                  <h4 className="font-headline-md text-base text-primary font-bold">{currentCity.name}{currentCity.country ? `, ${currentCity.country}` : ''}</h4>
                  <p className="text-xs text-on-surface-variant">{translateCondition(currentCity.condition)} · {t('humidity')}: {currentCity.humidity ?? '--'}% · {t('windLabel')}: {currentCity.windKm ?? '--'} km/h</p>
                </div>
                <span className="text-2xl font-light text-on-surface font-mono">
                  {currentCity.tempC !== null && currentCity.tempC !== undefined ? formatTemp(currentCity.tempC, currentCity.tempF) : '--'}
                </span>
              </div>
            </div>
          )}

          {/* Saved Bookmarks */}
          {savedCities && savedCities.length > 0 && (
            <div>
              <span className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider block mb-2 font-mono font-semibold">
                {t('savedFavorites')}
              </span>
              <div className="space-y-1.5">
                {savedCities.slice(0, 5).map((city) => (
                  <div
                    key={city.id || `${city.lat}-${city.lon}`}
                    onClick={() => handleSelectCity(city)}
                    className="flex items-center justify-between p-2.5 rounded-xl bg-surface border border-outline-variant/15 hover:border-primary/30 transition-all cursor-pointer group"
                  >
                    <div className="flex items-center gap-2.5">
                      <span className="material-symbols-outlined text-amber-500 text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
                        star
                      </span>
                      <span className="text-xs font-medium text-on-surface group-hover:text-primary">{city.name}</span>
                      <span className="text-[10px] text-on-surface-variant/60">{city.country}</span>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleSavedCity(city);
                      }}
                      className="text-on-surface-variant/50 hover:text-amber-500 p-1"
                      title="Toggle bookmark"
                    >
                      <span className="material-symbols-outlined text-base">close</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

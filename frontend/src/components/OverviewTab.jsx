import React, { useState, useEffect } from 'react';
import { useWeather } from '../context/WeatherContext';
import WeatherMetrics from './WeatherMetrics';
import HourlyForecast from './HourlyForecast';
import SolarCycle from './SolarCycle';
import WeatherAtmosphere from './WeatherAtmosphere';
import { resolveWeatherVisual } from '../utils/weatherVisuals';
import { getLocalizedInsight, getLocalizedAlert, getLocalizedDayAtAGlanceItem } from '../utils/translations';

export default function OverviewTab() {
  const {
    currentCity,
    formatTemp,
    openAlertModal,
    setActiveTab,
    sendChatMessage,
    unit,
    showToast,
    isSkeletonLoading,
    refreshWeather,
    detectCurrentLocation,
    isDetectingLocation,
    setIsLocationOpen,
    currentLanguage,
    t,
    translateCondition
  } = useWeather();

  const [insightText, setInsightText] = useState(currentCity?.aiInsight || '');
  const [isRefreshingInsight, setIsRefreshingInsight] = useState(false);
  const [isHeroHovered, setIsHeroHovered] = useState(false);

  useEffect(() => {
    if (currentCity?.aiInsight) {
      setInsightText(currentCity.aiInsight);
    }
  }, [currentCity?.aiInsight]);

  const isLive = Boolean(currentCity?.isLiveLoaded && currentCity?.tempC !== null);

  // Determine effective weather condition and visual settings
  const rawCondition = isLive ? (currentCity?.condition || 'Clear Sky') : 'Awaiting Location';
  const displayCondition = translateCondition(rawCondition);
  const activeVisual = resolveWeatherVisual(rawCondition);
  
  const displayTempC = currentCity?.tempC;
  const displayTempF = currentCity?.tempF;

  const refreshInsight = () => {
    setIsRefreshingInsight(true);
    refreshWeather();
    setTimeout(() => {
      setIsRefreshingInsight(false);
    }, 600);
  };

  return (
    <main className="max-w-7xl mx-auto px-gutter md:px-container-padding-desktop pb-section-gap space-y-8">
      {/* Showpiece Hero Section with Dynamic Weather Visual */}
      <section 
        onMouseEnter={() => setIsHeroHovered(true)}
        onMouseLeave={() => setIsHeroHovered(false)}
        className="mt-6 md:mt-8 relative rounded-3xl overflow-hidden min-h-[52vh] flex flex-col justify-end p-6 sm:p-8 md:p-12 shadow-md group border border-outline-variant/20 transition-all cursor-default"
      >
        {/* Dynamic Atmospheric Visual / Placeholder */}
        <WeatherAtmosphere 
          condition={rawCondition} 
          isHovered={isHeroHovered}
          customVisual={activeVisual}
        />

        {/* Hero Main Content */}
        <div className="relative z-10 text-white space-y-3 pt-8">
          <div className="flex items-center gap-2 text-white/85 text-xs font-medium tracking-wide">
            <span className="material-symbols-outlined text-sm">schedule</span>
            <span>{currentCity?.region ? `${currentCity.region}, ` : ''}{currentCity?.country || ''}</span>
            <span className="text-white/40">·</span>
            <span className="text-sky-300 font-medium">{isLive ? activeVisual.tagline : t('gpsRequired')}</span>
          </div>

          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="font-tight font-medium text-headline-lg-mobile md:text-headline-lg text-white tracking-tight drop-shadow-sm">
                {isLive ? `${t('goodDay')}, ${currentCity?.name}.` : `${t('goodDay')}, ${t('atmosphericIntelligence')}.`}
              </h1>
              
              <div className="flex items-baseline gap-4 mt-2">
                <span className="font-tight text-[84px] md:text-[96px] leading-none tracking-tighter text-white font-light drop-shadow-md">
                  {isLive && displayTempC !== null ? formatTemp(displayTempC, displayTempF) : '--°'}
                </span>
                
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="material-symbols-outlined text-2xl text-sky-300">
                      {isLive ? (activeVisual.icon || 'wb_sunny') : 'location_searching'}
                    </span>
                    <span className="font-tight text-2xl md:text-3xl text-white font-medium block drop-shadow-sm">
                      {displayCondition}
                    </span>
                  </div>
                  
                  <span className="text-xs text-white/85 font-normal block drop-shadow-sm">
                    {isLive ? (
                      `${t('feelsLike')} ${formatTemp(currentCity?.feelsLikeC ?? displayTempC, currentCity?.feelsLikeF ?? displayTempF)} · ${t('uvLabel')} ${currentCity?.uvIndex ?? '--'} (${currentCity?.uvLabel || 'Mod'}) · ${t('humidityLabel')} ${currentCity?.humidity ?? '--'}% · ${t('windLabel')} ${currentCity?.windKm ?? '--'} km/h`
                    ) : (
                      t('awaitingLocationHeroDesc')
                    )}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {!isLive && (
                <button
                  onClick={() => setIsLocationOpen(true)}
                  className="flex items-center gap-2 px-6 py-3 rounded-full bg-primary text-white hover:bg-primary/90 font-label-caps text-xs tracking-wider transition-all shadow-md active:scale-95 font-bold cursor-pointer hover:shadow-lg"
                >
                  <span className="material-symbols-outlined text-base">my_location</span>
                  {t('chooseLocationGpsBtn')}
                </button>
              )}

              <button
                onClick={() => setActiveTab('assistant')}
                className="flex items-center gap-2 px-6 py-3 rounded-full bg-surface text-on-surface hover:bg-surface-container font-label-caps text-xs tracking-wider transition-all shadow-md active:scale-95 font-bold cursor-pointer hover:shadow-lg border border-outline-variant/30"
              >
                <span className="material-symbols-outlined text-primary text-base">auto_awesome</span>
                <span>{t('askWeatherGpt')}</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Severe Alert Banner */}
      {currentCity?.alert && (() => {
        const localizedAlert = getLocalizedAlert(currentCity.alert, currentLanguage?.code);
        return (
          <div 
            onClick={() => openAlertModal(currentCity.alert)}
            className="bg-tertiary-fixed border border-tertiary-fixed-dim/30 rounded-2xl p-6 flex items-start justify-between gap-4 cursor-pointer hover:border-tertiary-fixed-dim/60 transition-all group shadow-sm"
          >
            <div className="flex items-start gap-4">
              <span className="material-symbols-outlined text-tertiary text-2xl mt-0.5" style={{ fontVariationSettings: "'FILL' 1" }}>
                {localizedAlert.icon || 'warning'}
              </span>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="px-2 py-0.5 rounded-md bg-tertiary/10 text-tertiary text-[10px] font-bold uppercase tracking-wider font-label-caps">
                    {localizedAlert.severityLabel || t('severeWarning')}
                  </span>
                  <span className="text-xs text-on-tertiary-fixed-variant/75 font-medium">{localizedAlert.timing}</span>
                </div>
                <h3 className="font-tight text-lg text-on-tertiary-fixed-variant font-semibold group-hover:underline">
                  {localizedAlert.title}
                </h3>
                <p className="font-body-md text-xs text-on-tertiary-fixed-variant/80 mt-1">
                  {localizedAlert.shortDesc}
                </p>
              </div>
            </div>
            <span className="material-symbols-outlined text-tertiary group-hover:translate-x-1 transition-transform text-lg">
              arrow_forward
            </span>
          </div>
        );
      })()}

      {/* WeatherGPT Intelligence Summary Box */}
      <div className="bg-surface rounded-2xl border border-outline-variant/15 p-7 shadow-sm">
        <div className="flex items-center justify-between mb-3.5">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-primary text-base">auto_awesome</span>
            <span className="font-label-caps text-xs text-primary uppercase tracking-wider font-bold">{t('todaysOutlook')}</span>
          </div>
          <button 
            onClick={refreshInsight}
            className="text-on-surface-variant/70 hover:text-primary transition-colors p-1.5 rounded-full hover:bg-surface-container cursor-pointer"
            title="Refresh Insight"
          >
            <span className={`material-symbols-outlined text-base ${isRefreshingInsight ? 'animate-spin' : ''}`}>
              refresh
            </span>
          </button>
        </div>
        <p className="font-body-lg text-base text-on-surface leading-relaxed font-normal">
          {getLocalizedInsight(currentCity, currentLanguage?.code) || t('liveTelemetryProjected')}
        </p>
      </div>

      {/* Personalization: Your Day at a Glance */}
      {currentCity?.dayAtAGlance && currentCity.dayAtAGlance.length > 0 && (
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-label-caps text-xs text-on-surface-variant uppercase tracking-wider font-semibold">
              {t('yourDayAtAGlance')} · {currentCity.name}
            </h2>
            <span className="text-[11px] text-on-surface-variant/75 font-medium">{t('personalizedForActivity')}</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {currentCity.dayAtAGlance.map(rawItem => {
              const item = getLocalizedDayAtAGlanceItem(rawItem, currentCity, currentLanguage?.code);
              return (
                <div 
                  key={item.id}
                  onClick={() => {
                    sendChatMessage(`Give me a detailed breakdown for ${item.category} in ${currentCity.name}`);
                    setActiveTab('assistant');
                  }}
                  className="bg-surface border border-outline-variant/15 rounded-xl p-5 hover:border-primary/30 transition-all cursor-pointer group shadow-sm flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-9 h-9 rounded-full bg-secondary-container/50 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                      <span className="material-symbols-outlined text-lg">{item.icon}</span>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold ${item.badgeColor}`}>
                      {item.status}
                    </span>
                  </div>
                  <div>
                    <h4 className="font-tight text-sm font-semibold text-on-surface group-hover:text-primary transition-colors">
                      {item.category}
                    </h4>
                    <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                      {item.text}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Main Grid: Visual Gauges + Hourly Timeline + Solar Cycle */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-7 space-y-8">
          <HourlyForecast />
          {/* Dedicated Sunrise & Sunset Solar Cycle Section */}
          <SolarCycle />
        </div>
        <div className="lg:col-span-5 space-y-8">
          <WeatherMetrics />
        </div>
      </div>
    </main>
  );
}

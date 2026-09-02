import React from 'react';
import { useWeather } from '../context/WeatherContext';
import { useAuth } from '../context/AuthContext';

export default function Header() {
  const {
    currentCity,
    activeTab,
    setActiveTab,
    setIsSearchOpen,
    setIsLocationOpen,
    setIsSettingsOpen,
    setIsLanguageOpen,
    unit,
    toggleUnit,
    theme,
    toggleTheme,
    showToast,
    t
  } = useWeather();

  const {
    user,
    isGuest,
    openAuthModal,
    logout,
    setIsHistoryDrawerOpen
  } = useAuth();

  return (
    <header className="w-full top-0 sticky z-50 bg-background/90 dark:bg-background/90 backdrop-blur-md border-b border-outline-variant/15 transition-all">
      <div className="flex justify-between items-center px-gutter py-3.5 max-w-7xl mx-auto">
        {/* Brand Logo & Nav */}
        <div className="flex items-center gap-8">
          <button 
            onClick={() => setActiveTab('overview')}
            className="font-headline-md text-xl font-bold tracking-tight text-on-surface dark:text-surface-bright text-left cursor-pointer hover:opacity-85 transition-opacity flex items-center gap-2"
          >
            <span className="text-primary font-mono">⚡</span>
            <span>{t('appName')}</span>
          </button>

          <nav className="hidden md:flex gap-6 items-center">
            <button
              onClick={() => setActiveTab('overview')}
              className={`text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === 'overview'
                  ? 'text-primary font-bold border-b-2 border-primary pb-0.5'
                  : 'text-on-surface-variant/80 hover:text-primary'
              }`}
            >
              {t('tabOverview')}
            </button>
            <button
              onClick={() => setActiveTab('forecast')}
              className={`text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === 'forecast'
                  ? 'text-primary font-bold border-b-2 border-primary pb-0.5'
                  : 'text-on-surface-variant/80 hover:text-primary'
              }`}
            >
              {t('tabForecast')}
            </button>
            <button
              onClick={() => setActiveTab('map')}
              className={`text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === 'map'
                  ? 'text-primary font-bold border-b-2 border-primary pb-0.5'
                  : 'text-on-surface-variant/80 hover:text-primary'
              }`}
            >
              {t('tabMap')}
            </button>
            <button
              onClick={() => setActiveTab('assistant')}
              className={`text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === 'assistant'
                  ? 'text-primary font-bold border-b-2 border-primary pb-0.5'
                  : 'text-on-surface-variant/80 hover:text-primary'
              }`}
            >
              {t('tabAssistant')}
            </button>
          </nav>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Quick Search trigger */}
          <button 
            onClick={() => setIsSearchOpen(true)}
            className="hidden sm:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-surface border border-outline-variant/15 text-on-surface-variant/80 hover:border-primary/40 transition-all text-xs shadow-sm hover:shadow cursor-pointer"
            title={t('searchCityPlaceholder')}
          >
            <span className="material-symbols-outlined text-sm">search</span>
            <span>{t('searchCityPlaceholder')}</span>
          </button>

          {/* Location badge */}
          <button
            onClick={() => setIsLocationOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-secondary-container/40 border border-outline-variant/15 hover:border-primary/30 transition-all cursor-pointer text-on-surface shadow-sm active:scale-95"
            aria-label="Select Location"
          >
            <span className="material-symbols-outlined text-primary text-sm">location_on</span>
            <span className="font-label-caps text-[11px] uppercase tracking-wider font-semibold">{currentCity?.name || t('selectLocation')}</span>
          </button>

          {/* Unit Toggle */}
          <button
            onClick={toggleUnit}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-surface border border-outline-variant/15 font-bold text-xs text-primary hover:bg-surface-container transition-all cursor-pointer active:scale-95 shadow-sm"
            title={`Switch to °${unit === 'C' ? 'F' : 'C'}`}
          >
            °{unit}
          </button>

          {/* Night / Light Mode Toggle */}
          <button
            onClick={() => {
              toggleTheme();
              showToast(theme === 'dark' ? 'Light Mode Enabled' : 'Night Mode Enabled');
            }}
            className="flex items-center justify-center w-8 h-8 rounded-full bg-surface border border-outline-variant/15 text-on-surface-variant hover:text-primary hover:bg-surface-container transition-all cursor-pointer active:scale-95 shadow-sm"
            title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Night Mode'}
            aria-label="Toggle Night Mode"
          >
            <span className="material-symbols-outlined text-lg">
              {theme === 'dark' ? 'light_mode' : 'dark_mode'}
            </span>
          </button>

          {/* Language Selector */}
          <button
            onClick={() => setIsLanguageOpen(true)}
            className="text-on-surface-variant/80 hover:text-primary transition-colors duration-200 cursor-pointer p-1.5 rounded-full hover:bg-surface-container active:scale-95"
            aria-label="Language options"
            title={t('languageSelectorTitle')}
          >
            <span className="material-symbols-outlined text-xl">language</span>
          </button>

          {/* Settings */}
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="text-on-surface-variant/80 hover:text-primary transition-colors duration-200 cursor-pointer p-1.5 rounded-full hover:bg-surface-container active:scale-95"
            aria-label="Settings"
            title={t('settingsTitle')}
          >
            <span className="material-symbols-outlined text-xl">settings</span>
          </button>

          {/* Title Bar Auth Controls */}
          {user ? (
            <div className="flex items-center gap-1.5 pl-2 border-l border-outline-variant/20">
              {/* History Button */}
              <button
                onClick={() => setIsHistoryDrawerOpen(true)}
                className="flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary hover:bg-primary/20 transition-all text-xs font-semibold shadow-sm cursor-pointer"
                title={t('history')}
              >
                <span className="material-symbols-outlined text-sm">history</span>
                <span className="hidden sm:inline">{t('history')}</span>
              </button>

              {/* User Avatar pill */}
              <div 
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-container border border-outline-variant/15 text-xs text-on-surface"
                title={`Signed in as ${user.email}`}
              >
                <span className="w-5 h-5 rounded-full bg-primary text-on-primary flex items-center justify-center font-bold text-[10px]">
                  {(user.name || user.email || 'U')[0].toUpperCase()}
                </span>
                <span className="hidden md:inline font-medium max-w-[100px] truncate">
                  {user.name || user.email.split('@')[0]}
                </span>
              </div>

              {/* Logout Button */}
              <button
                onClick={() => {
                  logout();
                  showToast(t('signOut'));
                }}
                className="text-on-surface-variant/70 hover:text-error transition-colors p-1.5 rounded-full hover:bg-surface-container cursor-pointer"
                title={t('signOut')}
              >
                <span className="material-symbols-outlined text-lg">logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 pl-2 border-l border-outline-variant/20">
              <button
                onClick={() => openAuthModal('choice')}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-primary text-on-primary hover:bg-primary/90 transition-all text-xs font-semibold shadow-sm cursor-pointer active:scale-95"
                title="Sign in or create account"
              >
                <span className="material-symbols-outlined text-sm">account_circle</span>
                <span>{t('signInLogin')}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

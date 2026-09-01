import React from 'react';
import { WeatherProvider, useWeather } from './context/WeatherContext';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import MobileNav from './components/MobileNav';
import NotificationToast from './components/NotificationToast';
import OverviewTab from './components/OverviewTab';
import ForecastAnalyticsTab from './components/ForecastAnalyticsTab';
import MapAlertCenterTab from './components/MapAlertCenterTab';
import AssistantTab from './components/AssistantTab';

import SearchModal from './components/SearchModal';
import LocationModal from './components/LocationModal';
import SettingsModal from './components/SettingsModal';
import LanguageModal from './components/LanguageModal';
import AlertDetailModal from './components/AlertDetailModal';
import VoiceModal from './components/VoiceModal';
import AuthModal from './components/AuthModal';
import AssistantHistoryDrawer from './components/AssistantHistoryDrawer';

function MainLayout() {
  const { activeTab } = useWeather();

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        <Header />
        
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'forecast' && <ForecastAnalyticsTab />}
        {activeTab === 'map' && <MapAlertCenterTab />}
        {activeTab === 'assistant' && <AssistantTab />}
      </div>

      <MobileNav />
      <NotificationToast />

      {/* Global Modals & Drawers */}
      <SearchModal />
      <LocationModal />
      <SettingsModal />
      <LanguageModal />
      <AlertDetailModal />
      <VoiceModal />
      <AuthModal />
      <AssistantHistoryDrawer />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <WeatherProvider>
        <MainLayout />
      </WeatherProvider>
    </AuthProvider>
  );
}


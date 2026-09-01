import React from 'react';
import { useWeather } from '../context/WeatherContext';

export default function NotificationToast() {
  const { toastMessage } = useWeather();

  if (!toastMessage) return null;

  return (
    <div class="fixed top-20 right-6 z-50 animate-bounce transition-all">
      <div class="bg-inverse-surface text-inverse-on-surface px-5 py-3 rounded-xl shadow-xl border border-outline/20 flex items-center gap-3">
        <span class="material-symbols-outlined text-primary-fixed text-sm">info</span>
        <span class="font-body-md text-sm font-medium">{toastMessage}</span>
      </div>
    </div>
  );
}

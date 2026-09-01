// Application constants, language localizations, and map layer configurations

export const LANGUAGES = [
  { code: 'en', name: 'English (US)', flag: '🇺🇸' },
  { code: 'hi', name: 'हिन्दी (Hindi)', flag: '🇮🇳' },
  { code: 'es', name: 'Español (Spanish)', flag: '🇪🇸' },
  { code: 'fr', name: 'Français (French)', flag: '🇫🇷' },
  { code: 'ja', name: '日本語 (Japanese)', flag: '🇯🇵' },
  { code: 'de', name: 'Deutsch (German)', flag: '🇩🇪' }
];

export const MAP_LAYERS = [
  { id: 'rain', name: 'Rainfall Radar', icon: 'water_drop', color: '#2a6088' },
  { id: 'temperature', name: 'Temperature Thermal', icon: 'thermostat', color: '#e07a5f' },
  { id: 'wind', name: 'Wind Velocity Stream', icon: 'air', color: '#3d405b' },
  { id: 'clouds', name: 'Cloud Coverage Satellite', icon: 'cloud', color: '#81b29a' }
];

export const DEFAULT_CITIES = [
  { id: 'ranchi', name: 'Ranchi', region: 'Jharkhand', country: 'India', lat: 23.3441, lon: 85.3096 },
  { id: 'new-delhi', name: 'New Delhi', region: 'Delhi', country: 'India', lat: 28.6139, lon: 77.2090 },
  { id: 'london', name: 'London', region: 'Greater London', country: 'United Kingdom', lat: 51.5074, lon: -0.1278 },
  { id: 'tokyo', name: 'Tokyo', region: 'Kanto', country: 'Japan', lat: 35.6762, lon: 139.6503 },
  { id: 'new-york', name: 'New York', region: 'New York', country: 'United States', lat: 40.7128, lon: -74.0060 },
  { id: 'paris', name: 'Paris', region: 'Île-de-France', country: 'France', lat: 48.8566, lon: 2.3522 },
  { id: 'reykjavik', name: 'Reykjavik', region: 'Capital Region', country: 'Iceland', lat: 64.1466, lon: -21.9426 },
  { id: 'sydney', name: 'Sydney', region: 'New South Wales', country: 'Australia', lat: -33.8688, lon: 151.2093 }
];

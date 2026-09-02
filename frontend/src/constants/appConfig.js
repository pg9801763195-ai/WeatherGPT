// Application constants, language localizations, and map layer configurations

export const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'hi', name: 'हिन्दी (Hindi)', flag: '🇮🇳' }
];

export const MAP_LAYERS = [
  { id: 'rain', name: 'Rainfall Radar', icon: 'water_drop', color: '#2a6088' },
  { id: 'temperature', name: 'Temperature Thermal', icon: 'thermostat', color: '#e07a5f' },
  { id: 'wind', name: 'Wind Velocity Stream', icon: 'air', color: '#3d405b' },
  { id: 'clouds', name: 'Cloud Coverage Satellite', icon: 'cloud', color: '#81b29a' }
];

export const POPULAR_CITIES = [
  { id: 'new-delhi', name: 'New Delhi', region: 'Delhi', country: 'India', lat: 28.6139, lon: 77.2090 },
  { id: 'mumbai', name: 'Mumbai', region: 'Maharashtra', country: 'India', lat: 19.0760, lon: 72.8777 },
  { id: 'bengaluru', name: 'Bengaluru', region: 'Karnataka', country: 'India', lat: 12.9716, lon: 77.5946 },
  { id: 'kolkata', name: 'Kolkata', region: 'West Bengal', country: 'India', lat: 22.5726, lon: 88.3639 },
  { id: 'london', name: 'London', region: 'Greater London', country: 'United Kingdom', lat: 51.5074, lon: -0.1278 },
  { id: 'new-york', name: 'New York', region: 'New York', country: 'United States', lat: 40.7128, lon: -74.0060 },
  { id: 'tokyo', name: 'Tokyo', region: 'Kanto', country: 'Japan', lat: 35.6762, lon: 139.6503 },
  { id: 'paris', name: 'Paris', region: 'Île-de-France', country: 'France', lat: 48.8566, lon: 2.3522 },
  { id: 'sydney', name: 'Sydney', region: 'New South Wales', country: 'Australia', lat: -33.8688, lon: 151.2093 }
];

export const DEFAULT_CITIES = POPULAR_CITIES;


// Weather Visual Themes & GIF Registry
// Custom GIF for Thunderstorm is configured from the local GIFs assets.
// For any other weather condition, simply assign your GIF path to the `gif` field.

export const WEATHER_VISUALS = {
  // Thunderstorm / Severe Storm
  thunderstorm: {
    id: 'thunderstorm',
    label: 'Thunderstorm',
    gif: '/gifs/thunderstorm.gif',
    gradient: 'from-slate-950 via-purple-950 to-slate-900',
    accentColor: '#c084fc',
    icon: 'thunderstorm',
    tagline: 'Convective atmospheric instability with active lightning'
  },

  // Rain / Drizzle
  rain: {
    id: 'rain',
    label: 'Rain & Drizzle',
    gif: '/gifs/rain.gif',
    gradient: 'from-slate-900 via-sky-950 to-slate-950',
    accentColor: '#60a5fa',
    icon: 'rainy',
    tagline: 'Continuous precipitation with active cloud cover'
  },

  // Sunny / Clear Sky
  sunny: {
    id: 'sunny',
    label: 'Sunny & Clear',
    gif: '/gifs/sunny.gif',
    gradient: 'from-sky-900 via-blue-950 to-slate-950',
    accentColor: '#fbbf24',
    icon: 'wb_sunny',
    tagline: 'High solar irradiance with unobstructed skies'
  },

  // Heavy Clouds / Overcast
  cloudy: {
    id: 'cloudy',
    label: 'Cloudy & Overcast',
    gif: '/gifs/cloudy.gif',
    gradient: 'from-slate-900 via-slate-800 to-slate-950',
    accentColor: '#94a3b8',
    icon: 'cloud',
    tagline: 'Stratocumulus cloud deck filtering solar illumination'
  },

  // Partly Cloudy
  partlyCloudy: {
    id: 'partly-cloudy',
    label: 'Partly Cloudy',
    gif: '/gifs/partly-cloudy.gif',
    gradient: 'from-slate-900 via-sky-950 to-slate-950',
    accentColor: '#38bdf8',
    icon: 'partly_cloudy_day',
    tagline: 'Scattered cumulus clouds with periodic sun intervals'
  },

  // Snow / Winter
  snow: {
    id: 'snow',
    label: 'Snow & Flurries',
    gif: '/gifs/snow.gif',
    gradient: 'from-slate-900 via-blue-950 to-slate-950',
    accentColor: '#e0f2fe',
    icon: 'ac_unit',
    tagline: 'Crystalline precipitation with sub-zero temperatures'
  },

  // Fog / Mist
  fog: {
    id: 'fog',
    label: 'Fog & Mist',
    gif: '/gifs/fog.gif',
    gradient: 'from-slate-900 via-stone-900 to-slate-950',
    accentColor: '#cbd5e1',
    icon: 'foggy',
    tagline: 'Low boundary layer cloud ceiling with reduced visibility'
  },

  // Clear Night
  night: {
    id: 'night',
    label: 'Clear Night',
    gif: '/gifs/night.gif',
    gradient: 'from-slate-950 via-indigo-950 to-slate-950',
    accentColor: '#818cf8',
    icon: 'nights_stay',
    tagline: 'Starlit nocturnal atmosphere with radiant cooling'
  }
};

/**
 * Resolves appropriate weather visual based on condition text
 */
export function resolveWeatherVisual(conditionStr = '', isNightOverride = false) {
  const text = (conditionStr || '').toLowerCase();

  if (text.includes('thunder') || text.includes('lightning') || text.includes('squall') || text.includes('storm')) {
    return WEATHER_VISUALS.thunderstorm;
  }

  if (isNightOverride || text.includes('night') || text.includes('moon') || text.includes('starlit')) {
    return WEATHER_VISUALS.night;
  }

  if (text.includes('snow') || text.includes('blizzard') || text.includes('flurr') || text.includes('frost') || text.includes('ice') || text.includes('sleet')) {
    return WEATHER_VISUALS.snow;
  }

  if (text.includes('rain') || text.includes('drizzle') || text.includes('shower') || text.includes('downpour') || text.includes('wet') || text.includes('monsoon')) {
    return WEATHER_VISUALS.rain;
  }

  if (text.includes('fog') || text.includes('mist') || text.includes('haze') || text.includes('smoke')) {
    return WEATHER_VISUALS.fog;
  }

  if (text.includes('partly') || text.includes('scattered') || text.includes('sun break') || text.includes('clearing') || text.includes('mainly sunny')) {
    return WEATHER_VISUALS.partlyCloudy;
  }

  if (text.includes('cloud') || text.includes('overcast') || text.includes('gray') || text.includes('heavy clouds') || text.includes('dense')) {
    return WEATHER_VISUALS.cloudy;
  }

  if (text.includes('sun') || text.includes('clear') || text.includes('hot') || text.includes('blazing') || text.includes('warm') || text.includes('fair')) {
    return WEATHER_VISUALS.sunny;
  }

  return WEATHER_VISUALS.cloudy;
}

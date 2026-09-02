// Comprehensive English and Hindi Localization Dictionary for WeatherGPT

export const TRANSLATIONS = {
  en: {
    // Navigation & Global Header
    appName: 'WeatherGPT',
    tabOverview: 'Overview',
    tabForecast: 'Forecast',
    tabMap: 'Map',
    tabAssistant: 'Assistant',
    searchCityPlaceholder: 'Search city...',
    selectLocation: 'Select Location',
    signInLogin: 'Sign In / Login',
    signOut: 'Sign Out',
    myAccount: 'My Account',
    history: 'History',

    // Hero Section
    goodDay: 'Good day',
    atmosphericIntelligence: 'Atmospheric Intelligence',
    awaitingLocation: 'Awaiting Location',
    chooseLocationOrGps: 'Choose Location or Enable GPS',
    feelsLike: 'Feels like',
    uvLabel: 'UV',
    humidityLabel: 'Humidity',
    windLabel: 'Wind',
    askWeatherGpt: 'Ask WeatherGPT',
    chooseLocationGpsBtn: 'Choose Location (GPS)',
    awaitingLocationHeroDesc: 'Please select your city or enable GPS coordinates to load live atmospheric conditions.',
    gpsRequired: 'GPS / City Selection Required',
    liveTelemetryProjected: 'Real-time telemetry projection powered by Open-Meteo.',

    // Today's Outlook & Day at a Glance
    todaysOutlook: "Today's Weather Outlook",
    yourDayAtAGlance: 'Your Day at a Glance',
    personalizedForActivity: 'Personalized for local activity',
    commute: 'Commute',
    outdoorPlans: 'Outdoor Plans',
    fitnessRun: 'Fitness & Workout',
    agroAdvisory: 'Agro Advisory',
    optimalRoutes: 'Optimal Routes',
    wetPavement: 'Wet Pavement',
    primeWindow: 'Prime Window',
    cautionWindow: 'Exercise Caution',

    // Timeline & Gauges
    todaysTimeline: "Today's Timeline & Temp Curve",
    timelineSub: '24-hour meteorological projection',
    liveTimeline: 'Live Timeline',
    clickHourInspect: 'Click any hour to inspect micro-atmospheric details',
    atmosphericGauges: 'Atmospheric Conditions & Gauges',
    liveMetrics: 'Live Metrics',
    pendingSelection: 'Pending Selection',
    
    // Gauge Labels
    humidity: 'Humidity',
    uvIndex: 'UV Index',
    windVector: 'Wind Vector',
    precipitation: 'Precipitation',
    barometer: 'Barometer',
    visibility: 'Visibility',
    dewPoint: 'Dew Point',
    humidAir: 'Humid Air',
    moderate: 'Moderate',
    comfort: 'Comfort',
    clearHorizon: 'Clear Horizon',
    hazyLow: 'Hazy / Low',

    // Solar Cycle
    solarCycleTitle: 'Solar Cycle & Daylight',
    solarCycleSub: 'Sun trajectory and astronomical daylight window',
    daylight: 'Daylight',
    dawnSunrise: 'Dawn · Sunrise',
    duskSunset: 'Dusk · Sunset',
    goldenHourStart: 'Golden Hour Start',
    civilTwilightEnd: 'Civil Twilight End',
    sunInSky: '☀️ Sun in Sky',
    nightInterval: '🌙 Night Interval',

    // Location Modal
    chooseYourLocation: 'Choose Your Location',
    locationModalSubtitle: 'Select your city or enable GPS for live weather telemetry',
    useCurrentLocationGps: 'Use My Current Location (GPS)',
    detectingGps: 'Detecting GPS Coordinates...',
    autoDetectDesc: 'Auto-detect exact live coordinates from browser',
    searchAnyCityPlaceholder: 'Search any global city, region or town...',
    popularCities: '🌍 Popular Cities',
    currentlyActive: '📍 Currently Active',
    savedFavorites: '⭐ Saved Favorites',
    clearSearch: 'Clear',

    // Settings Modal
    settingsTitle: 'Settings & Accessibility',
    temperatureUnit: 'Temperature Unit',
    tempUnitDesc: 'Switch between Celsius (°C) and Fahrenheit (°F)',
    fontSizeScaling: 'Font Size Scaling',
    fontSizeDesc: 'Adjust font scale for enhanced legibility',
    weatherAlertNotifications: 'Weather Alert Notifications',
    alertNotifDesc: 'Receive atmospheric advisory push alerts',
    appVersion: 'WeatherGPT Atmospheric Intelligence v3.0.0',
    appCredit: 'Live Open-Meteo Real-Time Meteorological Telemetry',

    // Language Modal
    languageSelectorTitle: 'Language Selector',

    // Forecast Analytics Tab
    forecastAnalyticsTitle: '7-Day & Climatological Analytics',
    forecastAnalyticsDesc: 'Please choose a city or enable GPS coordinates to load real-time multi-day forecasts and NWP model telemetry.',
    past7Days: 'Past 7 Days',
    past30Days: 'Past 30 Days',
    past1Year: '12 Months',
    tempMetric: 'Temperature',
    precipMetric: 'Rainfall',
    windMetric: 'Wind Speed',
    sevenDayForecast: '7-Day Forecast',
    nwpModelDiagnostics: 'NWP Model Diagnostics (GFS / ECMWF)',
    convectiveInstability: 'Atmospheric Convective Energy',
    capeCinIndex: 'CAPE & CIN Stability Index',
    cropWindowSafety: 'Agro Crop Advisory Window',

    // Map Tab
    interactiveRadar: 'Interactive Weather Radar',
    radarRainfall: 'Rainfall Radar',
    radarTemperature: 'Temperature Thermal',
    radarWind: 'Wind Velocity Stream',
    radarClouds: 'Cloud Coverage Satellite',
    radarPlayback: 'Radar Timeline Playback',
    mapInstructions: 'Click anywhere on the map to inspect live atmospheric telemetry',

    // Assistant Tab
    assistantTitle: 'MausamVani AI Meteorological Assistant',
    assistantSub: 'Multimodal Neural Agent with NWP Diagnostics, IMD Alerts & Agro Advisories',
    assistantPlaceholder: 'Ask about rainfall probability, travel safety, crop spray windows, or NWP models...',
    askPrompt1: 'Will it rain today in my city?',
    askPrompt2: 'Is it safe to spray crops today?',
    askPrompt3: 'Explain atmospheric CAPE instability',
    clearChat: 'Clear Chat',
    regenerate: 'Regenerate',
    listenVoice: 'Listen Voice',
    stopVoice: 'Stop Voice',

    // Alerts
    severeWarning: 'Severe Warning',
    heatWarning: 'Heat Warning',
    rainAdvisory: 'Rain Advisory',
    activeNow: 'Active Now',
    acknowledge: 'Acknowledge',
    shareAdvisory: 'Share Advisory'
  },

  hi: {
    // Navigation & Global Header
    appName: 'WeatherGPT',
    tabOverview: 'अवलोकन',
    tabForecast: 'पूर्वानुमान',
    tabMap: 'मौसम मानचित्र',
    tabAssistant: 'एआई सहायक',
    searchCityPlaceholder: 'शहर खोजें...',
    selectLocation: 'स्थान चुनें',
    signInLogin: 'साइन इन / लॉगिन',
    signOut: 'लॉग आउट',
    myAccount: 'मेरा खाता',
    history: 'इतिहास',

    // Hero Section
    goodDay: 'नमस्ते',
    atmosphericIntelligence: 'वायुमंडलीय मौसम विज्ञान',
    awaitingLocation: 'स्थान का चयन करें',
    chooseLocationOrGps: 'स्थान चुनें या GPS चालू करें',
    feelsLike: 'महसूस हो रहा है',
    uvLabel: 'यूवी (UV)',
    humidityLabel: 'आर्द्रता (नमी)',
    windLabel: 'हवा',
    askWeatherGpt: 'WeatherGPT से पूछें',
    chooseLocationGpsBtn: 'स्थान चुनें (GPS)',
    awaitingLocationHeroDesc: 'कृपया वास्तविक समय का मौसम देखने के लिए अपना शहर चुनें या GPS अनुमति दें।',
    gpsRequired: 'GPS या शहर चयन आवश्यक है',
    liveTelemetryProjected: 'Open-Meteo उपग्रह द्वारा लाइव मौसम डेटा।',

    // Today's Outlook & Day at a Glance
    todaysOutlook: 'आज का मौसम दृष्टिकोण',
    yourDayAtAGlance: 'आज की दिनचर्या व गतिविधियां',
    personalizedForActivity: 'स्थानीय गतिविधियों के अनुसार अनुकूलित',
    commute: 'यात्रा व आवागमन',
    outdoorPlans: 'बाहरी योजनाएं',
    fitnessRun: 'व्यायाम व दौड़',
    agroAdvisory: 'कृषि सलाह',
    optimalRoutes: 'उत्तम मार्ग',
    wetPavement: 'सड़क पर फिसलन',
    primeWindow: 'अनुकूल समय',
    cautionWindow: 'सावधानी बरतें',

    // Timeline & Gauges
    todaysTimeline: 'आज का समय चक्र और तापमान वक्र',
    timelineSub: '24 घंटे का मौसम पूर्वानुमान',
    liveTimeline: 'लाइव समय चक्र',
    clickHourInspect: 'मौसम की जानकारी के लिए किसी भी समय पर क्लिक करें',
    atmosphericGauges: 'वायुमंडलीय स्थिति और गेज',
    liveMetrics: 'लाइव माप',
    pendingSelection: 'चयन की प्रतीक्षा',

    // Gauge Labels
    humidity: 'आर्द्रता (नमी)',
    uvIndex: 'यूवी सूचकांक (UV)',
    windVector: 'हवा की गति और दिशा',
    precipitation: 'वर्षा (बारिश)',
    barometer: 'वायुमंडलीय दबाव',
    visibility: 'दृश्यता',
    dewPoint: 'ओस बिंदु',
    humidAir: 'अधिक नमी',
    moderate: 'मध्यम',
    comfort: 'सुखद',
    clearHorizon: 'साफ़ दृश्यता',
    hazyLow: 'धुंधला / कम',

    // Solar Cycle
    solarCycleTitle: 'सौर चक्र और दिन का समय',
    solarCycleSub: 'सूर्य प्रक्षेपवक्र और खगोलीय दिन का समय',
    daylight: 'दिन का प्रकाश',
    dawnSunrise: 'भोर · सूर्योदय',
    duskSunset: 'संध्या · सूर्यास्त',
    goldenHourStart: 'स्वर्ण काल प्रारंभ',
    civilTwilightEnd: 'गोधूलि समाप्त',
    sunInSky: '☀️ सूर्य आकाश में है',
    nightInterval: '🌙 रात्रि समय',

    // Location Modal
    chooseYourLocation: 'अपना स्थान चुनें',
    locationModalSubtitle: 'लाइव मौसम के लिए अपना शहर चुनें या GPS चालू करें',
    useCurrentLocationGps: 'मेरे वर्तमान स्थान का उपयोग करें (GPS)',
    detectingGps: 'GPS स्थान खोजा जा रहा है...',
    autoDetectDesc: 'ब्राउज़र से सीधे सटीक लाइव स्थान प्राप्त करें',
    searchAnyCityPlaceholder: 'दुनिया के किसी भी शहर या क्षेत्र का नाम खोजें...',
    popularCities: '🌍 प्रमुख शहर',
    currentlyActive: '📍 वर्तमान सक्रिय स्थान',
    savedFavorites: '⭐ सहेजे गए स्थान',
    clearSearch: 'हटाएं',

    // Settings Modal
    settingsTitle: 'सेटिंग्स और अनुकूलन',
    temperatureUnit: 'तापमान इकाई',
    tempUnitDesc: 'सेल्सियस (°C) और फारेनहाइट (°F) के बीच बदलें',
    fontSizeScaling: 'फॉन्ट का आकार',
    fontSizeDesc: 'स्पष्टता के लिए लिखावट का आकार बदलें',
    weatherAlertNotifications: 'मौसम चेतावनी सूचनाएं',
    alertNotifDesc: 'गंभीर मौसम के अलर्ट प्राप्त करें',
    appVersion: 'WeatherGPT Atmospheric Intelligence v3.0.0',
    appCredit: 'लाइव Open-Meteo रियल-टाइम मौसम विज्ञान',

    // Language Modal
    languageSelectorTitle: 'भाषा का चयन करें',

    // Forecast Analytics Tab
    forecastAnalyticsTitle: '7-दिवसीय और जलवायु विश्लेषण',
    forecastAnalyticsDesc: '7 दिनों का लाइव पूर्वानुमान और NWP मॉडल डेटा देखने के लिए कृपया कोई शहर चुनें या GPS चालू करें।',
    past7Days: 'पिछले 7 दिन',
    past30Days: 'पिछले 30 दिन',
    past1Year: '12 महीने (वार्षिक)',
    tempMetric: 'तापमान',
    precipMetric: 'वर्षा (बारिश)',
    windMetric: 'हवा की गति',
    sevenDayForecast: '7-दिवसीय पूर्वानुमान',
    nwpModelDiagnostics: 'NWP मौसम मॉडल डायग्नोस्टिक्स (GFS / ECMWF)',
    convectiveInstability: 'वायुमंडलीय ऊर्जा व तूफान संभावना',
    capeCinIndex: 'CAPE और CIN स्थिरता सूचकांक',
    cropWindowSafety: 'फसल सुरक्षा व कृषि छिड़काव समय',

    // Map Tab
    interactiveRadar: 'इंटरैक्टिव मौसम रडार',
    radarRainfall: 'वर्षा रडार',
    radarTemperature: 'तापमान थर्मल',
    radarWind: 'हवा का प्रवाह',
    radarClouds: 'बादलों का उपग्रह दृश्य',
    radarPlayback: 'रडार समय चक्र प्लेबैक',
    mapInstructions: 'लाइव मौसम देखने के लिए नक्शे पर कहीं भी क्लिक करें',

    // Assistant Tab
    assistantTitle: 'मौसमवाणी एआई मौसम सहायक',
    assistantSub: 'NWP मॉडल, IMD अलर्ट व कृषि सलाह से लैस स्मार्ट सहायक',
    assistantPlaceholder: 'बारिश, तापमान, यात्रा सुरक्षा या फसल छिड़काव के बारे में पूछें...',
    askPrompt1: 'क्या आज मेरे शहर में बारिश होगी?',
    askPrompt2: 'क्या आज फसल पर कीटनाशक छिड़कना सुरक्षित है?',
    askPrompt3: 'वायुमंडलीय CAPE स्थिरता के बारे में बताएं',
    clearChat: 'चैट साफ़ करें',
    regenerate: 'पुनः उत्पन्न करें',
    listenVoice: 'आवाज़ सुनें',
    stopVoice: 'आवाज़ रोकें',

    // Alerts
    severeWarning: 'गंभीर चेतावनी',
    heatWarning: 'भीषण गर्मी की चेतावनी',
    rainAdvisory: 'भारी बारिश की सलाह',
    activeNow: 'अभी सक्रिय',
    acknowledge: 'स्वीकार करें',
    shareAdvisory: 'साझा करें'
  }
};

// Weather Condition Localizations (English to Hindi)
export const CONDITION_TRANSLATIONS_HI = {
  'clear sky': 'साफ़ आसमान',
  'mainly clear': 'मुख्यतः साफ़',
  'mainly sunny': 'मुख्यतः धूप',
  'sunny & clear': 'धूप और साफ़',
  'sunny': 'धूप खिली है',
  'partly cloudy': 'आंशिक रूप से बादल',
  'cloudy': 'बादल छाए हैं',
  'cloudy & overcast': 'घने बादल',
  'overcast & cloudy': 'घने बादल',
  'overcast': 'घने काले बादल',
  'foggy': 'कोहरा',
  'fog & mist': 'कोहरा और धुंध',
  'depositing rime fog': 'सफेद घना कोहरा',
  'light drizzle': 'हल्की बूंदाबांदी',
  'moderate drizzle': 'मध्यम बूंदाबांदी',
  'dense drizzle': 'तेज़ बूंदाबांदी',
  'freezing drizzle': 'बर्फ़ीली बूंदाबांदी',
  'slight rain': 'हल्की बारिश',
  'moderate rain': 'मध्यम बारिश',
  'heavy rain': 'भारी बारिश',
  'rain & drizzle': 'बारिश और बूंदाबांदी',
  'showers': 'बारिश की बौछारें',
  'light rain showers': 'हल्की बारिश की बौछारें',
  'thunderstorm': 'गरज के साथ तूफान / आंधी',
  'thunderstorm with hail': 'ओलावृष्टि के साथ तूफान',
  'slight snow fall': 'हल्की बर्फबारी',
  'moderate snow fall': 'मध्यम बर्फबारी',
  'heavy snow fall': 'भारी बर्फबारी',
  'snow & flurries': 'बर्फबारी',
  'clear night': 'साफ़ रात',
  'awaiting location': 'स्थान का चयन करें',
  'connecting to live satellites...': 'उपग्रह से कनेक्ट हो रहा है...'
};

/**
 * Universal translation lookup helper
 */
export function getTranslation(key, langCode = 'en') {
  const lang = (langCode || 'en').toLowerCase().startsWith('hi') ? 'hi' : 'en';
  return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['en']?.[key] || key;
}

/**
 * Weather condition translator helper
 */
export function getTranslatedCondition(conditionStr = '', langCode = 'en') {
  if (!conditionStr) return '';
  const isHindi = (langCode || 'en').toLowerCase().startsWith('hi');
  if (!isHindi) return conditionStr;

  const clean = conditionStr.trim().toLowerCase();
  return CONDITION_TRANSLATIONS_HI[clean] || conditionStr;
}

/**
 * Localize Dynamic AI Insight string into active language
 */
export function getLocalizedInsight(currentCity, langCode = 'en') {
  if (!currentCity) return '';
  const isHi = (langCode || 'en').toLowerCase().startsWith('hi');
  if (!isHi) return currentCity.aiInsight || '';

  if (currentCity.aiInsightHi) return currentCity.aiInsightHi;

  const name = currentCity.name || 'आपके शहर';
  const tempC = currentCity.tempC ?? '--';
  const precip = currentCity.precipProbability ?? 0;
  const humidity = currentCity.humidity ?? '--';
  const uv = currentCity.uvIndex ?? '--';
  const feelsLike = currentCity.feelsLikeC ?? tempC;

  if (precip > 60) {
    return `${name} में बारिश की संभावना बहुत अधिक है (${precip}%)। बाहर जाते समय छाता या रेनकोट अवश्य साथ रखें और गीली सड़कों पर सावधानी से चलें।`;
  } else if (tempC > 32) {
    return `${name} में तेज़ धूप और लू का प्रभाव है (${tempC}°C, यूवी ${uv})। पर्याप्त पानी पिएं और दोपहर में सीधी धूप से बचें।`;
  } else if (tempC < 5) {
    return `${name} में शीतलहर सक्रिय है (${tempC}°C, महसूस हो रहा ${feelsLike}°C)। ठंड से बचाव के लिए गर्म कपड़े पहनें।`;
  } else {
    return `${name} में मौसम शांत और सुहावना है। मध्यम आर्द्रता (${humidity}%) के साथ बाहरी गतिविधियों व यात्रा के लिए अनुकूल समय है।`;
  }
}

/**
 * Localize Dynamic Severe Weather Alert object
 */
export function getLocalizedAlert(alert, langCode = 'en') {
  if (!alert) return null;
  const isHi = (langCode || 'en').toLowerCase().startsWith('hi');
  if (!isHi) return alert;

  const titleHi = alert.titleHi || (
    alert.title?.toLowerCase().includes('thunderstorm') || alert.title?.toLowerCase().includes('storm')
      ? 'आंधी-तूफान और वज्रपात की चेतावनी'
      : alert.title?.toLowerCase().includes('heat')
      ? 'भीषण लू व अत्यधिक गर्मी की चेतावनी'
      : 'भारी बारिश व वर्षा की सलाह'
  );

  const severityLabelHi = alert.severityLabelHi || (
    alert.severity === 'severe' ? 'गंभीर चेतावनी' : alert.severity === 'warning' ? 'मौसम चेतावनी' : 'मौसम सलाह'
  );

  const timingHi = alert.timingHi || (
    alert.timing === 'Active Now' ? 'अभी सक्रिय' : alert.timing || 'सक्रिय'
  );

  let shortDescHi = alert.shortDescHi;
  if (!shortDescHi && alert.shortDesc) {
    if (alert.shortDesc.includes('thunderstorm') || alert.shortDesc.includes('Lightning') || alert.shortDesc.includes('downpours')) {
      shortDescHi = 'गरज के साथ आंधी-तूफान और बिजली गिरने की संभावना। भारी बारिश हो सकती है।';
    } else if (alert.shortDesc.includes('heat') || alert.shortDesc.includes('thermal')) {
      shortDescHi = 'भीषण गर्मी और उच्च तापमान का प्रभाव। दोपहर में बाहर निकलने से बचें।';
    } else {
      shortDescHi = 'तेज़ बारिश और बूंदाबांदी की संभावना। सावधानी बरतें।';
    }
  }

  return {
    ...alert,
    title: titleHi,
    severityLabel: severityLabelHi,
    timing: timingHi,
    shortDesc: shortDescHi || alert.shortDesc,
    recommendedAction: alert.recommendedActionHi || alert.recommendedAction || 'सुरक्षित स्थान पर रहें और सावधानी बरतें।'
  };
}

/**
 * Localize Day-at-a-Glance item
 */
export function getLocalizedDayAtAGlanceItem(item, currentCity, langCode = 'en') {
  if (!item) return item;
  const isHi = (langCode || 'en').toLowerCase().startsWith('hi');
  if (!isHi) return item;

  const categoryMap = {
    'Commute': 'यात्रा व आवागमन',
    'Outdoor Plans': 'बाहरी योजनाएं',
    'Rain & Sun Gear': 'धूप व बारिश से बचाव',
    'Atmospheric Health': 'वायुमंडलीय स्वास्थ्य',
    'Fitness & Workout': 'व्यायाम व दौड़',
    'Agro Advisory': 'कृषि सलाह'
  };

  const statusMap = {
    'Wet Pavement': 'सड़क पर फिसलन',
    'Optimal Routes': 'सुगम आवागमन',
    'High Heat Window': 'अत्यधिक गर्मी',
    'Showers Possible': 'बारिश की संभावना',
    'Prime Window': 'अनुकूल समय',
    'Umbrella Advised': 'छाता साथ रखें',
    'Sun Protection': 'धूप से बचाव',
    'Standard': 'सामान्य',
    'Elevated Moisture': 'अधिक नमी',
    'Comfortable': 'सुखद वातावरण'
  };

  const category = item.categoryHi || categoryMap[item.category] || item.category;
  const status = item.statusHi || statusMap[item.status] || item.status;

  let text = item.textHi;
  if (!text) {
    const name = currentCity?.name || 'आपके क्षेत्र';
    if (item.id === 'commute') {
      text = (currentCity?.precipProbability ?? 0) > 50
        ? `बारिश की संभावना ${(currentCity?.precipProbability ?? 90)}% है। गीली सड़कों के कारण यात्रा में 10-15 मिनट अतिरिक्त समय लेकर चलें।`
        : `${name} में साफ़ मौसम और दृश्यता के साथ सामान्य यातायात की संभावना है।`;
    } else if (item.id === 'outdoor') {
      text = (currentCity?.tempC ?? 25) > 32
        ? `दोपहर में तापमान ${(currentCity?.tempC ?? 35)}°C तक पहुंचेगा। बाहरी कार्य सुबह 10 बजे से पहले या शाम 6 बजे के बाद करें।`
        : `सुखद तापमान (${currentCity?.tempC ?? 28}°C) और अनुकूल हवा के साथ बाहर जाने के लिए उत्तम समय।`;
    } else if (item.id === 'protection') {
      text = (currentCity?.precipProbability ?? 0) > 40
        ? `बारिश की संभावना ${(currentCity?.precipProbability ?? 80)}% तक है। बाहर निकलते समय छाता साथ रखें।`
        : `यूवी इंडेक्स ${currentCity?.uvIndex ?? 5} है। धूप का चश्मा और सनस्क्रीन का प्रयोग करें।`;
    } else if (item.id === 'health') {
      text = `सापेक्ष आर्द्रता ${currentCity?.humidity ?? 75}% और ओस बिंदु ${currentCity?.dewPointC ?? 20}°C है। वायुमंडलीय दबाव ${currentCity?.pressureHpa ?? 1013} hPa पर स्थिर है।`;
    } else {
      text = item.text;
    }
  }

  return {
    ...item,
    category,
    status,
    text
  };
}


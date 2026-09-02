import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { LANGUAGES, POPULAR_CITIES, DEFAULT_CITIES } from '../constants/appConfig';
import { fetchWeatherData, reverseGeocodeCoords } from '../services/weatherApi';
import { queryWeatherAgent, synthesizeSpeech } from '../services/aiAgentService';
import { getTranslation, getTranslatedCondition } from '../utils/translations';

const WeatherContext = createContext();

export function WeatherProvider({ children }) {
  // Current active live city state (initialized dynamically)
  const [currentCity, setCurrentCity] = useState(() => {
    try {
      const saved = localStorage.getItem('weathergpt_last_city');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed && typeof parsed.lat === 'number' && typeof parsed.lon === 'number') {
          return {
            ...parsed,
            tempC: null,
            tempF: null,
            condition: 'Connecting to Live Satellites...',
            conditionIcon: 'partly_cloudy_day',
            feelsLikeC: null,
            feelsLikeF: null,
            humidity: null,
            windKm: null,
            windDirection: 'N',
            windDegrees: 0,
            visibilityKm: 10.0,
            uvIndex: null,
            uvLabel: 'Live',
            precipProbability: 0,
            precipMm: 0.0,
            pressureHpa: 1013,
            pressureTrend: 'Steady ➔',
            dewPointC: null,
            dewPointF: null,
            sunrise: '--:--',
            sunset: '--:--',
            lastUpdated: 'Fetching live telemetry...',
            aiInsight: `Connecting to atmospheric telemetry...`,
            dayAtAGlance: [],
            alert: null,
            hourly: [],
            sevenDay: [],
            analytics: null,
            radarFrames: []
          };
        }
      }
    } catch (e) {}

    return {
      id: 'awaiting-location',
      name: 'Select Location',
      region: '',
      country: '',
      lat: 28.6139,
      lon: 77.2090,
      tempC: null,
      tempF: null,
      condition: 'Choose Location or Enable GPS',
      conditionIcon: 'partly_cloudy_day',
      feelsLikeC: null,
      feelsLikeF: null,
      humidity: null,
      windKm: null,
      windDirection: 'N',
      windDegrees: 0,
      visibilityKm: 10.0,
      uvIndex: null,
      uvLabel: 'Awaiting Location',
      precipProbability: 0,
      precipMm: 0.0,
      pressureHpa: 1013,
      pressureTrend: 'Steady ➔',
      dewPointC: null,
      dewPointF: null,
      sunrise: '--:--',
      sunset: '--:--',
      lastUpdated: 'Awaiting location...',
      aiInsight: 'Please select a city or use your GPS location to load real-time atmospheric intelligence.',
      dayAtAGlance: [],
      alert: null,
      hourly: [],
      sevenDay: [],
      analytics: null,
      radarFrames: []
    };
  });

  const [unit, setUnit] = useState('C'); // 'C' | 'F'
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'forecast' | 'map' | 'assistant'

  // Saved / Favorite Locations (persisted in localStorage)
  const [savedCities, setSavedCities] = useState(() => {
    try {
      const saved = localStorage.getItem('weathergpt_saved_cities');
      return saved ? JSON.parse(saved) : POPULAR_CITIES;
    } catch {
      return POPULAR_CITIES;
    }
  });

  // Modals state
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isLocationOpen, setIsLocationOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLanguageOpen, setIsLanguageOpen] = useState(false);
  const [isAlertDetailOpen, setIsAlertDetailOpen] = useState(false);
  const [activeAlert, setActiveAlert] = useState(null);
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);

  // Accessibility & Preferences (Language is persisted in localStorage)
  const [currentLanguage, setCurrentLanguageState] = useState(() => {
    try {
      const savedCode = localStorage.getItem('weathergpt_lang');
      if (savedCode) {
        const found = LANGUAGES.find(l => l.code === savedCode);
        if (found) return found;
      }
    } catch {}
    return LANGUAGES[0];
  });

  const setCurrentLanguage = (langObj) => {
    setCurrentLanguageState(langObj);
    try {
      localStorage.setItem('weathergpt_lang', langObj.code);
    } catch {}
  };

  // Translation helpers
  const t = (key) => getTranslation(key, currentLanguage?.code);
  const translateCondition = (cond) => getTranslatedCondition(cond, currentLanguage?.code);

  const [fontSizeMode, setFontSizeMode] = useState('standard');
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);
  const [isSkeletonLoading, setIsSkeletonLoading] = useState(false);
  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [weatherError, setWeatherError] = useState(null);

  // Theme / Night Mode State (Persisted in localStorage)
  const [theme, setThemeState] = useState(() => {
    try {
      const saved = localStorage.getItem('weathergpt_theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return 'dark'; // Default to sleek night mode
    } catch {
      return 'dark';
    }
  });

  const isDarkMode = theme === 'dark';

  const setTheme = (newTheme) => {
    setThemeState(newTheme);
    try {
      localStorage.setItem('weathergpt_theme', newTheme);
    } catch {}
  };

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
  };

  // Synchronize documentElement and body class with active theme
  useEffect(() => {
    if (typeof document !== 'undefined') {
      const root = document.documentElement;
      const body = document.body;
      if (theme === 'dark') {
        root.classList.add('dark');
        root.classList.remove('light');
        body?.classList?.add('dark');
        body?.classList?.remove('light');
        root.style.colorScheme = 'dark';
      } else {
        root.classList.remove('dark');
        root.classList.add('light');
        body?.classList?.remove('dark');
        body?.classList?.add('light');
        root.style.colorScheme = 'light';
      }
    }
  }, [theme]);

  // Chat Assistant State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'msg-1',
      sender: 'ai',
      text: 'Hello! I am WeatherGPT Intelligence. I am connected directly to real-time meteorological satellite APIs. Ask me about rainfall probabilities, travel safety, workout windows, or weekend outlooks for any city!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isAudioPlaying: false,
      feedback: null
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  // Save favorites to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('weathergpt_saved_cities', JSON.stringify(savedCities));
    } catch (e) {
      console.warn('LocalStorage error:', e);
    }
  }, [savedCities]);

  // Initial location resolution on app load
  useEffect(() => {
    const savedLastCity = localStorage.getItem('weathergpt_last_city');
    if (savedLastCity) {
      try {
        const parsed = JSON.parse(savedLastCity);
        if (parsed && typeof parsed.lat === 'number' && typeof parsed.lon === 'number') {
          loadLiveWeather(parsed);
          return;
        }
      } catch (e) {
        console.warn('Error parsing saved last city:', e);
      }
    }

    // If no prior saved city, open the location picker modal so user can choose or allow GPS
    setIsLocationOpen(true);

    // Prompt GPS detection automatically
    if (navigator.geolocation) {
      detectCurrentLocation();
    }
  }, []);

  /**
   * Main function to load real-time weather from Open-Meteo API
   */
  const loadLiveWeather = async ({ lat, lon, name, region, country, id }) => {
    setIsSkeletonLoading(true);
    setWeatherError(null);

    try {
      const liveData = await fetchWeatherData({ lat, lon, name, region, country, id });
      setCurrentCity(liveData);

      // Persist chosen city to localStorage
      try {
        localStorage.setItem('weathergpt_last_city', JSON.stringify({
          id: id || `${name}-${lat}-${lon}`,
          name,
          region,
          country,
          lat,
          lon
        }));
      } catch (e) {}

      showToast(`Live weather loaded for ${name}`);
    } catch (err) {
      console.error('Failed to load weather:', err);
      setWeatherError('Unable to connect to live weather service. Please check connection.');
      showToast('Error connecting to live weather API');
    } finally {
      setIsSkeletonLoading(false);
    }
  };

  /**
   * Browser Geolocation GPS Auto-Detection
   */
  const detectCurrentLocation = () => {
    if (!navigator.geolocation) {
      showToast('Geolocation is not supported by your browser');
      return;
    }

    setIsDetectingLocation(true);
    showToast('Detecting your GPS location...');

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const { latitude, longitude } = pos.coords;
        try {
          const geoInfo = await reverseGeocodeCoords(latitude, longitude);
          await loadLiveWeather({
            lat: latitude,
            lon: longitude,
            name: geoInfo.name,
            region: geoInfo.region,
            country: geoInfo.country
          });
          setIsLocationOpen(false);
          setIsSearchOpen(false);
        } catch (e) {
          console.error(e);
          showToast('Could not resolve your location name');
        } finally {
          setIsDetectingLocation(false);
        }
      },
      (error) => {
        setIsDetectingLocation(false);
        console.warn('Geolocation error:', error);
        showToast('Location permission denied or unavailable');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const switchCity = (target) => {
    if (!target) return;
    if (typeof target === 'string') {
      const found = savedCities.find(c => c.id === target) || DEFAULT_CITIES.find(c => c.id === target);
      if (found) {
        loadLiveWeather(found);
      }
    } else if (target.lat !== undefined && target.lon !== undefined) {
      loadLiveWeather({
        lat: target.lat,
        lon: target.lon,
        name: target.name || 'Selected City',
        region: target.region || '',
        country: target.country || '',
        id: target.id || `${target.name}-${target.lat}-${target.lon}`
      });
    }
  };

  const refreshWeather = () => {
    if (currentCity?.lat && currentCity?.lon) {
      loadLiveWeather(currentCity);
    }
  };

  const toggleUnit = () => {
    const newUnit = unit === 'C' ? 'F' : 'C';
    setUnit(newUnit);
    showToast(`Temperature unit switched to °${newUnit}`);
  };

  const toggleSavedCity = (cityObj) => {
    const cityId = typeof cityObj === 'string' ? cityObj : cityObj.id;
    setSavedCities(prev => {
      const exists = prev.some(c => c.id === cityId);
      let updated;
      if (exists) {
        updated = prev.filter(c => c.id !== cityId);
        showToast(`Removed from favorites`);
      } else {
        const cityToAdd = typeof cityObj === 'object' ? cityObj : { id: cityId, name: currentCity.name, lat: currentCity.lat, lon: currentCity.lon, country: currentCity.country, region: currentCity.region };
        updated = [...prev, cityToAdd];
        showToast(`Saved ${cityToAdd.name} to favorites`);
      }
      return updated;
    });
  };

  const showToast = (text) => {
    setToastMessage(text);
    setTimeout(() => {
      setToastMessage(null);
    }, 3200);
  };

  const openAlertModal = (alertObj) => {
    setActiveAlert(alertObj || currentCity.alert);
    setIsAlertDetailOpen(true);
  };

  const activeAudioRef = useRef(null);

  /**
   * Real-time Multimodal AI Weather Agent Chat (Connected to MausamVani API)
   */
  const sendChatMessage = async (userText, autoPlayVoice = false) => {
    if (!userText || !userText.trim()) return;

    const userMsg = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: userText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatMessages(prev => [...prev, userMsg]);
    setIsTyping(true);

    try {
      // 1. Query the live MausamVani Multimodal Weather AI Agent Backend
      const authToken = localStorage.getItem('weathergpt_auth_token') || undefined;
      const activeConvId = sessionStorage.getItem('weathergpt_active_conv_id') || undefined;

      const agentResult = await queryWeatherAgent({
        query: userText,
        locationName: currentCity?.name,
        languageCode: currentLanguage?.code || 'auto',
        unit,
        token: authToken,
        conversationId: activeConvId
      });

      if (agentResult && agentResult.success && agentResult.text) {
        if (agentResult.conversationId) {
          sessionStorage.setItem('weathergpt_active_conv_id', agentResult.conversationId);
        }

        const aiMsgId = `msg-${Date.now() + 1}`;
        const aiMsg = {
          id: aiMsgId,
          sender: 'ai',
          text: agentResult.text,
          actionCard: agentResult.actionCard,
          detectedLanguage: agentResult.detectedLanguage,
          audioOutputFile: agentResult.audioOutputFile,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isAudioPlaying: false,
          feedback: null
        };
        setChatMessages(prev => [...prev, aiMsg]);
        setIsTyping(false);

        if (autoPlayVoice) {
          setTimeout(() => {
            toggleAudioSpeech(aiMsgId);
          }, 350);
        }
        return;
      }
    } catch (err) {
      console.warn('Agent API query error, using resilient fallback:', err);
    }

    // 2. Intelligent Real-Time Meteorological Synthesis Fallback
    setTimeout(() => {
      const tempStr = unit === 'C' ? `${currentCity.tempC}°C` : `${currentCity.tempF}°F`;
      const precip = currentCity.precipProbability ?? 0;
      
      const fallbackAiText = `### 🌤️ Weather & Atmospheric Report for **${currentCity.name}**\n\n**Current Conditions:** ${currentCity.condition}, **${tempStr}** (Feels like ${unit === 'C' ? currentCity.feelsLikeC + '°C' : currentCity.feelsLikeF + '°F'}), Humidity: ${currentCity.humidity}%, Wind: ${currentCity.windKm} km/h from ${currentCity.windDirection}.\n\n**🌀 NWP & Atmospheric Diagnostics:** Surface barometric pressure is ${currentCity.pressureHpa} hPa (${currentCity.pressureTrend}). Solar UV radiation index is ${currentCity.uvIndex} (${currentCity.uvLabel}). Precipitation probability is ${precip}% (${currentCity.precipMm} mm/h).\n\n**🌾 Agricultural & Safety Guidance:** Optimal window for field management. Maintain standard irrigation schedules according to local soil moisture.`;

      const aiMsgId = `msg-${Date.now() + 1}`;
      const aiMsg = {
        id: aiMsgId,
        sender: 'ai',
        text: fallbackAiText,
        actionCard: {
          title: `${currentCity.name} Live Telemetry`,
          subtitle: `${currentCity.condition} · Wind ${currentCity.windKm} km/h · Precip ${precip}%`,
          metric: tempStr,
          badge: 'LIVE TELEMETRY',
          icon: 'wb_sunny'
        },
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isAudioPlaying: false,
        feedback: null
      };

      setChatMessages(prev => [...prev, aiMsg]);
      setIsTyping(false);

      if (autoPlayVoice) {
        setTimeout(() => {
          toggleAudioSpeech(aiMsgId);
        }, 350);
      }
    }, 600);
  };

  const handleFeedback = (msgId, type) => {
    setChatMessages(prev =>
      prev.map(msg => msg.id === msgId ? { ...msg, feedback: type } : msg)
    );
    showToast(type === 'up' ? 'Feedback recorded: Helpful!' : 'Feedback recorded: Thanks for reporting.');
  };

  const regenerateAiResponse = async (msgId) => {
    const targetMsg = chatMessages.find(m => m.id === msgId);
    if (!targetMsg) return;

    // Find the prior user message
    const msgIdx = chatMessages.findIndex(m => m.id === msgId);
    const userMsg = msgIdx > 0 ? chatMessages[msgIdx - 1]?.text : `Current weather and NWP forecast for ${currentCity.name}`;

    setIsTyping(true);
    showToast('Regenerating AI response with live agent telemetry...');

    try {
      const agentResult = await queryWeatherAgent({
        query: userMsg || `Weather for ${currentCity.name}`,
        locationName: currentCity?.name,
        languageCode: currentLanguage?.code || 'auto',
        unit
      });

      if (agentResult && agentResult.success && agentResult.text) {
        setChatMessages(prev =>
          prev.map(msg => {
            if (msg.id === msgId) {
              return {
                ...msg,
                text: agentResult.text,
                actionCard: agentResult.actionCard,
                detectedLanguage: agentResult.detectedLanguage,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              };
            }
            return msg;
          })
        );
        setIsTyping(false);
        return;
      }
    } catch (err) {
      console.warn('Regenerate agent query error:', err);
    }

    setTimeout(() => {
      setChatMessages(prev =>
        prev.map(msg => {
          if (msg.id === msgId) {
            return {
              ...msg,
              text: `Live atmospheric recalculation for ${currentCity.name}: Barometric pressure is ${currentCity.pressureHpa} hPa (${currentCity.pressureTrend}). Wind vector is ${currentCity.windKm} km/h from ${currentCity.windDirection}. UV Index is ${currentCity.uvIndex}.`,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
          }
          return msg;
        })
      );
      setIsTyping(false);
    }, 600);
  };

  const toggleAudioSpeech = async (msgId) => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current = null;
    }

    const targetMsg = chatMessages.find(m => m.id === msgId);
    if (!targetMsg) return;

    if (targetMsg.isAudioPlaying) {
      setChatMessages(prev =>
        prev.map(msg => ({ ...msg, isAudioPlaying: false }))
      );
      return;
    }

    setChatMessages(prev =>
      prev.map(msg => ({ ...msg, isAudioPlaying: msg.id === msgId }))
    );

    const cleanText = targetMsg.text.replace(/[*#_`•]/g, '').trim();

    try {
      const audioUrl = await synthesizeSpeech({
        text: cleanText,
        languageCode: targetMsg.detectedLanguage || currentLanguage.code || 'hi'
      });

      if (audioUrl) {
        const audio = new Audio(audioUrl);
        activeAudioRef.current = audio;
        audio.onended = () => {
          setChatMessages(prev =>
            prev.map(msg => msg.id === msgId ? { ...msg, isAudioPlaying: false } : msg)
          );
          activeAudioRef.current = null;
        };
        audio.onerror = (e) => {
          console.warn('Audio playback error, falling back to Web Speech API:', e);
          setChatMessages(prev =>
            prev.map(msg => msg.id === msgId ? { ...msg, isAudioPlaying: false } : msg)
          );
          speakWithBrowser(cleanText, msgId);
        };
        await audio.play();
        return;
      }
    } catch (err) {
      console.warn('Neural TTS failed, falling back to browser speech synthesis:', err);
    }

    speakWithBrowser(cleanText, msgId);
  };

  const speakWithBrowser = (cleanText, msgId) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.onend = () => {
        setChatMessages(prev =>
          prev.map(msg => msg.id === msgId ? { ...msg, isAudioPlaying: false } : msg)
        );
      };
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    }
  };

  const clearChatHistory = () => {
    setChatMessages([]);
    showToast('Chat history cleared');
  };

  const formatTemp = (tempC, tempF) => {
    return unit === 'C' ? `${tempC}°` : `${tempF}°`;
  };

  const savedCityIds = savedCities.map(c => c.id);

  return (
    <WeatherContext.Provider
      value={{
        currentCity,
        switchCity,
        loadLiveWeather,
        refreshWeather,
        detectCurrentLocation,
        isDetectingLocation,
        weatherError,
        unit,
        toggleUnit,
        formatTemp,
        savedCities,
        savedCityIds,
        toggleSavedCity,
        activeTab,
        setActiveTab,
        isSearchOpen,
        setIsSearchOpen,
        isLocationOpen,
        setIsLocationOpen,
        isSettingsOpen,
        setIsSettingsOpen,
        isLanguageOpen,
        setIsLanguageOpen,
        isAlertDetailOpen,
        setIsAlertDetailOpen,
        activeAlert,
        openAlertModal,
        isVoiceOpen,
        setIsVoiceOpen,
        currentLanguage,
        setCurrentLanguage,
        t,
        translateCondition,
        fontSizeMode,
        setFontSizeMode,
        notificationsEnabled,
        setNotificationsEnabled,
        toastMessage,
        showToast,
        isSkeletonLoading,
        chatMessages,
        setChatMessages,
        isTyping,
        sendChatMessage,
        toggleAudioSpeech,
        theme,
        setTheme,
        toggleTheme,
        isDarkMode,
        clearChatHistory
      }}

    >
      <div className={`min-h-screen ${fontSizeMode === 'large' ? 'text-lg' : ''}`}>
        {children}
      </div>
    </WeatherContext.Provider>
  );
}

export function useWeather() {
  return useContext(WeatherContext);
}

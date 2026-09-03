/**
 * AI Agent & Authentication Integration Service
 * Connects the Frontend Assistant & UI to the MausamVani Multimodal Weather AI Agent Backend.
 *
 * Supports:
 * 1. Real-time weather information retrieval & Assistant chat
 * 2. JWT Authentication (OTP request, OTP verification, password creation, login, logout, me)
 * 3. User-owned persistent assistant conversation history
 * 4. NWP Model diagnostics (GFS/WRF/ECMWF, CAPE, CIN, 500hPa)
 * 5. Extreme weather alerts and early warnings (IMD/NDMA CAP)
 * 6. Location-based forecasting & crop agro-advisories
 * 7. Multilingual support for Indian languages (Hindi, Telugu, Tamil, Marathi, etc.)
 * 8. Climate trend & historical weather analysis (Kaggle Indian Cities Dataset 1990-2023)
 * 9. Voice-enabled interaction & Neural TTS speech synthesis
 */

const AGENT_API_BASE = (typeof window !== 'undefined' && window.location.port === '3000')
  ? 'http://localhost:8000/api'
  : (import.meta.env.VITE_API_BASE_URL
      ? (import.meta.env.VITE_API_BASE_URL.endsWith('/api') ? import.meta.env.VITE_API_BASE_URL : `${import.meta.env.VITE_API_BASE_URL}/api`)
      : '/api');



// Persistent session management across turns for guest sessions
function getOrCreateSessionId() {
  try {
    let sid = window?.sessionStorage?.getItem('weathergpt_session_id');
    if (!sid) {
      sid = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 8);
      window?.sessionStorage?.setItem('weathergpt_session_id', sid);
    }
    return sid;
  } catch (e) {
    return 'default_session';
  }
}

/**
 * Sends a natural language query to the Multimodal Weather AI Agent.
 * When token is supplied, backend automatically saves messages to user's MongoDB history.
 */
export async function queryWeatherAgent({
  query,
  locationName,
  languageCode = 'auto',
  unit = 'C',
  sessionId,
  conversationId,
  token
}) {
  try {
    const activeSessionId = sessionId || getOrCreateSessionId();
    const headers = {
      'Content-Type': 'application/json'
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${AGENT_API_BASE}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query,
        location_name: locationName,
        language_code: languageCode,
        unit,
        session_id: activeSessionId,
        conversation_id: conversationId || undefined
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Agent server returned status ${res.status}`);
    }

    const data = await res.json();
    return {
      success: true,
      text: data.response_text || data.raw_english_response,
      translatedText: data.translated_response,
      detectedLanguage: data.detected_language,
      actionCard: data.action_card,
      hasAdvisory: data.has_advisory,
      hasNwp: data.has_nwp,
      hasAlerts: data.has_alerts,
      hasClimate: data.has_climate,
      audioOutputFile: data.audio_output_file,
      conversationId: data.conversation_id,
      isAuthenticated: data.is_authenticated
    };
  } catch (err) {
    console.warn('Multimodal Weather Agent API query error:', err);
    return null;
  }
}

/**
 * Synthesize Neural Text-to-Speech via edge-tts (Indian regional voices).
 */
export async function synthesizeSpeech({ text, languageCode = 'hi' }) {
  try {
    const res = await fetch(`${AGENT_API_BASE}/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text,
        language_code: languageCode
      })
    });

    if (!res.ok) throw new Error('TTS generation failed');

    const data = await res.json();
    if (data.audio_base64) {
      const mime = data.format || 'audio/mp3';
      return `data:${mime};base64,${data.audio_base64}`;
    }
    return null;
  } catch (err) {
    console.warn('Agent TTS fallback:', err);
    return null;
  }
}

/**
 * Transcribe raw audio recording via Python Whisper STT engine.
 */
export async function transcribeAudio(audioBlob, languageCode = 'auto') {
  try {
    const formData = new FormData();
    formData.append('file', audioBlob, 'voice_query.webm');
    formData.append('language', languageCode);

    const res = await fetch(`${AGENT_API_BASE}/stt`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) throw new Error(`STT failed with status ${res.status}`);
    const data = await res.json();
    return data.transcript || null;
  } catch (err) {
    console.warn('Backend STT failed:', err);
    return null;
  }
}

// =============================================================================
// Authentication API Endpoints
// =============================================================================

/**
 * Step 1: Request 6-digit registration OTP code to email.
 */
export async function requestOtpApi(email) {
  const res = await fetch(`${AGENT_API_BASE}/auth/register/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to send verification code.');
  }
  return data;
}

/**
 * Step 2: Verify 6-digit OTP code.
 */
export async function verifyOtpApi(email, otp) {
  const res = await fetch(`${AGENT_API_BASE}/auth/register/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Invalid or expired verification code.');
  }
  return data;
}

/**
 * Direct user registration (Email + Password + Name, no OTP).
 */
export async function directRegisterApi({ name, email, password }) {
  const res = await fetch(`${AGENT_API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to create account.');
  }
  return data;
}

/**
 * Google OAuth Login & Registration.
 */
export async function googleLoginApi({ credential, email, name, picture, sub }) {
  const res = await fetch(`${AGENT_API_BASE}/auth/google`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ credential, email, name, picture, sub })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Google sign in failed.');
  }
  return data;
}

/**
 * Step 3: Set password and finalize account creation.
 */
export async function setPasswordApi({ email, verificationToken, password, name }) {
  const res = await fetch(`${AGENT_API_BASE}/auth/register/set-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      verification_token: verificationToken,
      password,
      name
    })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Failed to create account.');
  }
  return data;
}

/**
 * Login with Email and Password.
 */
export async function loginApi(email, password) {
  const res = await fetch(`${AGENT_API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || 'Invalid email or password.');
  }
  return data;
}

/**
 * Logout and clear session.
 */
export async function logoutApi() {
  try {
    await fetch(`${AGENT_API_BASE}/auth/logout`, {
      method: 'POST'
    });
  } catch (e) {
    // Ignore network error on logout
  }
}

/**
 * Get current authenticated user profile.
 */
export async function fetchCurrentUserApi(token) {
  if (!token) return null;
  const res = await fetch(`${AGENT_API_BASE}/auth/me`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.user || null;
}

// =============================================================================
// Assistant History API Endpoints
// =============================================================================

/**
 * List all saved conversation sessions for the authenticated user.
 */
export async function fetchAssistantHistoryApi(token) {
  if (!token) return [];
  const res = await fetch(`${AGENT_API_BASE}/assistant/history`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.conversations || [];
}

/**
 * Get specific conversation message timeline.
 */
export async function fetchConversationDetailsApi(conversationId, token) {
  if (!token || !conversationId) return null;
  const res = await fetch(`${AGENT_API_BASE}/assistant/history/${conversationId}`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.conversation || null;
}

/**
 * Create a new conversation thread.
 */
export async function createConversationApi(title, token) {
  if (!token) return null;
  const res = await fetch(`${AGENT_API_BASE}/assistant/conversations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ title: title || 'New Weather Conversation' })
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data.conversation || null;
}

/**
 * Delete a conversation thread.
 */
export async function deleteConversationApi(conversationId, token) {
  if (!token || !conversationId) return false;
  const res = await fetch(`${AGENT_API_BASE}/assistant/history/${conversationId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return res.ok;
}

/**
 * Fetch available hardware microphone devices on the host system.
 */
export async function fetchAudioDevicesApi() {
  try {
    const res = await fetch(`${AGENT_API_BASE}/voice/devices`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.devices || [];
  } catch (e) {
    return [];
  }
}

/**
 * Triggers Python real-time microphone listening with Voice Activity Detection (VAD).
 */
export async function listenDeviceMicApi({ language = 'hi-IN', maxDuration = 10.0, locationName, deviceIndex } = {}) {
  try {
    const res = await fetch(`${AGENT_API_BASE}/voice/listen-mic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language,
        max_duration: maxDuration,
        location_name: locationName,
        device_index: deviceIndex
      })
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (e) {
    console.warn('Realtime mic capture error:', e);
    return null;
  }
}


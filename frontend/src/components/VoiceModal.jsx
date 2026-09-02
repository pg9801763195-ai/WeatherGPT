import React, { useState, useEffect, useRef } from 'react';
import { useWeather } from '../context/WeatherContext';
import { LANGUAGES } from '../constants/appConfig';
import { transcribeAudio } from '../services/aiAgentService';

export default function VoiceModal() {
  const {
    isVoiceOpen,
    setIsVoiceOpen,
    sendChatMessage,
    setActiveTab,
    currentCity,
    currentLanguage,
    setCurrentLanguage,
    showToast
  } = useWeather();

  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [micStatus, setMicStatus] = useState('Tap the microphone to speak');
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const isHi = currentLanguage?.code === 'hi';
  const activeCityName = currentCity?.name && currentCity.name !== 'Select Location' ? currentCity.name : (isHi ? 'मेरे शहर' : 'my city');
  const quickVoicePrompts = isHi ? [
    `क्या आज ${activeCityName} में बारिश होगी?`,
    `क्या अभी बाहर निकलना या ड्राइव करना सुरक्षित है?`,
    `आज का तापमान और हवा की गति क्या है?`,
    `इस वीकेंड ${activeCityName} का मौसम पूर्वानुमान बताएं`
  ] : [
    `Will it rain in ${activeCityName} today?`,
    `Is it safe to go outdoors or drive right now?`,
    `What is the current temperature & wind speed?`,
    `Tell me the weekend forecast for ${activeCityName}`
  ];

  useEffect(() => {
    if (!isVoiceOpen) {
      cleanupAudio();
      setIsRecording(false);
      setTranscript('');
      setIsTranscribing(false);
      return;
    }

    startListening();

    return () => {
      cleanupAudio();
    };
  }, [isVoiceOpen, currentLanguage?.code]);

  const cleanupAudio = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
      mediaRecorderRef.current = null;
    }
  };

  const startListening = async () => {
    cleanupAudio();
    setIsRecording(true);
    setMicStatus('Listening... Speak now');

    // 1. Start browser speech recognition for live visual feedback
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        const langMap = {
          en: 'en-IN',
          hi: 'hi-IN',
          te: 'te-IN',
          ta: 'ta-IN',
          bn: 'bn-IN',
          mr: 'mr-IN',
          gu: 'gu-IN',
          kn: 'kn-IN',
          ml: 'ml-IN',
          pa: 'pa-IN'
        };
        recognition.lang = langMap[currentLanguage?.code] || 'en-IN';

        recognition.onresult = (event) => {
          let full = '';
          for (let i = 0; i < event.results.length; i++) {
            full += event.results[i][0].transcript + ' ';
          }
          if (full.trim()) {
            setTranscript(full.trim());
          }
        };

        recognition.onerror = (e) => {
          if (e.error !== 'no-speech') {
            console.warn('SpeechRecognition status:', e.error);
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      } catch (err) {
        console.warn('SpeechRecognition initialization notice:', err);
      }
    }

    // 2. Also start MediaRecorder for Whisper backup
    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            audioChunksRef.current.push(event.data);
          }
        };

        mediaRecorder.start(250);
        mediaRecorderRef.current = mediaRecorder;
      }
    } catch (err) {
      console.warn('MediaRecorder audio capture notice:', err);
    }
  };

  const stopAndSubmit = async (customQuery = null) => {
    let finalQuery = customQuery || transcript.trim();

    // If no live transcript yet, attempt Whisper backend transcription
    if (!finalQuery && audioChunksRef.current.length > 0) {
      setIsTranscribing(true);
      setMicStatus('Transcribing via Whisper AI...');
      try {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const backendTranscript = await transcribeAudio(audioBlob, currentLanguage?.code || 'auto');
        if (backendTranscript) {
          finalQuery = backendTranscript;
        }
      } catch (e) {
        console.warn('Whisper STT fallback:', e);
      }
      setIsTranscribing(false);
    }

    if (!finalQuery) {
      finalQuery = `What is the weather and forecast for ${currentCity.name}?`;
    }

    cleanupAudio();
    setIsRecording(false);
    setIsVoiceOpen(false);
    setActiveTab('assistant');

    // Send chat message with autoPlayVoice=true so assistant automatically speaks back!
    sendChatMessage(finalQuery, true);
  };

  if (!isVoiceOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-outline-variant/20 shadow-2xl max-w-md w-full p-6 sm:p-8 flex flex-col items-center text-center space-y-5">
        
        {/* Language selector header */}
        <div className="w-full flex justify-between items-center text-xs text-on-surface-variant border-b border-outline-variant/10 pb-3">
          <span className="font-label-caps uppercase font-bold text-primary flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            Voice Intelligence
          </span>
          <select
            value={currentLanguage?.code || 'en'}
            onChange={(e) => {
              const lang = LANGUAGES.find(l => l.code === e.target.value);
              if (lang) setCurrentLanguage(lang);
            }}
            className="bg-surface-container border border-outline-variant/20 rounded-lg px-2.5 py-1 text-xs text-on-surface focus:ring-0 cursor-pointer font-medium"
          >
            {LANGUAGES.map(l => (
              <option key={l.code} value={l.code}>
                {l.flag} {l.name}
              </option>
            ))}
          </select>
        </div>

        {/* Pulsing Mic Visualizer Button */}
        <div className="relative my-2 flex items-center justify-center">
          {isRecording && (
            <>
              <span className="absolute w-28 h-28 rounded-full bg-primary/20 animate-ping"></span>
              <span className="absolute w-24 h-24 rounded-full bg-primary/30 animate-pulse"></span>
            </>
          )}
          <button
            type="button"
            onClick={isRecording ? () => stopAndSubmit() : startListening}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center text-white shadow-2xl transition-all active:scale-95 cursor-pointer ${
              isRecording 
                ? 'bg-primary border-4 border-white' 
                : 'bg-slate-700 border-4 border-slate-500 hover:bg-slate-600'
            }`}
            title={isRecording ? 'Tap when done speaking' : 'Tap to start speaking'}
          >
            <span className="material-symbols-outlined text-3xl">
              {isRecording ? 'mic' : 'mic_none'}
            </span>
          </button>
        </div>

        <div>
          <span className="font-label-caps text-xs font-bold text-primary tracking-wider uppercase block mb-1">
            {isTranscribing ? 'Processing Whisper AI...' : micStatus}
          </span>
          
          <div className="min-h-[60px] max-h-[100px] overflow-y-auto bg-surface-container-low/60 rounded-2xl p-3 border border-outline-variant/15 flex items-center justify-center">
            <p className="font-body-md text-sm font-semibold text-on-surface leading-relaxed">
              {transcript ? (
                `"${transcript}"`
              ) : (
                <span className="text-on-surface-variant/60 italic text-xs font-normal">
                  Speak clearly into your microphone in {currentLanguage?.name}...
                </span>
              )}
            </p>
          </div>
        </div>

        {/* Quick Voice Prompt Suggestions */}
        <div className="w-full text-left space-y-1.5">
          <span className="text-[10px] text-on-surface-variant uppercase tracking-wider block font-label-caps font-bold">
            Or Tap to Ask & Hear Spoken Reply:
          </span>
          <div className="flex flex-wrap gap-1.5">
            {quickVoicePrompts.map((prompt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => stopAndSubmit(prompt)}
                className="text-xs bg-surface-container border border-outline-variant/20 rounded-full px-3 py-1 text-on-surface hover:bg-primary hover:text-white transition-all cursor-pointer text-left"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Modal Action Buttons */}
        <div className="w-full flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={() => {
              cleanupAudio();
              setIsVoiceOpen(false);
            }}
            className="flex-1 py-2.5 rounded-full border border-outline-variant/30 text-on-surface-variant text-xs font-semibold hover:bg-surface-container transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => stopAndSubmit()}
            className="flex-1 py-2.5 rounded-full bg-primary text-white text-xs font-bold shadow-md hover:bg-primary/90 transition-all active:scale-95 cursor-pointer flex items-center justify-center gap-1.5"
          >
            <span>Ask & Speak</span>
            <span className="material-symbols-outlined text-sm">volume_up</span>
          </button>
        </div>
      </div>
    </div>
  );
}

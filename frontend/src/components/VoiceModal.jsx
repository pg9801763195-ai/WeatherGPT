import React, { useState, useEffect, useRef } from 'react';
import { useWeather } from '../context/WeatherContext';
import { LANGUAGES } from '../constants/appConfig';
import { transcribeAudio, listenDeviceMicApi } from '../services/aiAgentService';

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
  const [micStatus, setMicStatus] = useState('Listening... Speak now');
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [useHardwareMic, setUseHardwareMic] = useState(false);

  const recognitionRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);

  const isHi = currentLanguage?.code === 'hi';
  const isOr = currentLanguage?.code === 'or';
  const activeCityName = currentCity?.name && currentCity.name !== 'Select Location' ? currentCity.name : (isHi ? 'मेरे शहर' : 'my city');

  const quickVoicePrompts = isOr ? [
    `କଣ ଆଜି ${activeCityName} ରେ ବର୍ଷା ହେବ?`,
    `କଣ ଏବେ ବାହାରକୁ ଯିବା ସୁରକ୍ଷିତ?`,
    `ଆଜି ତାପମାତ୍ରା କେତେ ଅଛି?`,
    `ଏହି ସପ୍ତାହନ୍ତରେ ${activeCityName} ର ପାଣିପାଗ କିପରି ରହିବ?`
  ] : isHi ? [
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
      setAudioLevel(0);
      return;
    }

    startListening();

    return () => {
      cleanupAudio();
    };
  }, [isVoiceOpen, currentLanguage?.code, useHardwareMic]);

  const cleanupAudio = () => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
      recognitionRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (e) {}
      mediaRecorderRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try { audioContextRef.current.close(); } catch (e) {}
      audioContextRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  const startListening = async () => {
    cleanupAudio();
    setIsRecording(true);
    setTranscript('');
    setMicStatus('Listening... Speak now');

    // Option A: Direct Python Device Hardware Mic
    if (useHardwareMic) {
      setMicStatus('Listening via Device Hardware Mic (Python VAD)...');
      setIsTranscribing(true);
      try {
        const langMap = {
          en: 'en-IN',
          hi: 'hi-IN',
          or: 'or-IN',
          te: 'te-IN',
          ta: 'ta-IN',
          bn: 'bn-IN',
          mr: 'mr-IN',
          gu: 'gu-IN',
          kn: 'kn-IN',
          ml: 'ml-IN',
          pa: 'pa-IN'
        };
        const lang = langMap[currentLanguage?.code] || 'en-IN';
        const res = await listenDeviceMicApi({
          language: lang,
          locationName: currentCity?.name || 'Jatani'
        });

        if (res && res.transcript) {
          setTranscript(res.transcript);
          setMicStatus('Speech captured!');
        } else {
          setMicStatus('No speech detected. Tap mic to retry.');
        }
      } catch (err) {
        console.warn('Hardware mic error:', err);
        setMicStatus('Mic capture error.');
      }
      setIsTranscribing(false);
      return;
    }

    // Option B: Standard Browser Web Speech & AudioContext Wave Analyzer
    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        streamRef.current = stream;

        // Visual Audio Wave Analyzer
        try {
          const AudioContext = window.AudioContext || window.webkitAudioContext;
          if (AudioContext) {
            const audioCtx = new AudioContext();
            audioContextRef.current = audioCtx;
            const source = audioCtx.createMediaStreamSource(stream);
            const analyser = audioCtx.createAnalyser();
            analyser.fftSize = 64;
            source.connect(analyser);
            analyserRef.current = analyser;

            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);

            const updateMeter = () => {
              if (!analyserRef.current) return;
              analyserRef.current.getByteFrequencyData(dataArray);
              let sum = 0;
              for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
              }
              const avg = sum / bufferLength;
              setAudioLevel(Math.min(100, Math.round(avg * 1.5)));
              animationFrameRef.current = requestAnimationFrame(updateMeter);
            };
            updateMeter();
          }
        } catch (e) {
          console.warn('AudioContext Visualizer notice:', e);
        }

        // MediaRecorder backup
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
      console.warn('Microphone stream access error:', err);
      setMicStatus('Microphone permission required.');
    }

    // Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        const langMap = {
          en: 'en-IN',
          hi: 'hi-IN',
          or: 'or-IN',
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
            setMicStatus('Listening...');
          }
        };

        recognition.onerror = (e) => {
          if (e.error !== 'no-speech') {
            console.warn('SpeechRecognition notice:', e.error);
          }
        };

        recognition.onend = () => {
          // If still recording, restart
          if (isRecording && recognitionRef.current) {
            try { recognition.start(); } catch (e) {}
          }
        };

        recognition.start();
        recognitionRef.current = recognition;
      } catch (err) {
        console.warn('SpeechRecognition initialization error:', err);
      }
    }
  };

  const handleMicToggle = () => {
    if (isRecording) {
      // If currently listening, stop recording and keep current transcript without auto-submitting
      cleanupAudio();
      setIsRecording(false);
      setMicStatus(transcript.trim() ? 'Listening stopped. Tap Ask & Speak to send, or Mic to record again.' : 'Mic paused. Tap Mic to speak.');
    } else {
      startListening();
    }
  };

  const handleResetMic = () => {
    cleanupAudio();
    setTranscript('');
    setIsTranscribing(false);
    setAudioLevel(0);
    startListening();
    if (showToast) {
      showToast('Microphone reset. Speak now.', 'info');
    }
  };

  const stopAndSubmit = async (customQuery = null) => {
    let finalQuery = customQuery || transcript.trim();

    // If no text captured yet, attempt backend speech-to-text with audio chunks
    if (!finalQuery && audioChunksRef.current.length > 0) {
      setIsTranscribing(true);
      setMicStatus('Transcribing speech via AI...');
      try {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const backendTranscript = await transcribeAudio(audioBlob, currentLanguage?.code || 'auto');
        if (backendTranscript && backendTranscript.trim()) {
          finalQuery = backendTranscript.trim();
        }
      } catch (e) {
        console.warn('Audio transcription fallback error:', e);
      }
      setIsTranscribing(false);
    }

    if (!finalQuery) {
      setMicStatus('No speech detected yet. Speak clearly or select a prompt below.');
      if (showToast) {
        showToast('Please speak into the mic or select a prompt below.', 'warning');
      }
      return;
    }

    cleanupAudio();
    setIsRecording(false);
    setIsVoiceOpen(false);
    setActiveTab('assistant');

    // Send chat query with autoPlayVoice=true so AI automatically speaks response out loud
    sendChatMessage(finalQuery, true);
  };

  if (!isVoiceOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fadeIn">
      <div className="bg-surface rounded-3xl border border-outline-variant/20 shadow-2xl max-w-md w-full p-6 sm:p-8 flex flex-col items-center text-center space-y-5">
        
        {/* Language selector & Hardware toggle header */}
        <div className="w-full flex justify-between items-center text-xs text-on-surface-variant border-b border-outline-variant/10 pb-3">
          <span className="font-label-caps uppercase font-bold text-primary flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${isRecording ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`}></span>
            Voice Intelligence
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setUseHardwareMic(!useHardwareMic)}
              className={`text-[11px] px-2 py-0.5 rounded-full border transition-all cursor-pointer font-medium ${
                useHardwareMic
                  ? 'bg-primary/20 border-primary text-primary font-bold'
                  : 'bg-surface-container border-outline-variant/20 text-on-surface-variant hover:text-on-surface'
              }`}
              title="Toggle between Browser Web Audio and Python Device Hardware Mic"
            >
              {useHardwareMic ? '🎙️ Device Mic' : '🌐 Web Mic'}
            </button>
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
        </div>

        {/* Pulsing Mic Visualizer Button & Reset Control */}
        <div className="relative my-2 flex items-center justify-center">
          {isRecording && (
            <>
              <span
                className="absolute rounded-full bg-primary/20 transition-all duration-100 pointer-events-none"
                style={{
                  width: `${80 + audioLevel * 0.8}px`,
                  height: `${80 + audioLevel * 0.8}px`
                }}
              ></span>
              <span
                className="absolute rounded-full bg-primary/30 transition-all duration-100 pointer-events-none"
                style={{
                  width: `${95 + audioLevel * 1.2}px`,
                  height: `${95 + audioLevel * 1.2}px`
                }}
              ></span>
            </>
          )}
          <button
            type="button"
            onClick={handleMicToggle}
            className={`relative w-20 h-20 rounded-full flex items-center justify-center text-white shadow-2xl transition-all active:scale-95 cursor-pointer z-10 ${
              isRecording 
                ? 'bg-primary border-4 border-white shadow-primary/40 animate-pulse' 
                : 'bg-slate-700 border-4 border-slate-500 hover:bg-slate-600'
            }`}
            title={isRecording ? 'Tap to pause/stop listening' : 'Tap to start listening'}
          >
            <span className="material-symbols-outlined text-3xl">
              {isRecording ? 'mic' : 'mic_none'}
            </span>
          </button>

          {/* Dedicated Reset Mic Button */}
          <button
            type="button"
            onClick={handleResetMic}
            className="absolute -right-12 top-1/2 -translate-y-1/2 p-2 rounded-full bg-surface-container border border-outline-variant/30 text-on-surface-variant hover:text-primary hover:border-primary/50 transition-all cursor-pointer shadow-md"
            title="Reset Microphone & Restart Listening"
          >
            <span className="material-symbols-outlined text-lg">refresh</span>
          </button>
        </div>

        {/* Live Audio Meter & Status */}
        <div className="w-full">
          <div className="flex items-center justify-center gap-2 mb-1">
            <span className="font-label-caps text-xs font-bold text-primary tracking-wider uppercase block">
              {isTranscribing ? 'Processing Speech AI...' : micStatus}
            </span>
            {transcript && (
              <button
                type="button"
                onClick={() => setTranscript('')}
                className="text-[10px] text-on-surface-variant/60 hover:text-error underline cursor-pointer"
                title="Clear transcript text"
              >
                Clear
              </button>
            )}
          </div>
          
          <div className="min-h-[64px] max-h-[110px] overflow-y-auto bg-surface-container-low/60 rounded-2xl p-3.5 border border-outline-variant/15 flex items-center justify-center text-left">
            <p className="font-body-md text-sm font-semibold text-on-surface leading-relaxed w-full">
              {transcript ? (
                <span className="text-primary font-bold">"{transcript}"</span>
              ) : (
                <span className="text-on-surface-variant/60 italic text-xs font-normal">
                  Speak clearly into your microphone in {currentLanguage?.name || 'English'}...
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
                className="text-xs bg-surface-container border border-outline-variant/20 rounded-full px-3 py-1.5 text-on-surface hover:bg-primary hover:text-white transition-all cursor-pointer text-left font-medium"
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
            disabled={!transcript.trim() && !isRecording}
            className={`flex-1 py-2.5 rounded-full text-white text-xs font-bold shadow-md transition-all active:scale-95 cursor-pointer flex items-center justify-center gap-1.5 ${
              transcript.trim() || isRecording
                ? 'bg-primary hover:bg-primary/90'
                : 'bg-slate-600 opacity-60 cursor-not-allowed'
            }`}
          >
            <span>Ask & Speak</span>
            <span className="material-symbols-outlined text-sm">volume_up</span>
          </button>
        </div>
      </div>
    </div>
  );
}

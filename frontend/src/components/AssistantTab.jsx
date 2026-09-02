import React, { useState, useRef, useEffect } from 'react';
import { useWeather } from '../context/WeatherContext';
import { useAuth } from '../context/AuthContext';

export default function AssistantTab() {
  const {
    chatMessages,
    setChatMessages,
    isTyping,
    sendChatMessage,
    toggleAudioSpeech,
    handleFeedback,
    regenerateAiResponse,
    clearChatHistory,
    setIsVoiceOpen,
    currentCity,
    currentLanguage,
    showToast,
    t
  } = useWeather();

  const {
    user,
    isGuest,
    openAuthModal,
    setIsHistoryDrawerOpen,
    startNewChat,
    activeConversationId
  } = useAuth();

  const [inputText, setInputText] = useState('');
  const [isListeningInline, setIsListeningInline] = useState(false);
  const messagesEndRef = useRef(null);
  const inlineRecognitionRef = useRef(null);

  const isHi = currentLanguage?.code === 'hi';
  const cityName = currentCity?.name && currentCity.name !== 'Select Location' ? currentCity.name : (isHi ? 'मेरे शहर' : 'my city');

  const suggestedQuestions = isHi ? [
    `☔ क्या आज ${cityName} में बारिश होगी? क्या छाता साथ रखें?`,
    `🚗 क्या अभी ${cityName} में बाहर निकलना या ड्राइव करना सुरक्षित है?`,
    `🏃 आज ${cityName} में वॉक या कसरत के लिए सबसे अच्छा समय क्या है?`,
    `👕 आज के मौसम के हिसाब से क्या पहनना सही रहेगा?`,
    `📅 इस वीकेंड ${cityName} में मौसम कैसा रहेगा?`,
    `🌾 क्या आज ${cityName} में पौधों या फसलों को पानी देना सही है?`
  ] : [
    `☔ Will it rain today in ${cityName}? Should I carry an umbrella?`,
    `🚗 Is it safe to drive or commute right now in ${cityName}?`,
    `🏃 Best time for a walk or outdoor workout in ${cityName} today?`,
    `👕 What should I wear today based on the temperature & weather?`,
    `📅 What is the weekend weather outlook for ${cityName}?`,
    `🌾 Is today a good day for gardening or outdoor watering?`
  ];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isTyping]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!inputText.trim()) return;
    if (inlineRecognitionRef.current) {
      try { inlineRecognitionRef.current.stop(); } catch (err) {}
      setIsListeningInline(false);
    }
    sendChatMessage(inputText);
    setInputText('');
  };

  const handleStartNewChat = () => {
    startNewChat();
    clearChatHistory();
    sessionStorage.removeItem('weathergpt_active_conv_id');
    showToast('Started new conversation');
  };

  const copyTextToClipboard = (text) => {
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      showToast('AI response copied to clipboard');
    }
  };

  const handleMicClick = () => {
    setIsVoiceOpen(true);
  };

  return (
    <main className="flex-grow flex flex-col max-w-3xl mx-auto w-full px-container-padding-mobile md:px-0 pt-8 pb-32 md:pb-12 space-y-6">
      {/* Top action header for assistant */}
      <div className="flex items-center justify-between border-b border-outline-variant/10 pb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-label-caps text-xs text-on-surface font-bold uppercase tracking-wider">
            WeatherGPT Intelligence · {currentCity.name}
          </span>
          {user ? (
            <span className="text-[10px] bg-primary/10 text-primary border border-primary/20 px-2 py-0.5 rounded-full font-medium">
              Saved Session
            </span>
          ) : (
            <span className="text-[10px] bg-secondary-container/40 text-on-surface-variant border border-outline-variant/20 px-2 py-0.5 rounded-full font-medium">
              Guest Mode
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsHistoryDrawerOpen(true)}
            className="text-xs text-on-surface-variant hover:text-primary transition-colors flex items-center gap-1 font-medium cursor-pointer"
            title="Open Assistant History Drawer"
          >
            <span className="material-symbols-outlined text-sm">history</span>
            <span>History</span>
          </button>

          {chatMessages.length > 0 && (
            <button
              onClick={handleStartNewChat}
              className="text-xs text-primary hover:text-primary/80 transition-colors flex items-center gap-1 font-semibold cursor-pointer"
              title="Start a new chat thread"
            >
              <span className="material-symbols-outlined text-sm">add_comment</span>
              <span>New Chat</span>
            </button>
          )}

          {chatMessages.length > 0 && (
            <button
              onClick={clearChatHistory}
              className="text-xs text-on-surface-variant hover:text-error transition-colors flex items-center gap-1 font-medium cursor-pointer"
            >
              <span className="material-symbols-outlined text-sm">delete_sweep</span>
              {t('clearChat')}
            </button>
          )}
        </div>
      </div>


      {/* Chat Messages Timeline */}
      <div className="flex-grow flex flex-col space-y-6 overflow-y-auto mb-8 scrollbar-hide">
        {/* Empty State Intro */}
        {chatMessages.length === 0 && (
          <div className="text-center my-12 space-y-3">
            <div className="w-16 h-16 rounded-full bg-primary-container/10 flex items-center justify-center mx-auto mb-4 border border-primary-container/20">
              <span className="material-symbols-outlined text-3xl text-primary">auto_awesome</span>
            </div>
            <h1 className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface font-medium">
              {currentLanguage?.code === 'hi' ? 'WeatherGPT आपकी क्या मदद कर सकता है?' : 'How can WeatherGPT help?'}
            </h1>
            <p className="font-body-md text-sm text-on-surface-variant max-w-md mx-auto leading-relaxed">
              {t('assistantSub')}
            </p>
          </div>
        )}

        {/* Message Items */}
        {chatMessages.map(msg => (
          <div
            key={msg.id}
            className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start gap-4'}`}
          >
            {msg.sender === 'ai' && (
              <div className="mt-1 flex-shrink-0">
                <div className="w-9 h-9 rounded-full bg-primary-container/10 flex items-center justify-center border border-primary-container/20 shadow-sm">
                  <span className="material-symbols-outlined text-primary text-base">auto_awesome</span>
                </div>
              </div>
            )}

            <div className={`flex flex-col gap-3 ${msg.sender === 'user' ? 'max-w-[85%]' : 'max-w-[90%]'}`}>
              {/* Bubble Body */}
              <div
                className={`px-6 py-4.5 rounded-2xl border shadow-sm relative group ${
                  msg.sender === 'user'
                    ? 'bg-primary text-white rounded-tr-sm border-primary'
                    : 'bg-surface text-on-surface border-outline-variant/20 rounded-tl-sm'
                }`}
              >
                <div className="font-body-md text-sm leading-relaxed whitespace-pre-wrap">
                  {msg.text}
                </div>

                {/* AI Response Tools */}
                {msg.sender === 'ai' && (
                  <div className="mt-4 pt-3 border-t border-outline-variant/10 flex items-center justify-between text-xs text-on-surface-variant">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleAudioSpeech(msg.id)}
                        className={`flex items-center gap-1 font-medium transition-colors cursor-pointer ${
                          msg.isAudioPlaying ? 'text-primary font-bold animate-pulse' : 'hover:text-primary'
                        }`}
                        title="Read aloud in regional neural voice"
                      >
                        <span className="material-symbols-outlined text-sm">
                          {msg.isAudioPlaying ? 'volume_up' : 'volume_mute'}
                        </span>
                        <span>{msg.isAudioPlaying ? 'Playing' : 'Listen'}</span>
                      </button>

                      <button
                        onClick={() => copyTextToClipboard(msg.text)}
                        className="hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
                        title="Copy to clipboard"
                      >
                        <span className="material-symbols-outlined text-sm">content_copy</span>
                        <span>Copy</span>
                      </button>

                      <button
                        onClick={() => regenerateAiResponse(msg.id)}
                        className="hover:text-primary transition-colors flex items-center gap-1 cursor-pointer"
                        title="Regenerate answer"
                      >
                        <span className="material-symbols-outlined text-sm">refresh</span>
                        <span>Retry</span>
                      </button>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleFeedback(msg.id, 'up')}
                        className={`p-1 rounded hover:bg-surface-container transition-colors cursor-pointer ${
                          msg.feedback === 'up' ? 'text-emerald-600 font-bold' : 'text-on-surface-variant/60'
                        }`}
                        title="Helpful"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: msg.feedback === 'up' ? "'FILL' 1" : "'FILL' 0" }}>
                          thumb_up
                        </span>
                      </button>
                      <button
                        onClick={() => handleFeedback(msg.id, 'down')}
                        className={`p-1 rounded hover:bg-surface-container transition-colors cursor-pointer ${
                          msg.feedback === 'down' ? 'text-error font-bold' : 'text-on-surface-variant/60'
                        }`}
                        title="Not helpful"
                      >
                        <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: msg.feedback === 'down' ? "'FILL' 1" : "'FILL' 0" }}>
                          thumb_down
                        </span>
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Rich Inline Action Card */}
              {msg.actionCard && (
                <div className="bg-surface border border-outline-variant/20 rounded-2xl p-5 shadow-sm flex flex-col gap-3 w-full sm:w-80 border-l-4 border-l-primary animate-fadeIn">
                  <div className="flex items-center justify-between border-b border-outline-variant/10 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="material-symbols-outlined text-primary text-sm">{msg.actionCard.icon}</span>
                      <span className="font-label-caps text-[10px] text-on-surface-variant tracking-wider uppercase font-bold">{msg.actionCard.badge}</span>
                    </div>
                    <span className="font-body-md text-sm font-bold text-primary">{msg.actionCard.metric}</span>
                  </div>
                  <div>
                    <p className="font-headline-md text-base font-semibold text-on-surface mb-1">{msg.actionCard.title}</p>
                    <p className="font-body-md text-xs text-on-surface-variant leading-relaxed">{msg.actionCard.subtitle}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator state */}
        {isTyping && (
          <div className="flex justify-start gap-4 animate-fadeIn">
            <div className="w-9 h-9 rounded-full bg-primary-container/10 flex items-center justify-center border border-primary-container/20">
              <span className="material-symbols-outlined text-primary text-base animate-spin">auto_awesome</span>
            </div>
            <div className="bg-surface border border-outline-variant/20 px-5 py-4 rounded-2xl text-on-surface-variant text-xs flex items-center gap-2 shadow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 rounded-full bg-primary animate-bounce [animation-delay:0.4s]"></span>
              <span className="ml-2 font-medium">MausamVani AI is synthesizing meteorological telemetry...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Follow-up Prompts */}
      <div className="space-y-2">
        <span className="text-[10px] text-on-surface-variant uppercase tracking-wider block font-label-caps">
          {isHi ? 'सुझाए गए प्रश्न' : 'Suggested Queries'}
        </span>
        <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {suggestedQuestions.map((q, idx) => (
            <button
              key={idx}
              onClick={() => sendChatMessage(q)}
              className="flex-shrink-0 bg-surface border border-outline-variant/20 rounded-full px-4 py-2 font-label-caps text-xs text-on-surface-variant hover:bg-surface-container-low hover:text-primary transition-all cursor-pointer shadow-sm active:scale-95"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input Area Form */}
      <div className="fixed md:sticky bottom-[88px] md:bottom-8 left-0 right-0 w-full px-container-padding-mobile md:px-0 max-w-3xl mx-auto z-30">
        <form onSubmit={handleSubmit} className="relative bg-surface rounded-2xl border border-outline-variant/30 shadow-xl overflow-hidden focus-within:border-primary/60 focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder={isListeningInline ? (currentLanguage?.code === 'hi' ? 'माइक से सुन रहे हैं...' : 'Listening to your microphone...') : (currentLanguage?.code === 'hi' ? `${currentCity?.name || 'मौसम'} के बारे में पूछें...` : `Ask WeatherGPT about ${currentCity?.name || 'weather'}...`)}
            className="w-full bg-transparent border-none px-6 py-5 font-body-md text-sm text-on-surface placeholder:text-on-surface-variant/50 focus:ring-0 focus:outline-none pr-28"
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
            <button
              type="button"
              onClick={handleMicClick}
              className={`p-2.5 rounded-full transition-all cursor-pointer ${
                isListeningInline 
                  ? 'bg-red-500 text-white animate-pulse shadow-md' 
                  : 'text-on-surface-variant hover:text-primary hover:bg-surface-container'
              }`}
              title={isListeningInline ? 'Listening... Click to stop' : 'Click to speak via Microphone'}
            >
              <span className="material-symbols-outlined text-xl">
                {isListeningInline ? 'mic' : 'mic_none'}
              </span>
            </button>
            <button
              type="submit"
              disabled={!inputText.trim()}
              className="p-2.5 text-white bg-primary disabled:opacity-40 rounded-full hover:bg-primary/90 transition-all active:scale-95 shadow-md font-bold cursor-pointer"
              title="Send Message"
            >
              <span className="material-symbols-outlined text-xl">arrow_upward</span>
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

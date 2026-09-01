import React, { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWeather } from '../context/WeatherContext';

export default function AssistantHistoryDrawer() {
  const {
    user,
    isGuest,
    conversations,
    activeConversationId,
    setActiveConversationId,
    isHistoryDrawerOpen,
    setIsHistoryDrawerOpen,
    isLoadingHistory,
    loadHistory,
    loadConversation,
    startNewChat,
    deleteConversation,
    openAuthModal
  } = useAuth();

  const { setChatMessages, showToast } = useWeather();

  useEffect(() => {
    if (isHistoryDrawerOpen && user) {
      loadHistory();
    }
  }, [isHistoryDrawerOpen, user]);

  if (!isHistoryDrawerOpen) return null;

  // Group conversations by date: Today, Yesterday, Previous 7 Days, Older
  const groupConversations = () => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const groups = {
      Today: [],
      Yesterday: [],
      'Previous 7 Days': [],
      Older: []
    };

    conversations.forEach(conv => {
      const convDate = new Date(conv.updated_at || conv.created_at);
      if (convDate >= today) {
        groups.Today.push(conv);
      } else if (convDate >= yesterday) {
        groups.Yesterday.push(conv);
      } else if (convDate >= sevenDaysAgo) {
        groups['Previous 7 Days'].push(conv);
      } else {
        groups.Older.push(conv);
      }
    });

    return groups;
  };

  const grouped = groupConversations();

  const handleSelectConversation = async (convId) => {
    const details = await loadConversation(convId);
    if (details && details.messages) {
      // Transform stored messages into WeatherContext format
      const formatted = details.messages.map(m => ({
        id: m.id,
        sender: m.role === 'user' ? 'user' : 'ai',
        text: m.content,
        actionCard: m.metadata?.action_card || null,
        detectedLanguage: m.metadata?.detected_language || null,
        audioOutputFile: m.metadata?.audio_output_file || null,
        timestamp: m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
        isAudioPlaying: false,
        feedback: null
      }));
      setChatMessages(formatted);
      setIsHistoryDrawerOpen(false);
      showToast(`Loaded: ${details.title}`);
    }
  };

  const handleNewChat = () => {
    startNewChat();
    setChatMessages([]);
    setIsHistoryDrawerOpen(false);
    showToast('Started new conversation');
  };

  const handleDelete = async (e, convId) => {
    e.stopPropagation();
    if (window.confirm('Delete this conversation from your history?')) {
      const ok = await deleteConversation(convId);
      if (ok) {
        showToast('Conversation deleted');
      }
    }
  };

  return (
    <div className="fixed inset-0 z-[90] flex justify-end bg-black/50 backdrop-blur-sm animate-fadeIn">
      {/* Backdrop click to dismiss */}
      <div className="flex-grow" onClick={() => setIsHistoryDrawerOpen(false)} />

      {/* Drawer Body */}
      <div className="w-full max-w-sm sm:max-w-md h-full bg-surface text-on-surface border-l border-outline-variant/20 shadow-2xl flex flex-col justify-between overflow-hidden animate-slideLeft">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-outline-variant/15 flex items-center justify-between bg-surface-container/30">
          <div className="flex items-center gap-2.5">
            <span className="material-symbols-outlined text-primary text-xl">history</span>
            <div>
              <h3 className="font-headline-sm text-base font-bold text-on-surface">
                Assistant History
              </h3>
              <p className="text-[11px] text-on-surface-variant">
                {user ? `${user.email}` : 'Guest Session'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {user && (
              <button
                onClick={handleNewChat}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-primary/10 hover:bg-primary/20 text-primary text-xs font-semibold transition-all cursor-pointer"
                title="Start a new chat thread"
              >
                <span className="material-symbols-outlined text-sm">add</span>
                <span>New Chat</span>
              </button>
            )}
            <button
              onClick={() => setIsHistoryDrawerOpen(false)}
              className="text-on-surface-variant hover:text-on-surface p-1.5 rounded-full hover:bg-surface-container transition-colors cursor-pointer"
              title="Close drawer"
            >
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-grow overflow-y-auto p-4 space-y-6 scrollbar-hide">
          {/* GUEST NOTICE */}
          {isGuest && (
            <div className="p-5 rounded-2xl bg-secondary-container/20 border border-secondary-container/40 text-center space-y-3 my-6">
              <div className="w-12 h-12 rounded-full bg-secondary/10 text-secondary flex items-center justify-center mx-auto">
                <span className="material-symbols-outlined text-2xl">lock_person</span>
              </div>
              <h4 className="text-sm font-bold text-on-surface">
                History is disabled for Guests
              </h4>
              <p className="text-xs text-on-surface-variant leading-relaxed">
                You can use all WeatherGPT assistant and forecast features in guest mode, but your chat sessions will not be saved permanently.
              </p>
              <button
                onClick={() => {
                  setIsHistoryDrawerOpen(false);
                  openAuthModal('register');
                }}
                className="w-full py-2.5 rounded-xl bg-primary text-on-primary font-medium text-xs uppercase tracking-wider shadow hover:bg-primary/90 transition-all cursor-pointer"
              >
                Sign In to Save History
              </button>
            </div>
          )}

          {/* AUTHENTICATED USER HISTORY LIST */}
          {user && (
            <>
              {isLoadingHistory ? (
                <div className="text-center py-12 text-on-surface-variant text-xs flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                  <span>Loading conversations...</span>
                </div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-16 space-y-2 text-on-surface-variant">
                  <span className="material-symbols-outlined text-4xl text-on-surface-variant/40">
                    chat_bubble_outline
                  </span>
                  <div className="text-sm font-medium text-on-surface">No saved conversations yet</div>
                  <div className="text-xs">Ask WeatherGPT a question to start your history.</div>
                </div>
              ) : (
                Object.entries(grouped).map(([groupTitle, convList]) => {
                  if (convList.length === 0) return null;
                  return (
                    <div key={groupTitle} className="space-y-2">
                      <div className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant/70 px-2">
                        {groupTitle}
                      </div>
                      <div className="space-y-1.5">
                        {convList.map(conv => {
                          const isActive = activeConversationId === conv.id;
                          return (
                            <div
                              key={conv.id}
                              onClick={() => handleSelectConversation(conv.id)}
                              className={`group flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer text-left ${
                                isActive
                                  ? 'bg-primary/15 border-primary/40 text-primary font-semibold'
                                  : 'bg-surface-container/40 hover:bg-surface-container border-outline-variant/15 text-on-surface'
                              }`}
                            >
                              <div className="flex items-center gap-2.5 min-w-0 flex-1 pr-2">
                                <span className="material-symbols-outlined text-base flex-shrink-0 opacity-70">
                                  chat
                                </span>
                                <div className="min-w-0 flex-1">
                                  <div className="text-xs font-medium truncate">
                                    {conv.title || 'Weather Conversation'}
                                  </div>
                                  {conv.last_message && (
                                    <div className="text-[10px] text-on-surface-variant truncate opacity-80">
                                      {conv.last_message}
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="flex items-center gap-1.5 flex-shrink-0">
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface-container-highest/60 text-on-surface-variant font-mono">
                                  {conv.message_count || 0}
                                </span>
                                <button
                                  onClick={(e) => handleDelete(e, conv.id)}
                                  className="opacity-0 group-hover:opacity-100 p-1 text-on-surface-variant hover:text-error hover:bg-error-container/20 rounded transition-all cursor-pointer"
                                  title="Delete conversation"
                                >
                                  <span className="material-symbols-outlined text-sm">delete</span>
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-outline-variant/15 bg-surface-container/30 text-xs text-on-surface-variant flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            <span>MongoDB Database Connected</span>
          </div>
          <span className="text-[10px] uppercase font-mono">v1.0.0</span>
        </div>

      </div>
    </div>
  );
}

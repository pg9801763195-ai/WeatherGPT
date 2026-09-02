import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  loginApi,
  logoutApi,
  directRegisterApi,
  googleLoginApi,
  requestOtpApi,
  verifyOtpApi,
  setPasswordApi,
  fetchCurrentUserApi,
  fetchAssistantHistoryApi,
  fetchConversationDetailsApi,
  createConversationApi,
  deleteConversationApi
} from '../services/aiAgentService';

const AuthContext = createContext();

const TOKEN_STORAGE_KEY = 'weathergpt_auth_token';

export function AuthProvider({ children }) {
  // Authentication State
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem(TOKEN_STORAGE_KEY) || null;
    } catch {
      return null;
    }
  });
  const [user, setUser] = useState(null); // null = Guest Mode (Default)
  const [isLoadingAuth, setIsLoadingAuth] = useState(true);

  // Modal State
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalView, setAuthModalView] = useState('choice'); // 'choice' | 'register' | 'login'

  // Assistant History State
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  /**
   * Check current authentication status on initial app load
   */
  const checkAuthStatus = useCallback(async () => {
    if (!token) {
      setUser(null);
      setIsLoadingAuth(false);
      return;
    }
    try {
      const currentUser = await fetchCurrentUserApi(token);
      if (currentUser) {
        setUser(currentUser);
        // Load user's assistant history
        loadHistory(token);
      } else {
        // Token expired or invalid -> Clean up and reset to Guest
        setUser(null);
        setToken(null);
        try {
          localStorage.removeItem(TOKEN_STORAGE_KEY);
        } catch {}
      }
    } catch (e) {
      console.warn('Auth check error, defaulting to Guest mode:', e);
      setUser(null);
    } finally {
      setIsLoadingAuth(false);
    }
  }, [token]);

  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  /**
   * Modal Open/Close Controls
   */
  const openAuthModal = (view = 'choice') => {
    setAuthModalView(view);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
    setAuthModalView('choice');
  };

  /**
   * Direct 1-Click Registration (Email + Password + Name, No OTP)
   */
  const register = async ({ name, email, password }) => {
    const res = await directRegisterApi({ name, email, password });
    if (res && res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      try {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.token);
      } catch {}
      closeAuthModal();
      loadHistory(res.token);
      return res.user;
    }
    return null;
  };

  /**
   * Google OAuth Login & Registration
   */
  const loginWithGoogle = async (googleData) => {
    const res = await googleLoginApi(googleData);
    if (res && res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      try {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.token);
      } catch {}
      closeAuthModal();
      loadHistory(res.token);
      return res.user;
    }
    return null;
  };

  /**
   * Step 1: Request OTP
   */
  const requestOtp = async (email) => {
    return await requestOtpApi(email);
  };

  /**
   * Step 2: Verify OTP
   */
  const verifyOtp = async (email, otp) => {
    return await verifyOtpApi(email, otp);
  };

  /**
   * Step 3: Set Password & Create Account
   */
  const setPasswordAndRegister = async ({ email, verificationToken, password, name }) => {
    const res = await setPasswordApi({ email, verificationToken, password, name });
    if (res && res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      try {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.token);
      } catch {}
      closeAuthModal();
      loadHistory(res.token);
      return res.user;
    }
    return null;
  };

  /**
   * Login
   */
  const login = async (email, password) => {
    const res = await loginApi(email, password);
    if (res && res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      try {
        localStorage.setItem(TOKEN_STORAGE_KEY, res.token);
      } catch {}
      closeAuthModal();
      loadHistory(res.token);
      return res.user;
    }
    return null;
  };

  /**
   * Logout
   */
  const logout = async () => {
    await logoutApi();
    setUser(null);
    setToken(null);
    setConversations([]);
    setActiveConversationId(null);
    setIsHistoryDrawerOpen(false);
    try {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    } catch {}
  };

  /**
   * Assistant History Operations
   */
  const loadHistory = async (activeToken = token) => {
    if (!activeToken) {
      setConversations([]);
      return;
    }
    setIsLoadingHistory(true);
    try {
      const historyList = await fetchAssistantHistoryApi(activeToken);
      setConversations(historyList || []);
    } catch (e) {
      console.warn('Failed to load assistant history:', e);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const loadConversation = async (conversationId) => {
    if (!token || !conversationId) return null;
    try {
      const details = await fetchConversationDetailsApi(conversationId, token);
      if (details) {
        setActiveConversationId(conversationId);
        return details;
      }
      return null;
    } catch (e) {
      console.warn('Failed to load conversation:', e);
      return null;
    }
  };

  const startNewChat = () => {
    setActiveConversationId(null);
  };

  const deleteConversation = async (conversationId) => {
    if (!token || !conversationId) return false;
    try {
      const success = await deleteConversationApi(conversationId, token);
      if (success) {
        setConversations(prev => prev.filter(c => c.id !== conversationId));
        if (activeConversationId === conversationId) {
          setActiveConversationId(null);
        }
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Failed to delete conversation:', e);
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isGuest: !user,
        isLoadingAuth,
        isAuthModalOpen,
        authModalView,
        setAuthModalView,
        openAuthModal,
        closeAuthModal,
        requestOtp,
        verifyOtp,
        setPasswordAndRegister,
        register,
        loginWithGoogle,
        login,
        logout,
        conversations,
        setConversations,
        activeConversationId,
        setActiveConversationId,
        isHistoryDrawerOpen,
        setIsHistoryDrawerOpen,
        isLoadingHistory,
        loadHistory,
        loadConversation,
        startNewChat,
        deleteConversation
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWeather } from '../context/WeatherContext';

export default function AuthModal() {
  const {
    isAuthModalOpen,
    closeAuthModal,
    authModalView,
    setAuthModalView,
    register,
    loginWithGoogle,
    login
  } = useAuth();

  const { showToast } = useWeather();

  // Active Tab ('login' | 'register')
  const [activeTab, setActiveTab] = useState('login');

  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Status
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Sync modal view state
  useEffect(() => {
    if (isAuthModalOpen) {
      setErrorMsg('');
      setIsLoading(false);
      if (authModalView === 'register') {
        setActiveTab('register');
      } else {
        setActiveTab('login');
      }
    }
  }, [isAuthModalOpen, authModalView]);

  const GOOGLE_CLIENT_ID = '247258135956-7ad7sfrr0an48lorgc19l932bhrook4c.apps.googleusercontent.com';

  // Load and initialize Google Identity Services with real client ID
  useEffect(() => {
    if (typeof window !== 'undefined' && isAuthModalOpen) {
      const setupGsi = () => {
        if (window.google?.accounts?.id) {
          try {
            window.google.accounts.id.initialize({
              client_id: GOOGLE_CLIENT_ID,
              callback: async (response) => {
                try {
                  if (response.credential) {
                    setIsLoading(true);
                    const user = await loginWithGoogle({ credential: response.credential });
                    if (user) showToast(`Welcome, ${user.name || user.email}!`);
                  }
                } catch (err) {
                  setErrorMsg(err.message || 'Google sign-in failed.');
                } finally {
                  setIsLoading(false);
                }
              }
            });

            const btnContainer = document.getElementById('google-btn-slot');
            if (btnContainer) {
              btnContainer.innerHTML = '';
              window.google.accounts.id.renderButton(btnContainer, {
                theme: 'outline',
                size: 'large',
                type: 'standard',
                shape: 'rectangular',
                text: 'continue_with',
                logo_alignment: 'left',
                width: 340
              });
            }
          } catch (e) {
            console.warn('Google GSI init error:', e);
          }
        }
      };

      if (!window.google) {
        const script = document.createElement('script');
        script.src = 'https://accounts.google.com/gsi/client';
        script.async = true;
        script.defer = true;
        script.onload = setupGsi;
        document.body.appendChild(script);
      } else {
        setTimeout(setupGsi, 50);
      }
    }
  }, [isAuthModalOpen, activeTab]);

  if (!isAuthModalOpen) return null;

  // ---------------------------------------------------------------------------
  // Google OAuth Fallback Click Handler
  // ---------------------------------------------------------------------------
  const handleGoogleSignIn = () => {
    setErrorMsg('');
    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt();
    }
  };

  // ---------------------------------------------------------------------------
  // Direct Register Handler (No OTP)
  // ---------------------------------------------------------------------------
  const handleRegister = async (e) => {
    e?.preventDefault();
    if (!email.trim() || !email.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }
    if (password.length < 6) {
      setErrorMsg('Password must be at least 6 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setErrorMsg('Passwords do not match.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      const user = await register({
        name: name.trim() || undefined,
        email: email.trim().toLowerCase(),
        password
      });
      if (user) {
        showToast(`Welcome to WeatherGPT, ${user.name || user.email}!`);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to create account.');
    } finally {
      setIsLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Login Handler
  // ---------------------------------------------------------------------------
  const handleLogin = async (e) => {
    e?.preventDefault();
    if (!email.trim() || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      const user = await login(email.trim().toLowerCase(), password);
      if (user) {
        showToast(`Welcome back, ${user.name || user.email}!`);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Invalid email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[999] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md transition-all animate-fadeIn">
      <div className="relative w-full max-w-md bg-surface text-on-surface rounded-2xl border border-outline-variant/30 shadow-2xl overflow-hidden p-6 sm:p-8">
        
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 text-on-surface-variant/70 hover:text-on-surface p-1.5 rounded-full hover:bg-surface-container transition-colors cursor-pointer"
          title="Close"
        >
          <span className="material-symbols-outlined text-lg">close</span>
        </button>

        {/* Modal Header */}
        <div className="text-center mb-5">
          <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-2 text-primary shadow-sm">
            <span className="material-symbols-outlined text-2xl">
              {activeTab === 'login' ? 'login' : 'person_add'}
            </span>
          </div>
          <h2 className="font-headline-md text-xl font-bold tracking-tight text-on-surface">
            {activeTab === 'login' ? 'Sign In to WeatherGPT' : 'Create an Account'}
          </h2>
          <p className="font-body-sm text-xs text-on-surface-variant mt-1">
            Access atmospheric AI intelligence and persistent conversation history.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-xl bg-surface-container p-1 mb-5 border border-outline-variant/20">
          <button
            type="button"
            onClick={() => {
              setErrorMsg('');
              setActiveTab('login');
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'login'
                ? 'bg-primary text-on-primary shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setErrorMsg('');
              setActiveTab('register');
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'register'
                ? 'bg-primary text-on-primary shadow-sm'
                : 'text-on-surface-variant hover:text-on-surface'
            }`}
          >
            Register
          </button>
        </div>

        {/* Error Alert Box */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-error-container/20 border border-error/30 text-error text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-base flex-shrink-0">error</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Official Google Sign-In Button */}
        <div className="flex justify-center mb-3 min-h-[44px]">
          <div id="google-btn-slot" className="w-full flex justify-center"></div>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-3 my-4">
          <div className="flex-1 h-px bg-outline-variant/20"></div>
          <span className="text-[11px] uppercase tracking-wider text-on-surface-variant/60 font-semibold">
            or with email
          </span>
          <div className="flex-1 h-px bg-outline-variant/20"></div>
        </div>

        {/* ================================================================= */}
        {/* TAB 1: LOGIN FORM                                                 */}
        {/* ================================================================= */}
        {activeTab === 'login' && (
          <form onSubmit={handleLogin} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Email Address
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  mail
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  lock
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full pl-9 pr-9 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-on-surface-variant hover:text-on-surface cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !password}
              className="w-full py-2.5 mt-2 rounded-xl bg-primary text-on-primary font-semibold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <>
                  <span>Sign In</span>
                  <span className="material-symbols-outlined text-sm">login</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* ================================================================= */}
        {/* TAB 2: DIRECT REGISTRATION FORM (No OTP)                          */}
        {/* ================================================================= */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Your Name <span className="text-on-surface-variant/50 font-normal lowercase">(optional)</span>
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  badge
                </span>
                <input
                  type="text"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Priyanshu Gupta"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Email Address
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  mail
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Password <span className="text-on-surface-variant/50 font-normal lowercase">(min 6 chars)</span>
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  lock
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Create a password"
                  required
                  minLength={6}
                  className="w-full pl-9 pr-9 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-2.5 text-on-surface-variant hover:text-on-surface cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">
                    {showPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1 uppercase tracking-wider">
                Confirm Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  check_circle
                </span>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Repeat your password"
                  required
                  minLength={6}
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !email || !password || !confirmPassword}
              className="w-full py-2.5 mt-2 rounded-xl bg-primary text-on-primary font-semibold text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow-lg hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              ) : (
                <>
                  <span>Create Account</span>
                  <span className="material-symbols-outlined text-sm">arrow_forward</span>
                </>
              )}
            </button>
          </form>
        )}

        {/* Footer Guest Mode Link */}
        <div className="mt-5 text-center border-t border-outline-variant/15 pt-3">
          <button
            type="button"
            onClick={closeAuthModal}
            className="text-xs text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
          >
            Skip for now &amp; Continue as Guest →
          </button>
        </div>

      </div>
    </div>
  );
}

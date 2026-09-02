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

  // Load Google Identity Services script
  useEffect(() => {
    if (typeof window !== 'undefined' && !window.google) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.body.appendChild(script);
    }
  }, []);

  if (!isAuthModalOpen) return null;

  // ---------------------------------------------------------------------------
  // Google OAuth Handler
  // ---------------------------------------------------------------------------
  const handleGoogleSignIn = () => {
    setErrorMsg('');
    setIsLoading(true);
    try {
      // Check if official Google GSI is available
      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: '1081395897123-placeholder.apps.googleusercontent.com',
          callback: async (response) => {
            try {
              if (response.credential) {
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
        window.google.accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            // If popup was blocked or client ID not registered, provide quick email prompt for testing
            const testEmail = prompt('Enter your Google Account Email to test Google OAuth:');
            if (testEmail && testEmail.includes('@')) {
              loginWithGoogle({
                email: testEmail.trim().toLowerCase(),
                name: testEmail.split('@')[0],
                picture: `https://api.dicebear.com/7.x/bottts/svg?seed=${testEmail}`
              })
                .then(user => {
                  if (user) showToast(`Welcome, ${user.name || user.email}!`);
                })
                .catch(e => setErrorMsg(e.message))
                .finally(() => setIsLoading(false));
            } else {
              setIsLoading(false);
            }
          }
        });
      } else {
        // Fallback for direct Google email login testing
        const testEmail = prompt('Enter your Google Account Email:');
        if (testEmail && testEmail.includes('@')) {
          loginWithGoogle({
            email: testEmail.trim().toLowerCase(),
            name: testEmail.split('@')[0],
            picture: `https://api.dicebear.com/7.x/bottts/svg?seed=${testEmail}`
          })
            .then(user => {
              if (user) showToast(`Welcome, ${user.name || user.email}!`);
            })
            .catch(e => setErrorMsg(e.message))
            .finally(() => setIsLoading(false));
        } else {
          setIsLoading(false);
        }
      }
    } catch (err) {
      setErrorMsg(err.message || 'Google sign-in error.');
      setIsLoading(false);
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

        {/* Google OAuth Button */}
        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={isLoading}
          className="w-full py-2.5 px-4 rounded-xl border border-outline-variant/30 hover:border-primary/40 bg-surface-container/50 hover:bg-surface-container transition-all cursor-pointer flex items-center justify-center gap-3 text-sm font-medium text-on-surface shadow-sm disabled:opacity-50 mb-4"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Continue with Google</span>
        </button>

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

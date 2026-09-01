import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useWeather } from '../context/WeatherContext';

export default function AuthModal() {
  const {
    isAuthModalOpen,
    closeAuthModal,
    authModalView,
    setAuthModalView,
    requestOtp,
    verifyOtp,
    setPasswordAndRegister,
    login
  } = useAuth();

  const { showToast } = useWeather();

  // Registration Form State
  const [regStep, setRegStep] = useState(1); // 1: Email, 2: OTP, 3: Password
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [verificationToken, setVerificationToken] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  // Login Form State
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [showLoginPassword, setShowLoginPassword] = useState(false);

  // Status & Timers
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);

  // Reset states when modal opens
  useEffect(() => {
    if (isAuthModalOpen) {
      setErrorMsg('');
      setIsLoading(false);
      if (authModalView === 'register') {
        setRegStep(1);
      }
    }
  }, [isAuthModalOpen, authModalView]);

  // Resend OTP Countdown timer
  useEffect(() => {
    let timer;
    if (resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [resendCooldown]);

  if (!isAuthModalOpen) return null;

  // Password validation checklist
  const hasMinLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigitOrSpecial = /[\d\W_]/.test(password);
  const isPasswordValid = hasMinLength && hasUpper && hasLower && hasDigitOrSpecial;
  const passwordsMatch = password && password === confirmPassword;

  // ---------------------------------------------------------------------------
  // Handlers for Registration Flow
  // ---------------------------------------------------------------------------

  const handleRequestOtp = async (e) => {
    e?.preventDefault();
    if (!email.trim() || !email.includes('@')) {
      setErrorMsg('Please enter a valid email address.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      await requestOtp(email.trim());
      setRegStep(2);
      setResendCooldown(30);
      showToast(`Verification code sent to ${email}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to send verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (resendCooldown > 0 || isLoading) return;
    setErrorMsg('');
    setIsLoading(true);
    try {
      await requestOtp(email.trim());
      setResendCooldown(30);
      showToast(`New verification code sent to ${email}`);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to resend verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e?.preventDefault();
    if (!otp.trim() || otp.trim().length < 4) {
      setErrorMsg('Please enter the verification code.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      const res = await verifyOtp(email.trim(), otp.trim());
      if (res && res.verification_token) {
        setVerificationToken(res.verification_token);
        setRegStep(3);
        showToast('Code verified! Please create your password.');
      }
    } catch (err) {
      setErrorMsg(err.message || 'Invalid or expired verification code.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSetPassword = async (e) => {
    e?.preventDefault();
    if (!isPasswordValid) {
      setErrorMsg('Please ensure your password meets all security requirements.');
      return;
    }
    if (!passwordsMatch) {
      setErrorMsg('Passwords do not match.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      const user = await setPasswordAndRegister({
        email: email.trim(),
        verificationToken,
        password,
        name: name.trim() || undefined
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
  // Handler for Login Flow
  // ---------------------------------------------------------------------------

  const handleLogin = async (e) => {
    e?.preventDefault();
    if (!loginEmail.trim() || !loginPassword) {
      setErrorMsg('Please enter both email and password.');
      return;
    }
    setErrorMsg('');
    setIsLoading(true);
    try {
      const user = await login(loginEmail.trim(), loginPassword);
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
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/65 backdrop-blur-sm transition-all animate-fadeIn">
      <div className="relative w-full max-w-md bg-surface text-on-surface rounded-2xl border border-outline-variant/20 shadow-2xl overflow-hidden p-6 sm:p-8">
        
        {/* Close Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-4 right-4 text-on-surface-variant/70 hover:text-on-surface p-1.5 rounded-full hover:bg-surface-container transition-colors cursor-pointer"
          title="Close"
        >
          <span className="material-symbols-outlined text-lg">close</span>
        </button>

        {/* Modal Header */}
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mx-auto mb-3 text-primary shadow-sm">
            <span className="material-symbols-outlined text-2xl">
              {authModalView === 'choice' ? 'account_circle' : authModalView === 'register' ? 'person_add' : 'login'}
            </span>
          </div>
          <h2 className="font-headline-md text-xl font-bold tracking-tight text-on-surface">
            {authModalView === 'choice' && 'Welcome to WeatherGPT'}
            {authModalView === 'register' && (regStep === 1 ? 'Create Account' : regStep === 2 ? 'Verify Email' : 'Set Password')}
            {authModalView === 'login' && 'Sign In to WeatherGPT'}
          </h2>
          <p className="font-body-sm text-xs text-on-surface-variant mt-1 max-w-xs mx-auto">
            {authModalView === 'choice' && 'Experience AI-powered weather forecasting, crop advisories, and persistent conversation history.'}
            {authModalView === 'register' && (regStep === 1 ? 'Enter your email to receive a secure verification code.' : regStep === 2 ? `Enter the 6-digit code sent to ${email}` : 'Choose a strong password to secure your account.')}
            {authModalView === 'login' && 'Enter your credentials to access your saved conversations & settings.'}
          </p>
        </div>

        {/* Error Alert Box */}
        {errorMsg && (
          <div className="mb-4 p-3 rounded-lg bg-error-container/20 border border-error/30 text-error text-xs flex items-center gap-2">
            <span className="material-symbols-outlined text-base flex-shrink-0">error</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {/* ================================================================= */}
        {/* VIEW 1: CHOICE SCREEN (Guest / Register / Login)                  */}
        {/* ================================================================= */}
        {authModalView === 'choice' && (
          <div className="space-y-3">
            {/* Option 1: Continue as Guest */}
            <button
              onClick={closeAuthModal}
              className="w-full flex items-center justify-between p-3.5 rounded-xl border border-outline-variant/20 hover:border-primary/40 bg-surface-container/40 hover:bg-surface-container transition-all cursor-pointer group text-left shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-secondary/10 flex items-center justify-center text-secondary">
                  <span className="material-symbols-outlined text-lg">explore</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-on-surface flex items-center gap-2">
                    Continue as Guest
                    <span className="text-[10px] uppercase tracking-wider font-bold bg-secondary-container/60 text-on-secondary-container px-1.5 py-0.5 rounded">
                      Instant Access
                    </span>
                  </div>
                  <div className="text-[11px] text-on-surface-variant">
                    Full access to weather, forecasts & maps (no saved history).
                  </div>
                </div>
              </div>
              <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary group-hover:translate-x-0.5 transition-all text-sm">
                arrow_forward_ios
              </span>
            </button>

            {/* Option 2: Sign In / Create Account */}
            <button
              onClick={() => {
                setErrorMsg('');
                setAuthModalView('register');
                setRegStep(1);
              }}
              className="w-full flex items-center justify-between p-3.5 rounded-xl border border-primary/30 hover:border-primary bg-primary/10 hover:bg-primary/15 transition-all cursor-pointer group text-left shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-primary/20 flex items-center justify-center text-primary">
                  <span className="material-symbols-outlined text-lg">person_add</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-primary">
                    Sign In / Create Account
                  </div>
                  <div className="text-[11px] text-on-surface-variant">
                    Verify via Email OTP and save permanent chat history.
                  </div>
                </div>
              </div>
              <span className="material-symbols-outlined text-primary group-hover:translate-x-0.5 transition-all text-sm">
                arrow_forward_ios
              </span>
            </button>

            {/* Option 3: Login */}
            <button
              onClick={() => {
                setErrorMsg('');
                setAuthModalView('login');
              }}
              className="w-full flex items-center justify-between p-3.5 rounded-xl border border-outline-variant/20 hover:border-primary/40 bg-surface-container/40 hover:bg-surface-container transition-all cursor-pointer group text-left shadow-sm"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-surface-container flex items-center justify-center text-on-surface-variant">
                  <span className="material-symbols-outlined text-lg">login</span>
                </div>
                <div>
                  <div className="text-sm font-semibold text-on-surface">
                    Login
                  </div>
                  <div className="text-[11px] text-on-surface-variant">
                    Sign in with your registered email and password.
                  </div>
                </div>
              </div>
              <span className="material-symbols-outlined text-on-surface-variant group-hover:text-primary group-hover:translate-x-0.5 transition-all text-sm">
                arrow_forward_ios
              </span>
            </button>
          </div>
        )}

        {/* ================================================================= */}
        {/* VIEW 2: REGISTRATION FLOW (Step 1: Email, Step 2: OTP, Step 3: Pw) */}
        {/* ================================================================= */}
        {authModalView === 'register' && (
          <div>
            {/* Step Progress Bar */}
            <div className="flex items-center justify-center gap-2 mb-6">
              {[1, 2, 3].map(step => (
                <div
                  key={step}
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    regStep === step
                      ? 'w-8 bg-primary'
                      : regStep > step
                      ? 'w-4 bg-primary/50'
                      : 'w-4 bg-surface-container-highest'
                  }`}
                />
              ))}
            </div>

            {/* STEP 1: Enter Email */}
            {regStep === 1 && (
              <form onSubmit={handleRequestOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
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
                      placeholder="you@example.com"
                      required
                      autoFocus
                      className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !email}
                  className="w-full py-2.5 rounded-xl bg-primary text-on-primary font-medium text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <span>Send OTP Code</span>
                      <span className="material-symbols-outlined text-sm">send</span>
                    </>
                  )}
                </button>

                <div className="flex items-center justify-between text-xs pt-2">
                  <button
                    type="button"
                    onClick={() => setAuthModalView('choice')}
                    className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
                  >
                    ← Back
                  </button>
                  <button
                    type="button"
                    onClick={() => setAuthModalView('login')}
                    className="text-primary hover:underline font-medium cursor-pointer"
                  >
                    Already have an account? Login
                  </button>
                </div>
              </form>
            )}

            {/* STEP 2: Enter 6-digit OTP */}
            {regStep === 2 && (
              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
                      6-Digit Verification Code
                    </label>
                    <button
                      type="button"
                      onClick={() => setRegStep(1)}
                      className="text-[11px] text-primary hover:underline cursor-pointer"
                    >
                      Change email
                    </button>
                  </div>

                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
                    placeholder="123456"
                    required
                    autoFocus
                    className="w-full py-3 text-center text-2xl font-bold tracking-[8px] rounded-xl bg-surface-container border border-outline-variant/30 focus:border-primary focus:outline-none text-primary font-mono"
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-on-surface-variant">
                  <span>Code expires in 5 minutes</span>
                  <button
                    type="button"
                    onClick={handleResendOtp}
                    disabled={resendCooldown > 0 || isLoading}
                    className="text-primary hover:underline font-medium disabled:opacity-40 cursor-pointer"
                  >
                    {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : 'Resend OTP'}
                  </button>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || otp.length < 4}
                  className="w-full py-2.5 rounded-xl bg-primary text-on-primary font-medium text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <span>Verify Code</span>
                      <span className="material-symbols-outlined text-sm">check_circle</span>
                    </>
                  )}
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => setRegStep(1)}
                    className="text-xs text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
                  >
                    ← Back to Email
                  </button>
                </div>
              </form>
            )}

            {/* STEP 3: Set Password */}
            {regStep === 3 && (
              <form onSubmit={handleSetPassword} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
                    Full Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={e => setName(e.target.value)}
                    placeholder="e.g. Aryan Sharma"
                    className="w-full px-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
                    Create Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={e => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      autoFocus
                      className="w-full px-3 pr-9 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface font-mono"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(p => !p)}
                      className="absolute right-2.5 top-2.5 text-on-surface-variant hover:text-on-surface text-sm cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-base">
                        {showPassword ? 'visibility_off' : 'visibility'}
                      </span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
                    Confirm Password
                  </label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                    className="w-full px-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface font-mono"
                  />
                </div>

                {/* Password Strength Checklist */}
                <div className="p-3 rounded-xl bg-surface-container/50 border border-outline-variant/10 text-[11px] space-y-1 text-on-surface-variant">
                  <div className="font-semibold text-on-surface mb-1">Password Requirements:</div>
                  <div className={`flex items-center gap-1.5 ${hasMinLength ? 'text-emerald-400' : ''}`}>
                    <span className="material-symbols-outlined text-xs">
                      {hasMinLength ? 'check_circle' : 'radio_button_unchecked'}
                    </span>
                    <span>At least 8 characters</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasUpper ? 'text-emerald-400' : ''}`}>
                    <span className="material-symbols-outlined text-xs">
                      {hasUpper ? 'check_circle' : 'radio_button_unchecked'}
                    </span>
                    <span>At least one uppercase letter (A-Z)</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasLower ? 'text-emerald-400' : ''}`}>
                    <span className="material-symbols-outlined text-xs">
                      {hasLower ? 'check_circle' : 'radio_button_unchecked'}
                    </span>
                    <span>At least one lowercase letter (a-z)</span>
                  </div>
                  <div className={`flex items-center gap-1.5 ${hasDigitOrSpecial ? 'text-emerald-400' : ''}`}>
                    <span className="material-symbols-outlined text-xs">
                      {hasDigitOrSpecial ? 'check_circle' : 'radio_button_unchecked'}
                    </span>
                    <span>At least one number or symbol</span>
                  </div>
                  {confirmPassword && (
                    <div className={`flex items-center gap-1.5 ${passwordsMatch ? 'text-emerald-400' : 'text-error'}`}>
                      <span className="material-symbols-outlined text-xs">
                        {passwordsMatch ? 'check_circle' : 'cancel'}
                      </span>
                      <span>Passwords match</span>
                    </div>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !isPasswordValid || !passwordsMatch}
                  className="w-full py-2.5 rounded-xl bg-primary text-on-primary font-medium text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
                >
                  {isLoading ? (
                    <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  ) : (
                    <>
                      <span>Complete Registration</span>
                      <span className="material-symbols-outlined text-sm">lock_open</span>
                    </>
                  )}
                </button>
              </form>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* VIEW 3: LOGIN FORM                                                */}
        {/* ================================================================= */}
        {authModalView === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  mail
                </span>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={e => setLoginEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  autoFocus
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-on-surface-variant mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3 top-2.5 text-on-surface-variant text-base">
                  lock
                </span>
                <input
                  type={showLoginPassword ? 'text' : 'password'}
                  value={loginPassword}
                  onChange={e => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="w-full pl-9 pr-9 py-2 text-sm rounded-xl bg-surface-container border border-outline-variant/20 focus:border-primary focus:outline-none text-on-surface font-mono"
                />
                <button
                  type="button"
                  onClick={() => setShowLoginPassword(p => !p)}
                  className="absolute right-2.5 top-2.5 text-on-surface-variant hover:text-on-surface text-sm cursor-pointer"
                >
                  <span className="material-symbols-outlined text-base">
                    {showLoginPassword ? 'visibility_off' : 'visibility'}
                  </span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading || !loginEmail || !loginPassword}
              className="w-full py-2.5 rounded-xl bg-primary text-on-primary font-medium text-xs uppercase tracking-wider flex items-center justify-center gap-2 shadow hover:bg-primary/90 transition-all cursor-pointer disabled:opacity-50"
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

            <div className="flex items-center justify-between text-xs pt-2">
              <button
                type="button"
                onClick={() => setAuthModalView('choice')}
                className="text-on-surface-variant hover:text-primary transition-colors cursor-pointer"
              >
                ← Back
              </button>
              <button
                type="button"
                onClick={() => {
                  setErrorMsg('');
                  setAuthModalView('register');
                  setRegStep(1);
                }}
                className="text-primary hover:underline font-medium cursor-pointer"
              >
                Don't have an account? Sign up
              </button>
            </div>
          </form>
        )}

      </div>
    </div>
  );
}

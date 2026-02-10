/**
 * Registration form component with captcha support
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/stores/useAuthStore';

export default function RegisterForm() {
  const router = useRouter();
  const { register, isLoading, error, clearError, fetchCaptcha } = useAuthStore();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    captchaCode: '',
  });
  const [captchaId, setCaptchaId] = useState('');
  const [captchaImage, setCaptchaImage] = useState('');
  const [validationErrors, setValidationErrors] = useState<{
    username?: string;
    password?: string;
    confirmPassword?: string;
    captchaCode?: string;
  }>({});

  // Load captcha on mount
  useEffect(() => {
    loadCaptcha();
  }, []);

  const loadCaptcha = async () => {
    try {
      const captcha = await fetchCaptcha();
      setCaptchaId(captcha.captcha_id);
      setCaptchaImage(captcha.image);
      setFormData((prev) => ({ ...prev, captchaCode: '' }));
    } catch (error) {
      console.error('Failed to load captcha:', error);
    }
  };

  const validateForm = () => {
    const errors: typeof validationErrors = {};

    // Username validation
    if (!formData.username) {
      errors.username = 'Username is required';
    } else if (formData.username.length < 3) {
      errors.username = 'Username must be at least 3 characters';
    } else if (formData.username.length > 20) {
      errors.username = 'Username must be less than 20 characters';
    } else if (!/^[a-zA-Z0-9_]+$/.test(formData.username)) {
      errors.username = 'Username can only contain letters, numbers, and underscores';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.password)) {
      errors.password = 'Password must contain at least one uppercase letter';
    } else if (!/[a-z]/.test(formData.password)) {
      errors.password = 'Password must contain at least one lowercase letter';
    } else if (!/[0-9]/.test(formData.password)) {
      errors.password = 'Password must contain at least one number';
    }

    // Confirm password validation
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    // Captcha validation
    if (!formData.captchaCode) {
      errors.captchaCode = 'Captcha is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    clearError();

    if (!validateForm()) {
      return;
    }

    try {
      await register(formData.username, formData.password, formData.captchaCode, captchaId);

      // Registration successful, redirect to chat
      router.push('/chat');
    } catch (error) {
      // Reload captcha on error
      loadCaptcha();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear validation error for this field
    if (validationErrors[name as keyof typeof validationErrors]) {
      setValidationErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <div className="w-full max-w-md">
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl shadow-2xl p-8">
          {/* Logo/Title */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">AI Chat Assistant</h1>
            <p className="text-slate-400">Create your account</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {/* Registration Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-slate-300 mb-2">
                Username
              </label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleChange}
                className={`w-full px-4 py-3 bg-slate-900/50 border ${
                  validationErrors.username ? 'border-red-500' : 'border-slate-600'
                } rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition`}
                placeholder="3-20 characters, letters, numbers, _ only"
                disabled={isLoading}
                autoComplete="username"
              />
              {validationErrors.username && (
                <p className="mt-1 text-sm text-red-400">{validationErrors.username}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-300 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full px-4 py-3 bg-slate-900/50 border ${
                  validationErrors.password ? 'border-red-500' : 'border-slate-600'
                } rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition`}
                placeholder="Min 8 chars, with uppercase, lowercase, and number"
                disabled={isLoading}
                autoComplete="new-password"
              />
              {validationErrors.password && (
                <p className="mt-1 text-sm text-red-400">{validationErrors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-300 mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                id="confirmPassword"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                className={`w-full px-4 py-3 bg-slate-900/50 border ${
                  validationErrors.confirmPassword ? 'border-red-500' : 'border-slate-600'
                } rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition`}
                placeholder="Re-enter your password"
                disabled={isLoading}
                autoComplete="new-password"
              />
              {validationErrors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{validationErrors.confirmPassword}</p>
              )}
            </div>

            {/* Captcha */}
            <div>
              <label htmlFor="captchaCode" className="block text-sm font-medium text-slate-300 mb-2">
                Verification Code
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="captchaCode"
                  name="captchaCode"
                  value={formData.captchaCode}
                  onChange={handleChange}
                  className={`flex-1 px-4 py-3 bg-slate-900/50 border ${
                    validationErrors.captchaCode ? 'border-red-500' : 'border-slate-600'
                  } rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition uppercase`}
                  placeholder="Enter code"
                  maxLength={6}
                  disabled={isLoading}
                  autoComplete="off"
                />
                <button
                  type="button"
                  onClick={loadCaptcha}
                  className="px-4 py-3 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded-lg transition flex items-center justify-center"
                  disabled={isLoading}
                >
                  {captchaImage ? (
                    <img src={captchaImage} alt="Captcha" className="h-10" />
                  ) : (
                    <span className="text-slate-400 text-sm">Loading...</span>
                  )}
                </button>
              </div>
              {validationErrors.captchaCode && (
                <p className="mt-1 text-sm text-red-400">{validationErrors.captchaCode}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              ) : (
                'Create Account'
              )}
            </button>
          </form>

          {/* Login Link */}
          <div className="mt-6 text-center">
            <p className="text-slate-400 text-sm">
              Already have an account?{' '}
              <Link href="/login" className="text-blue-400 hover:text-blue-300 font-medium transition">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

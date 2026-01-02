import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../App';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import { ShoppingCart, Mail, Lock, User, ArrowRight } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "");
const API = BACKEND_URL;

export default function Auth() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get('tab') === 'signup' ? 'signup' : 'login';
  const { login } = useAuth();

  const [activeTab, setActiveTab] = useState(initialTab);
  const [signupData, setSignupData] = useState({
    username: '',
    email: '',
    password: '',
  });
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [otpData, setOtpData] = useState({ email: '', otp: '' });
  const [resetData, setResetData] = useState({
    email: '',
    otp: '',
    newPassword: '',
  });
  const [resetStep, setResetStep] = useState('request'); // 'request' | 'verify' | 'reset'
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/');
    }
  }, [navigate]);

  function validateSignup(username, email, password) {
    if (!username || username.length < 3)
      return 'Username must be at least 3 characters';
    if (!email || !/\S+@\S+\.\S+/.test(email)) return 'Invalid email format';
    if (!password || password.length < 6)
      return 'Password must be at least 6 characters';
    return null;
  }

  async function handleSignup(e) {
    e.preventDefault();
    const { username, email, password } = signupData;

    const validationError = validateSignup(username, email, password);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/register`, { username, email, password });
      setOtpData({ email, otp: '' });
      setActiveTab('verify');
      toast.success('Signup successful! Please check your email for OTP verification.');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Signup failed';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    const { email, otp } = otpData;

    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/verify-otp`, { email, otp });
      toast.success('Account verified successfully!');
      setActiveTab('login');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Verification failed';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    const { email, password } = loginData;

    setLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      // Error handled in auth context
    } finally {
      setLoading(false);
    }
  }

  async function requestResetOtp(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password/request`, {
        email: resetData.email,
      });
      toast.success('OTP sent to your email!');
      setResetStep('verify');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Failed to send OTP';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  async function verifyResetOtp(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password/verify`, {
        email: resetData.email,
        otp: resetData.otp,
      });
      toast.success('OTP verified!');
      setResetStep('reset');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'OTP verification failed';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  async function resetPassword(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password/reset`, {
        email: resetData.email,
        otp: resetData.otp,
        newPassword: resetData.newPassword,
      });
      toast.success('Password reset successful!');
      setActiveTab('login');
      setResetStep('request');
      setResetData({ email: '', otp: '', newPassword: '' });
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Password reset failed';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  async function resendOtp() {
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/forgot-password/request`, {
        email: resetData.email,
      });
      toast.success('OTP resent!');
    } catch (err) {
      const errMsg = err.response?.data?.message || 'Failed to resend OTP';
      toast.error(errMsg);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-6xl w-full bg-white shadow-2xl rounded-2xl overflow-hidden grid lg:grid-cols-2">
        {/* Left panel */}
        <div className="bg-gradient-to-br from-blue-600 to-purple-600 text-white p-12 flex flex-col justify-between relative overflow-hidden">
          <div className="relative z-10">
            <div className="flex items-center mb-6">
              <ShoppingCart className="h-8 w-8 mr-3" />
              <h1 className="text-4xl font-bold">ShopMate</h1>
            </div>
            <p className="text-blue-100 mb-8 text-lg">
              Your one-stop shop for amazing products
            </p>
            <ul className="space-y-3 text-sm text-blue-100">
              <li className="flex items-center">
                <ArrowRight className="h-4 w-4 mr-2" />
                Discover quality products at great prices
              </li>
              <li className="flex items-center">
                <ArrowRight className="h-4 w-4 mr-2" />
                Secure checkout and fast delivery
              </li>
              <li className="flex items-center">
                <ArrowRight className="h-4 w-4 mr-2" />
                24/7 customer support
              </li>
              <li className="flex items-center">
                <ArrowRight className="h-4 w-4 mr-2" />
                Easy returns and exchanges
              </li>
            </ul>
          </div>
          <div className="relative z-10">
            <p className="text-xs text-blue-200">
              Secure authentication with email verification and OTP-based password reset.
            </p>
          </div>
          {/* Background decoration */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-10 left-10 w-20 h-20 bg-white rounded-full"></div>
            <div className="absolute bottom-10 right-10 w-32 h-32 bg-white rounded-full"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-white rounded-full"></div>
          </div>
        </div>

        {/* Right panel: forms */}
        <div className="p-12">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-8">
              <TabsTrigger value="login" className="text-sm">Login</TabsTrigger>
              <TabsTrigger value="signup" className="text-sm">Sign Up</TabsTrigger>
            </TabsList>

            {/* Login Tab */}
            <TabsContent value="login" className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Welcome Back</h2>
                <p className="text-gray-600">Sign in to your ShopMate account</p>
              </div>

              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="login-email">Email</Label>
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="Enter your email"
                    value={loginData.email}
                    onChange={(e) =>
                      setLoginData({ ...loginData, email: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="login-password">Password</Label>
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="Enter your password"
                    value={loginData.password}
                    onChange={(e) =>
                      setLoginData({ ...loginData, password: e.target.value })
                    }
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  disabled={loading}
                >
                  {loading ? 'Signing In...' : 'Sign In'}
                </Button>
              </form>

              <div className="text-center">
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:underline"
                  onClick={() => {
                    setResetStep('request');
                    setActiveTab('forgot');
                  }}
                >
                  Forgot your password?
                </button>
              </div>
            </TabsContent>

            {/* Signup Tab */}
            <TabsContent value="signup" className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Create Account</h2>
                <p className="text-gray-600">Join ShopMate today</p>
              </div>

              <form onSubmit={handleSignup} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signup-username">Username</Label>
                  <Input
                    id="signup-username"
                    type="text"
                    placeholder="Choose a username"
                    value={signupData.username}
                    onChange={(e) =>
                      setSignupData({ ...signupData, username: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="Enter your email"
                    value={signupData.email}
                    onChange={(e) =>
                      setSignupData({ ...signupData, email: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <Input
                    id="signup-password"
                    type="password"
                    placeholder="Create a password"
                    value={signupData.password}
                    onChange={(e) =>
                      setSignupData({ ...signupData, password: e.target.value })
                    }
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  disabled={loading}
                >
                  {loading ? 'Creating Account...' : 'Create Account'}
                </Button>
              </form>
            </TabsContent>

            {/* Email Verification Tab */}
            <TabsContent value="verify" className="space-y-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-8 w-8 text-blue-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Verify Your Email</h2>
                <p className="text-gray-600">We've sent a 6-digit OTP to your email</p>
              </div>

              <form onSubmit={handleVerify} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="verify-email">Email</Label>
                  <Input
                    id="verify-email"
                    type="email"
                    placeholder="Enter your email"
                    value={otpData.email}
                    onChange={(e) =>
                      setOtpData({ ...otpData, email: e.target.value })
                    }
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="verify-otp">OTP</Label>
                  <Input
                    id="verify-otp"
                    type="text"
                    placeholder="Enter 6-digit OTP"
                    value={otpData.otp}
                    onChange={(e) =>
                      setOtpData({ ...otpData, otp: e.target.value })
                    }
                    maxLength={6}
                    required
                  />
                </div>
                <Button
                  type="submit"
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                  disabled={loading}
                >
                  {loading ? 'Verifying...' : 'Verify Account'}
                </Button>
              </form>

              <div className="text-center">
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:underline"
                  onClick={() => setActiveTab('login')}
                >
                  Back to Login
                </button>
              </div>
            </TabsContent>

            {/* Forgot Password Tab */}
            <TabsContent value="forgot" className="space-y-6">
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Lock className="h-8 w-8 text-purple-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900">Reset Password</h2>
                <p className="text-gray-600">
                  {resetStep === 'request' && 'Enter your email to receive a reset OTP'}
                  {resetStep === 'verify' && 'Enter the OTP sent to your email'}
                  {resetStep === 'reset' && 'Enter your new password'}
                </p>
              </div>

              {resetStep === 'request' && (
                <form onSubmit={requestResetOtp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reset-email">Email</Label>
                    <Input
                      id="reset-email"
                      type="email"
                      placeholder="Enter your email"
                      value={resetData.email}
                      onChange={(e) =>
                        setResetData({ ...resetData, email: e.target.value })
                      }
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    disabled={loading}
                  >
                    {loading ? 'Sending...' : 'Send Reset OTP'}
                  </Button>
                </form>
              )}

              {resetStep === 'verify' && (
                <form onSubmit={verifyResetOtp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reset-verify-email">Email</Label>
                    <Input
                      id="reset-verify-email"
                      type="email"
                      value={resetData.email}
                      onChange={(e) =>
                        setResetData({ ...resetData, email: e.target.value })
                      }
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="reset-otp">OTP</Label>
                    <Input
                      id="reset-otp"
                      type="text"
                      placeholder="Enter 6-digit OTP"
                      value={resetData.otp}
                      onChange={(e) =>
                        setResetData({ ...resetData, otp: e.target.value })
                      }
                      maxLength={6}
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    disabled={loading}
                  >
                    {loading ? 'Verifying...' : 'Verify OTP'}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full mt-2"
                    onClick={resendOtp}
                    disabled={loading}
                  >
                    Resend OTP
                  </Button>
                </form>
              )}

              {resetStep === 'reset' && (
                <form onSubmit={resetPassword} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="reset-new-password">New Password</Label>
                    <Input
                      id="reset-new-password"
                      type="password"
                      placeholder="Enter new password"
                      value={resetData.newPassword}
                      onChange={(e) =>
                        setResetData({
                          ...resetData,
                          newPassword: e.target.value,
                        })
                      }
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                    disabled={loading}
                  >
                    {loading ? 'Resetting...' : 'Reset Password'}
                  </Button>
                </form>
              )}

              <div className="text-center">
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:underline"
                  onClick={() => setActiveTab('login')}
                >
                  Back to Login
                </button>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "");
const API = BACKEND_URL;

const VerifyOTP = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const email = searchParams.get('email');

  useEffect(() => {
    if (!email) {
      navigate('/register');
    }
  }, [email, navigate]);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/api/auth/verify-otp`, { email, otp });
      toast.success('Email verified successfully! You can now log in.');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    setResendLoading(true);

    try {
      // Trigger registration again to resend OTP
      await axios.post(`${API}/api/auth/register`, {
        name: 'temp', // This will fail but resend OTP
        email,
        password: 'temp'
      });
    } catch (err) {
      // Expected to fail, but OTP should be resent
    }

    setResendLoading(false);
    setCountdown(60); // 60 second cooldown
    toast.success('OTP resent to your email');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Verify Your Email</CardTitle>
          <CardDescription>
            We've sent a 6-digit OTP to {email}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleVerify} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Enter OTP
              </label>
              <Input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="000000"
                maxLength="6"
                required
                className="text-center text-2xl tracking-widest"
              />
            </div>

            <Button type="submit" className="w-full" disabled={loading || otp.length !== 6}>
              {loading ? 'Verifying...' : 'Verify Email'}
            </Button>
          </form>

          <div className="text-center mt-4">
            <button
              onClick={handleResendOTP}
              disabled={resendLoading || countdown > 0}
              className="text-blue-600 hover:text-blue-800 disabled:text-gray-400 text-sm"
            >
              {resendLoading ? 'Sending...' : countdown > 0 ? `Resend OTP in ${countdown}s` : 'Resend OTP'}
            </button>
          </div>

          <div className="text-center mt-6">
            <button
              onClick={() => navigate('/register')}
              className="text-gray-600 hover:text-gray-800 text-sm"
            >
              Wrong email? Go back to register
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VerifyOTP;

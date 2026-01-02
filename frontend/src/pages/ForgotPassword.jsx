import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "");
const API = BACKEND_URL;

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setSuccess('');

    try {
      await axios.post(`${API}/api/auth/forgot-password/request`, { email });
      setSuccess('OTP sent to your email for password reset');
      setTimeout(() => navigate(`/reset-password?email=${email}`), 2000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Forgot Password</CardTitle>
          <CardDescription>
            Enter your email to receive password reset OTP
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>

            {success && (
              <div className="text-green-600 text-center p-3 bg-green-50 rounded">
                {success}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset OTP'}
            </Button>
          </form>

          <div className="text-center mt-6">
            <button
              onClick={() => navigate('/login')}
              className="text-gray-600 hover:text-gray-800 text-sm"
            >
              Back to Login
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ForgotPassword;

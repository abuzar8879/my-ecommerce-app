import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from './ui/alert-dialog';
import { Key, Trash2, History, UserX, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../App';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}`;

const changePasswordSchema = z.object({
  old_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(6, 'New password must be at least 6 characters'),
  confirm_password: z.string().min(1, 'Please confirm your new password')
}).refine((data) => data.new_password === data.confirm_password, {
  message: "Passwords don't match",
  path: ["confirm_password"],
});

const deleteAccountSchema = z.object({
  password: z.string().min(1, 'Password is required'),
});

const SettingsPage = () => {
  const { user, logout } = useAuth();
  const [loginHistory, setLoginHistory] = useState([]);
  const [showPasswords, setShowPasswords] = useState({
    old: false,
    new: false,
    confirm: false
  });
  const [isLoading, setIsLoading] = useState({
    password: false,
    address: false,
    history: false,
    delete: false
  });

  const passwordForm = useForm({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }
  });

  const deleteForm = useForm({
    resolver: zodResolver(deleteAccountSchema),
    defaultValues: {
      password: ''
    }
  });

  useEffect(() => {
    fetchLoginHistory();
  }, []);

  const fetchLoginHistory = async () => {
    setIsLoading(prev => ({ ...prev, history: true }));
    try {
      const response = await axios.get(`${API}/api/users/login-history`);
      setLoginHistory(response.data.login_history || []);
    } catch (error) {
      console.error('Error fetching login history:', error);
      toast.error('Failed to load login history');
    } finally {
      setIsLoading(prev => ({ ...prev, history: false }));
    }
  };

  const handleChangePassword = async (data) => {
    setIsLoading(prev => ({ ...prev, password: true }));
    try {
      await axios.put(`${API}/api/users/change-password`, {
        old_password: data.old_password,
        new_password: data.new_password
      });
      toast.success('Password changed successfully!');
      passwordForm.reset();
    } catch (error) {
      console.error('Change password error:', error);
      toast.error(error.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsLoading(prev => ({ ...prev, password: false }));
    }
  };

  const handleDeleteAddress = async () => {
    setIsLoading(prev => ({ ...prev, address: true }));
    try {
      await axios.delete(`${API}/api/users/delete-address`);
      toast.success('Address deleted successfully!');
      // Refresh user data
      window.location.reload();
    } catch (error) {
      console.error('Delete address error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete address');
    } finally {
      setIsLoading(prev => ({ ...prev, address: false }));
    }
  };

  const handleDeleteAccount = async (data) => {
    setIsLoading(prev => ({ ...prev, delete: true }));
    try {
      await axios.delete(`${API}/api/users/delete-account`, {
        data: { password: data.password }
      });
      toast.success('Account deleted successfully!');
      logout();
    } catch (error) {
      console.error('Delete account error:', error);
      toast.error(error.response?.data?.detail || 'Failed to delete account');
    } finally {
      setIsLoading(prev => ({ ...prev, delete: false }));
    }
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const togglePasswordVisibility = (field) => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-4xl font-bold mb-8">Settings</h1>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Key className="h-5 w-5 mr-2" />
            Change Password
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={passwordForm.handleSubmit(handleChangePassword)} className="space-y-4">
              <div>
                <Label htmlFor="old_password">Current Password</Label>
                <div className="relative">
                  <Input
                    id="old_password"
                    type={showPasswords.old ? "text" : "password"}
                    {...passwordForm.register('old_password')}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('old')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.old ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {passwordForm.formState.errors.old_password && (
                  <p className="text-sm text-red-600 mt-1">{passwordForm.formState.errors.old_password.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="new_password">New Password</Label>
                <div className="relative">
                  <Input
                    id="new_password"
                    type={showPasswords.new ? "text" : "password"}
                    {...passwordForm.register('new_password')}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('new')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {passwordForm.formState.errors.new_password && (
                  <p className="text-sm text-red-600 mt-1">{passwordForm.formState.errors.new_password.message}</p>
                )}
              </div>

              <div>
                <Label htmlFor="confirm_password">Confirm New Password</Label>
                <div className="relative">
                  <Input
                    id="confirm_password"
                    type={showPasswords.confirm ? "text" : "password"}
                    {...passwordForm.register('confirm_password')}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => togglePasswordVisibility('confirm')}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                {passwordForm.formState.errors.confirm_password && (
                  <p className="text-sm text-red-600 mt-1">{passwordForm.formState.errors.confirm_password.message}</p>
                )}
              </div>

              <Button type="submit" disabled={isLoading.password}>
                {isLoading.password ? 'Changing...' : 'Change Password'}
              </Button>
            </form>
        </CardContent>
      </Card>

      {/* Delete Address */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Trash2 className="h-5 w-5 mr-2" />
            Delete Address
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">
            Remove your saved delivery address from your account. This action cannot be undone.
          </p>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive" disabled={isLoading.address}>
                {isLoading.address ? 'Deleting...' : 'Delete Address'}
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently remove your delivery address. You can add it back later if needed.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDeleteAddress}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>

      {/* Login History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <History className="h-5 w-5 mr-2" />
            Login History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading.history ? (
            <p>Loading login history...</p>
          ) : loginHistory.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Device</TableHead>
                  <TableHead>IP Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loginHistory.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>{formatDateTime(entry.login_time)}</TableCell>
                    <TableCell>{entry.device || 'Unknown'}</TableCell>
                    <TableCell>{entry.ip_address || 'N/A'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-gray-600">No login history available.</p>
          )}
        </CardContent>
      </Card>

      {/* Delete Account */}
      <Card className="border-red-200">
        <CardHeader>
          <CardTitle className="flex items-center text-red-600">
            <UserX className="h-5 w-5 mr-2" />
            Delete Account
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600 mb-4">
            Permanently delete your account and all associated data. This action cannot be undone.
          </p>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button variant="destructive">
                Delete Account
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete Account</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete your account, all your orders, support tickets, and login history.
                  This action cannot be undone. Please enter your password to confirm.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <form onSubmit={deleteForm.handleSubmit(handleDeleteAccount)}>
                <div className="my-4">
                  <Label htmlFor="delete_password">Enter your password</Label>
                  <Input
                    id="delete_password"
                    type="password"
                    {...deleteForm.register('password')}
                    className="mt-2"
                  />
                  {deleteForm.formState.errors.password && (
                    <p className="text-sm text-red-600 mt-1">{deleteForm.formState.errors.password.message}</p>
                  )}
                </div>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    type="submit"
                    disabled={isLoading.delete}
                    className="bg-red-600 hover:bg-red-700"
                  >
                    {isLoading.delete ? 'Deleting...' : 'Delete Account'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </form>
            </AlertDialogContent>
          </AlertDialog>
        </CardContent>
      </Card>
    </div>
  );
};

export default SettingsPage;

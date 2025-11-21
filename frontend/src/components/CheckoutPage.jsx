import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth, useCart } from '../App'; // Assuming useAuth is exported from App.js or adjust import accordingly
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const API = process.env.REACT_APP_BACKEND_URL;

const CheckoutPage = () => {
  const { user, updateUser } = useAuth();
  const { cartItems, clearCart, getTotalPrice } = useCart();
  const [address, setAddress] = useState({
    street: '',
    city: '',
    state: '',
    postal_code: '',
    country: ''
  });
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState('COD');
  const [loading, setLoading] = useState(true);
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);

  useEffect(() => {
    if (user) {
      fetchUserData();
    } else {
      setLoading(false);
    }
  }, [user]);

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/api/auth/me`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      const userData = response.data;
      setFullName(userData.name || '');
      setEmail(userData.email || '');
      setPhoneNumber(userData.mobile_number || '');
      setAddress({
        street: userData.delivery_address?.street || '',
        city: userData.delivery_address?.city || '',
        state: userData.delivery_address?.state || '',
        postal_code: userData.delivery_address?.postal_code || userData.delivery_address?.pincode || '',
        country: userData.delivery_address?.country || ''
      });
      setLoading(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to fetch user data');
      setLoading(false);
    }
  };

  const handleEditToggle = () => {
    setIsEditing(!isEditing);
  };

  const handleAddressChange = (field, value) => {
    setAddress(prev => ({ ...prev, [field]: value }));
  };

  const handleSaveAddress = async () => {
    try {
      // Prepare address data with postal_code instead of pincode to match backend schema
      const deliveryAddress = {
        street: address.street || '',
        city: address.city || '',
        state: address.state || '',
        postal_code: address.postal_code || '',
        country: address.country || '',
        full_name: fullName || '',
        phone_number: phoneNumber || ''
      };

      // Basic client-side validation for required fields
      if (
        !fullName ||
        !email ||
        !deliveryAddress.street ||
        !deliveryAddress.city ||
        !deliveryAddress.state ||
        !deliveryAddress.postal_code ||
        !deliveryAddress.country
      ) {
        toast.error('Please fill in all required fields.');
        return;
      }

      const updatedData = {
        name: fullName,
        email,
        mobile_number: phoneNumber,
        delivery_address: deliveryAddress
      };

      console.log('Submitting profile update payload:', updatedData);

      const response = await axios.put(`${API}/api/users/profile`, updatedData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });
      updateUser(response.data);
      toast.success('Address updated successfully');
      setIsEditing(false);
    } catch (error) {
      // Handle validation errors gracefully
      if (error.response?.status === 422 && error.response?.data) {
        // Extract error messages from validation error object
        const validationErrors = error.response.data;
        let messages = [];
        if (Array.isArray(validationErrors)) {
          messages = validationErrors.map(err => {
            if (err.msg && err.loc) {
              return `${err.msg} at ${err.loc.join('.')}`;
            }
            return err.msg || JSON.stringify(err);
          });
        } else if (typeof validationErrors === 'object') {
          messages = Object.values(validationErrors).map(err => {
            if (err.msg && err.loc) {
              return `${err.msg} at ${err.loc.join('.')}`;
            }
            return err.msg || JSON.stringify(err);
          });
        } else {
          messages = [JSON.stringify(validationErrors)];
        }
        toast.error(messages.join(', '));
      } else {
        toast.error(error.response?.data?.detail || 'Failed to update address');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  const handlePlaceOrder = async () => {
    setIsPlacingOrder(true);
    try {
      // Generate unique order ID
      const orderId = `ORD${Date.now()}${Math.random().toString(36).substr(2, 5).toUpperCase()}`;

      // Prepare order data to match backend OrderCreate model
      const orderData = {
        products: cartItems.map(item => ({
          product_id: item.product.id,
          name: item.product.name,
          quantity: item.quantity,
          price: item.product.price,
          total: item.product.price * item.quantity
        })),
        total_amount: getTotalPrice()
      };

      // Create order via API
      const response = await axios.post(`${API}/api/orders`, orderData, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`
        }
      });

      // Clear cart
      clearCart();

      // Redirect to success page
      window.location.href = `/order-success/${orderId}`;
    } catch (error) {
      console.error('Error placing order:', error);
      toast.error(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setIsPlacingOrder(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 bg-white rounded shadow mt-10">
      <h1 className="text-2xl font-bold mb-6">Checkout</h1>

      <div className="mb-6">
        <Label>Full Name</Label>
        <Input
          value={fullName}
          onChange={e => setFullName(e.target.value)}
          disabled={!isEditing}
          className="mb-2"
        />
      </div>

      <div className="mb-6">
        <Label>Email</Label>
        <Input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          disabled={!isEditing}
          className="mb-2"
        />
      </div>

      <div className="mb-6">
        <Label>Phone Number</Label>
        <Input
          value={phoneNumber}
          onChange={e => setPhoneNumber(e.target.value)}
          disabled={!isEditing}
          className="mb-2"
        />
      </div>

      <h2 className="text-xl font-semibold mb-4">Delivery Address</h2>

      <div className="mb-4">
        <Label>Street</Label>
        <Input
          value={address.street}
          onChange={e => handleAddressChange('street', e.target.value)}
          disabled={!isEditing}
          className="mb-2"
        />
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <Label>City</Label>
          <Input
            value={address.city}
            onChange={e => handleAddressChange('city', e.target.value)}
            disabled={!isEditing}
            className="mb-2"
          />
        </div>
        <div>
          <Label>State</Label>
          <Input
            value={address.state}
            onChange={e => handleAddressChange('state', e.target.value)}
            disabled={!isEditing}
            className="mb-2"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <Label>Postal Code</Label>
          <Input
            value={address.postal_code}
            onChange={e => handleAddressChange('postal_code', e.target.value)}
            disabled={!isEditing}
            className="mb-2"
          />
        </div>
        <div>
          <Label>Country</Label>
          <Input
            value={address.country}
            onChange={e => handleAddressChange('country', e.target.value)}
            disabled={!isEditing}
            className="mb-2"
          />
        </div>
      </div>

      <div className="flex space-x-4 mb-6">
        {!isEditing ? (
          <>
            <Button onClick={handleEditToggle}>Edit Address</Button>
            <Button onClick={() => toast('Address confirmed')} variant="outline">Confirm Address</Button>
          </>
        ) : (
          <>
            <Button onClick={handleSaveAddress}>Save</Button>
            <Button onClick={handleEditToggle} variant="outline">Cancel</Button>
          </>
        )}
      </div>

      <div className="mb-6">
        <Label>Payment Method</Label>
        <Select value={paymentMethod} onValueChange={setPaymentMethod}>
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select a payment method" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="COD">Cash on Delivery (COD)</SelectItem>
            <SelectItem value="MoreOptions" disabled>More Options Coming Soon</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button
        onClick={handlePlaceOrder}
        disabled={isPlacingOrder || cartItems.length === 0}
        className="w-full"
      >
        {isPlacingOrder ? 'Placing Order...' : `Place Order - ₹${getTotalPrice().toFixed(2)}`}
      </Button>
    </div>
  );
};


export default CheckoutPage;
   

import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { CheckCircle, Package, Home } from 'lucide-react';
import { Button } from './ui/button';

const OrderSuccessPage = () => {
  const { orderId } = useParams();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="h-8 w-8 text-green-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">Order Placed Successfully!</h1>
        <p className="text-gray-600 mb-6">Thank you for your purchase. Your order has been confirmed.</p>

        <div className="bg-gray-50 rounded-lg p-4 mb-6">
          <p className="text-sm text-gray-600 mb-1">Order ID</p>
          <p className="font-mono font-semibold text-gray-900">{orderId}</p>
        </div>

        <div className="space-y-3">
          <Link to="/profile/orders">
            <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
              <Package className="h-4 w-4 mr-2" />
              View Order Details
            </Button>
          </Link>

          <Link to="/products">
            <Button variant="outline" className="w-full">
              <Home className="h-4 w-4 mr-2" />
              Continue Shopping
            </Button>
          </Link>
        </div>

        <div className="mt-6 text-sm text-gray-500">
          <p>You will receive an email confirmation shortly.</p>
        </div>
      </div>
    </div>
  );
};

export default OrderSuccessPage;

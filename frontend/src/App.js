import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import './App.css';

// Import UI components
import { Button } from './components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Badge } from './components/ui/badge';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';

// Icons
import { ShoppingCart, User, Star, Package, Users, BarChart3, Ticket, Plus, Minus, CreditCard, LogOut, Menu, X, Search, Filter, ArrowRight, Mail, Phone, MapPin, HelpCircle, Trash2, Send } from 'lucide-react';



const BACKEND_URL = process.env.REACT_APP_BACKEND_URL?.replace(/\/$/, "");
const API = BACKEND_URL;





// Profile form validation schema (moved to ProfileInfo component)

// Import Admin Components
import ProductManagement from './components/admin/ProductManagement';
import UserManagement from './components/admin/UserManagement';
import OrderManagement from './components/admin/OrderManagement';
import SupportTicketManagement from './components/admin/SupportTicketManagement';

// Import CheckoutPage
import CheckoutPage from './components/CheckoutPage';

// Import OrderSuccessPage
import OrderSuccessPage from './components/OrderSuccessPage';

// Import Profile Components
import ProfileLayout from './components/ProfileLayout';
import ProfileInfo from './components/ProfileInfo';
import MyTicketsPage from './components/MyTicketsPage';
import SettingsPage from './components/SettingsPage';
import OrderHistoryPage from './components/OrderHistoryPage';

// Import Error Boundary
import ErrorBoundary from './components/ErrorBoundary';

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/api/auth/me`);
      setUser(response.data);
    } catch (error) {
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const updateUser = (updatedUserData) => {
    setUser(updatedUserData);
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/api/auth/login`, { email, password });
      const { access_token, user: userData } = response.data;

      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      toast.success('Login successful!');
      return userData;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
      throw error;
    }
  };

  const register = async (name, email, password) => {
    try {
      const response = await axios.post(`${API}/api/auth/register`, { name, email, password });
      const { access_token, user: userData } = response.data;

      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      setUser(userData);
      toast.success('Registration successful!');
      return userData;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    toast.success('Logged out successfully');
  };

  // Make updateUser available globally for components that need it
  useEffect(() => {
    window.updateUserContext = updateUser;
    return () => {
      delete window.updateUserContext;
    };
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export { useAuth, useCart };

// Cart Context
const CartContext = createContext();

const CartProvider = ({ children }) => {
  const [cartItems, setCartItems] = useState(() => {
    // Initialize cart from localStorage
    try {
      const savedCart = localStorage.getItem('shopmate_cart');
      return savedCart ? JSON.parse(savedCart) : [];
    } catch (error) {
      console.error('Error loading cart from localStorage:', error);
      return [];
    }
  });

  // Save cart to localStorage whenever cartItems changes
  React.useEffect(() => {
    try {
      localStorage.setItem('shopmate_cart', JSON.stringify(cartItems));
    } catch (error) {
      console.error('Error saving cart to localStorage:', error);
    }
  }, [cartItems]);

  const addToCart = (product, quantity = 1) => {
    setCartItems(prev => {
      const existingItem = prev.find(item => item.product.id === product.id);
      if (existingItem) {
        return prev.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prev, { product, quantity }];
    });
    toast.success(`${product.name} added to cart!`);
  };

  const removeFromCart = (productId) => {
    setCartItems(prev => prev.filter(item => item.product.id !== productId));
  };

  const updateQuantity = (productId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCartItems(prev =>
      prev.map(item =>
        item.product.id === productId ? { ...item, quantity } : item
      )
    );
  };

  const clearCart = () => {
    setCartItems([]);
    localStorage.removeItem('shopmate_cart');
  };

  const getTotalPrice = () => {
    return cartItems.reduce((total, item) => total + (item.product.price * item.quantity), 0);
  };

  const getTotalItems = () => {
    return cartItems.reduce((total, item) => total + item.quantity, 0);
  };

  return (
    <CartContext.Provider value={{
      cartItems,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      getTotalPrice,
      getTotalItems
    }}>
      {children}
    </CartContext.Provider>
  );
};

const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

// Navigation Component
const Navigation = () => {
  const { user, logout } = useAuth();
  const { getTotalItems } = useCart();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <nav className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <a href="/" className="text-xl font-bold text-gray-900">
              ShopMate
            </a>
          </div>

          
          {/* Desktop Navigation  */}
          
          <div className="hidden md:flex items-center space-x-8">
            {user?.role !== 'admin' && (
              <>
                <a href="/products" className="text-gray-700 hover:text-gray-900 transition-colors">Products</a>
                <a href="/help" className="text-gray-700 hover:text-gray-900 transition-colors">Help</a>
                <a href="/contact" className="text-gray-700 hover:text-gray-900 transition-colors">Contact</a>
              </>
            )}
          </div>

          <div className="flex items-center space-x-4">
            {user?.role !== 'admin' && (
              <a href="/cart" className="relative p-2 text-gray-700 hover:text-gray-900 transition-colors">
                <ShoppingCart className="h-6 w-6" />
                {getTotalItems() > 0 && (
                  <Badge className="absolute -top-1 -right-1 px-2 py-1 text-xs bg-red-500 text-white">
                    {getTotalItems()}
                  </Badge>
                )}
              </a>
            )}

            {user ? (
              <div className="flex items-center space-x-4">
                {user.role === 'admin' && (
                  <a href="/admin" className="text-gray-700 hover:text-gray-900 transition-colors">
                    Admin
                  </a>
                )}
                <a href="/profile" className="text-gray-700 hover:text-gray-900 transition-colors">
                  <User className="h-6 w-6" />
                </a>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="text-gray-700 hover:text-gray-900"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <a href="/login">
                  <Button variant="ghost" size="sm">Login</Button>
                </a>
                <a href="/register">
                  <Button size="sm">Sign Up</Button>
                </a>
              </div>
            )}

            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t bg-white py-4">
            <div className="flex flex-col space-y-4">
              {user?.role !== 'admin' && (
                <>
                  <a href="/products" className="text-gray-700 hover:text-gray-900 transition-colors">Products</a>
                  <a href="/help" className="text-gray-700 hover:text-gray-900 transition-colors">Help</a>
                  <a href="/contact" className="text-gray-700 hover:text-gray-900 transition-colors">Contact</a>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

// Home Page
const HomePage = () => {
  const { user } = useAuth();
  const [featuredProducts, setFeaturedProducts] = useState([]);

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      fetchFeaturedProducts();
    }
  }, [user]);

  const fetchFeaturedProducts = async () => {
    try {
      const response = await axios.get(`${API}/api/products`);
      setFeaturedProducts(response.data.slice(0, 6));
    } catch (error) {
      console.error('Error fetching featured products:', error);
    }
  };

  // Admin users are redirected to admin dashboard by default
  if (user && user.role === 'admin') {
    return <Navigate to="/admin" replace />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Hero Section */}
      <section className="py-20 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold text-gray-900 mb-8 leading-tight">
            Welcome to
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600 block">
              ShopMate
            </span>
          </h1>
          <p className="text-xl text-gray-600 mb-12 max-w-2xl mx-auto">
            Discover amazing products at unbeatable prices. Your one-stop shop for everything you need.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="/products">
              <Button size="lg" className="w-full sm:w-auto bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-4 text-lg">
                Shop Now
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </a>
            <a href="/help">
              <Button variant="outline" size="lg" className="w-full sm:w-auto px-8 py-4 text-lg">
                Learn More
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">Featured Products</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {featuredProducts.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          <div className="text-center mt-12">
            <a href="/products">
              <Button size="lg" variant="outline">View All Products</Button>
            </a>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">Why Choose ShopMate?</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Package className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Quality Products</h3>
              <p className="text-gray-600">Carefully curated selection of high-quality products from trusted brands.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CreditCard className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Secure Payments</h3>
              <p className="text-gray-600">Safe and secure payment processing with multiple payment options.</p>
            </div>
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <HelpCircle className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-xl font-semibold mb-2">24/7 Support</h3>
              <p className="text-gray-600">Round-the-clock customer support to help you with any questions.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product }) => {
  const { addToCart } = useCart();

  return (
    <Card className="group hover:shadow-lg transition-all duration-300 border-0 bg-white/80 backdrop-blur">
      <CardContent className="p-6">
        <div className="aspect-square bg-gray-100 rounded-lg mb-4 overflow-hidden">
          {product.images && product.images.length > 0 ? (
            <img
              src={product.images[0]}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Package className="h-16 w-16 text-gray-400" />
            </div>
          )}
        </div>
        <h3 className="font-semibold text-lg mb-2 text-gray-900">{product.name}</h3>
        <p className="text-gray-600 text-sm mb-3 line-clamp-2">{product.description}</p>
        <div className="flex items-center justify-between mb-4">
          <span className="text-2xl font-bold text-blue-600">₹{product.price}</span>
          <Badge variant="secondary">{product.category}</Badge>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-500">Stock: {product.stock}</span>
          <Button
            onClick={() => addToCart(product)}
            disabled={product.stock === 0}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
          >
            Add to Cart
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

// Products Page
const ProductsPage = () => {
  const [products, setProducts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    fetchProducts();
  }, [searchTerm, selectedCategory]);

  const fetchProducts = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await axios.get(`${API}/api/products?${params}`);
      setProducts(response.data);
      
      // Extract unique categories
      const uniqueCategories = [...new Set(response.data.map(p => p.category))];
      setCategories(uniqueCategories);
    } catch (error) {
      console.error('Error fetching products:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">Our Products</h1>
        
        {/* Search and Filter */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search products..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Categories</option>
            {categories.map(category => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>
        </div>

        {/* Products Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>

        {products.length === 0 && (
          <div className="text-center py-12">
            <Package className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600">No products found</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Cart Page
const CartPage = () => {
  const { cartItems, updateQuantity, removeFromCart, getTotalPrice, clearCart } = useCart();
  const { user } = useAuth();
  const [isCheckingOut, setIsCheckingOut] = useState(false);

  if (user?.role === 'admin') {
    return <Navigate to="/admin" replace />;
  }

  const handleCheckout = async () => {
    if (!user) {
      toast.error('Please login to checkout');
      return;
    }

    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    // Navigate to /checkout page instead of performing API call
    window.location.href = '/checkout';
  };

  if (cartItems.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-2xl mx-auto px-4 text-center">
          <ShoppingCart className="h-16 w-16 text-gray-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold mb-4">Your cart is empty</h1>
          <p className="text-gray-600 mb-8">Add some products to get started!</p>
          <a href="/products">
            <Button>Continue Shopping</Button>
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold mb-8">Shopping Cart</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-4">
            {cartItems.map(item => (
              <Card key={item.product.id} className="p-6">
                <div className="flex items-center space-x-4">
                  <div className="w-20 h-20 bg-gray-100 rounded-lg overflow-hidden">
                    {item.product.images && item.product.images.length > 0 ? (
                      <img
                        src={item.product.images[0]}
                        alt={item.product.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <Package className="h-8 w-8 text-gray-400" />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="font-semibold">{item.product.name}</h3>
                    <p className="text-gray-600">${item.product.price}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => updateQuantity(item.product.id, item.quantity - 1)}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <span className="px-3 py-1 border rounded">{item.quantity}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => updateQuantity(item.product.id, item.quantity + 1)}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  <div className="text-right">
                    <p className="font-semibold">₹{(item.product.price * item.quantity).toFixed(2)}</p>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFromCart(item.product.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      Remove
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
          
          <div>
            <Card className="p-6 sticky top-24">
              <h3 className="text-xl font-semibold mb-4">Order Summary</h3>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between">
                  <span>Subtotal</span>
                  <span>₹{getTotalPrice().toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Shipping</span>
                  <span>Free</span>
                </div>
                <Separator />
                <div className="flex justify-between font-semibold text-lg">
                  <span>Total</span>
                  <span>${getTotalPrice().toFixed(2)}</span>
                </div>
              </div>
              
              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={handleCheckout}
                  disabled={isCheckingOut || !user}
                >
                  {isCheckingOut ? 'Processing...' : 'Proceed to Checkout'}
                </Button>
                {!user && (
                  <p className="text-sm text-gray-600 text-center">
                    Please <a href="/login" className="text-blue-600 hover:underline">login</a> to checkout
                  </p>
                )}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={clearCart}
                >
                  Clear Cart
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// Auth Pages
const LoginPage = () => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);
      window.location.href = '/';
    } catch (error) {
      // Error handled in auth context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome Back</CardTitle>
          <CardDescription>Sign in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Signing In...' : 'Sign In'}
            </Button>
          </form>
          <p className="text-center mt-4 text-sm text-gray-600">
            Don't have an account?{' '}
            <a href="/register" className="text-blue-600 hover:underline">
              Sign up
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

const RegisterPage = () => {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await register(name, email, password);
      window.location.href = '/';
    } catch (error) {
      // Error handled in auth context
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Create Account</CardTitle>
          <CardDescription>Sign up for a new account</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </Button>
          </form>
          <p className="text-center mt-4 text-sm text-gray-600">
            Already have an account?{' '}
            <a href="/login" className="text-blue-600 hover:underline">
              Sign in
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

// Checkout Success Page
const CheckoutSuccessPage = () => {
  const { clearCart } = useCart();
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState('');
  const [paymentStatus, setPaymentStatus] = useState('pending');
  const [isLoading, setIsLoading] = useState(true);

  if (user?.role === 'admin') {
    return <Navigate to="/admin" replace />;
  }

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const session_id = urlParams.get('session_id');
    
    if (session_id) {
      setSessionId(session_id);
      pollPaymentStatus(session_id);
    } else {
      setIsLoading(false);
    }
  }, []);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 10;
    
    if (attempts >= maxAttempts) {
      setPaymentStatus('timeout');
      setIsLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`);
      const status = response.data.payment_status;
      
      setPaymentStatus(status);
      
      if (status === 'paid') {
        clearCart();
        setIsLoading(false);
        toast.success('Payment successful! Thank you for your purchase.');
      } else if (status === 'expired') {
        setIsLoading(false);
      } else {
        // Continue polling
        setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), 2000);
      }
    } catch (error) {
      console.error('Error checking payment status:', error);
      setPaymentStatus('error');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md text-center p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold mb-2">Processing Payment...</h2>
          <p className="text-gray-600">Please wait while we confirm your payment.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
      <Card className="w-full max-w-md text-center">
        <CardContent className="p-8">
          {paymentStatus === 'paid' ? (
            <>
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-green-600 mb-2">Payment Successful!</h2>
              <p className="text-gray-600 mb-6">Thank you for your purchase. Your order has been confirmed.</p>
            </>
          ) : paymentStatus === 'expired' ? (
            <>
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <X className="h-8 w-8 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold text-red-600 mb-2">Payment Expired</h2>
              <p className="text-gray-600 mb-6">Your payment session has expired. Please try again.</p>
            </>
          ) : (
            <>
              <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CreditCard className="h-8 w-8 text-yellow-600" />
              </div>
              <h2 className="text-2xl font-bold text-yellow-600 mb-2">Payment Processing</h2>
              <p className="text-gray-600 mb-6">We're still processing your payment. Please check back shortly.</p>
            </>
          )}
          
          <div className="space-y-3">
            <a href="/products">
              <Button className="w-full">Continue Shopping</Button>
            </a>
            {user && (
              <a href="/profile">
                <Button variant="outline" className="w-full">View Orders</Button>
              </a>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Help Center Page
const HelpPage = () => {
  const [faqs, setFaqs] = useState([]);
  const [supportForm, setSupportForm] = useState({
    name: '',
    email: '',
    subject: '',
    description: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [activeTab, setActiveTab] = useState('faq');

  useEffect(() => {
    fetchFAQs();

    // Check URL parameters for tab
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    if (tab === 'support') {
      setActiveTab('support');
    }
  }, []);

  const fetchFAQs = async () => {
    try {
      const response = await axios.get(`${API}/faqs`);
      setFaqs(response.data);
    } catch (error) {
      console.error('Error fetching FAQs:', error);
    }
  };

  const handleSupportSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      await axios.post(`${API}/api/support/tickets`, supportForm);
      toast.success('Support ticket submitted successfully!');
      setSupportForm({ name: '', email: '', subject: '', description: '' });
    } catch (error) {
      toast.error('Failed to submit support ticket');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8">Help Center</h1>
        
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="faq">FAQ</TabsTrigger>
            <TabsTrigger value="support">Contact Support</TabsTrigger>
          </TabsList>
          
          <TabsContent value="faq" className="mt-8">
            <div className="space-y-4">
              <h2 className="text-2xl font-semibold mb-6">Frequently Asked Questions</h2>
              {faqs.length > 0 ? (
                faqs.map(faq => (
                  <Card key={faq.id}>
                    <CardHeader>
                      <CardTitle className="text-lg">{faq.question}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-gray-600">{faq.answer}</p>
                      <Badge variant="secondary" className="mt-2">{faq.category}</Badge>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <HelpCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">No FAQs available at the moment.</p>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="support" className="mt-8">
            <Card>
              <CardHeader>
                <CardTitle>Contact Support</CardTitle>
                <CardDescription>
                  Need help? Send us a message and we'll get back to you as soon as possible.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSupportSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Name</Label>
                      <Input
                        id="name"
                        value={supportForm.name}
                        onChange={(e) => setSupportForm({...supportForm, name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={supportForm.email}
                        onChange={(e) => setSupportForm({...supportForm, email: e.target.value})}
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="subject">Subject</Label>
                    <Input
                      id="subject"
                      value={supportForm.subject}
                      onChange={(e) => setSupportForm({...supportForm, subject: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="description">Description</Label>
                    <textarea
                      id="description"
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      rows="4"
                      value={supportForm.description}
                      onChange={(e) => setSupportForm({...supportForm, description: e.target.value})}
                      required
                    />
                  </div>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : 'Submit Ticket'}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

// Contact Page
const ContactPage = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-4xl font-bold text-center mb-8">Contact Us</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Get in Touch</CardTitle>
              <CardDescription>
                We'd love to hear from you. Here's how you can reach us.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Mail className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Email</h3>
                  <p className="text-gray-600">support@shopmate.com</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Phone className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Phone</h3>
                  <p className="text-gray-600">+1 (555) 123-4567</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <MapPin className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <h3 className="font-semibold">Address</h3>
                  <p className="text-gray-600">
                    123 Commerce Street<br />
                    Business District<br />
                    City, State 12345
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>Business Hours</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span>Monday - Friday</span>
                <span>9:00 AM - 6:00 PM</span>
              </div>
              <div className="flex justify-between">
                <span>Saturday</span>
                <span>10:00 AM - 4:00 PM</span>
              </div>
              <div className="flex justify-between">
                <span>Sunday</span>
                <span>Closed</span>
              </div>
              <Separator />
              <p className="text-sm text-gray-600">
                Our customer support team is available during business hours to assist you with any questions or concerns.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

// Admin Dashboard
const AdminDashboard = () => {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState(null);
  const [counters, setCounters] = useState({
    total_products: 0,
    total_pending_orders: 0,
    total_users: 0,
    total_unresolved_tickets: 0
  });

  useEffect(() => {
    if (user?.role === 'admin') {
      fetchDashboardData();
      fetchCounters();

      // Set up real-time updates every 30 seconds
      const interval = setInterval(fetchCounters, 30000);

      return () => clearInterval(interval);
    }
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/dashboard`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    }
  };

  const fetchCounters = async () => {
    try {
      const response = await axios.get(`${API}/api/admin/dashboard/counters`);
      setCounters(response.data);
    } catch (error) {
      console.error('Error fetching counters:', error);
    }
  };

  if (!user || user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <h1 className="text-4xl font-bold mb-8">Admin Dashboard</h1>

        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Package className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Products</p>
                    <p className="text-2xl font-bold">{dashboardData.stats.total_products}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <ShoppingCart className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Orders</p>
                    <p className="text-2xl font-bold">{dashboardData.stats.total_orders}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold">{dashboardData.stats.total_users}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Ticket className="h-8 w-8 text-red-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Open Tickets</p>
                    <p className="text-2xl font-bold">{dashboardData.stats.open_tickets}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <a href="/admin/products">
              <Button className="w-full h-20 flex flex-col items-center justify-center relative">
                <Package className="h-6 w-6 mb-2" />
                <span className="text-sm font-medium">Manage Products</span>
                <span className="absolute top-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full">
                  {counters.total_products}
                </span>
              </Button>
            </a>
            <a href="/admin/orders">
              <Button className="w-full h-20 flex flex-col items-center justify-center relative">
                <ShoppingCart className="h-6 w-6 mb-2" />
                <span className="text-sm font-medium">View Orders</span>
                <span className="absolute top-2 right-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  {counters.total_pending_orders}
                </span>
              </Button>
            </a>
            <a href="/admin/users">
              <Button className="w-full h-20 flex flex-col items-center justify-center relative">
                <Users className="h-6 w-6 mb-2" />
                <span className="text-sm font-medium">Manage Users</span>
                <span className="absolute top-2 right-2 bg-purple-500 text-white text-xs px-2 py-1 rounded-full">
                  {counters.total_users}
                </span>
              </Button>
            </a>
            <a href="/admin/support-tickets">
              <Button className="w-full h-20 flex flex-col items-center justify-center relative">
                <Ticket className="h-6 w-6 mb-2" />
                <span className="text-sm font-medium">Support Tickets</span>
                <span className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                  {counters.total_unresolved_tickets}
                </span>
              </Button>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
};

// Profile Page Components
const ProfilePage = () => {
  return (
    <ProfileLayout>
      <ProfileInfo />
    </ProfileLayout>
  );
};

const ProfileTicketsPage = () => {
  return (
    <ProfileLayout>
      <MyTicketsPage />
    </ProfileLayout>
  );
};

const ProfileSettingsPage = () => {
  return (
    <ProfileLayout>
      <SettingsPage />
    </ProfileLayout>
  );
};

const ProfileOrdersPage = () => {
  return (
    <ProfileLayout>
      <OrderHistoryPage />
    </ProfileLayout>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  return children;
};

// Main App Component
function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <CartProvider>
          <Router>
            <div className="App">
              <Navigation />
              <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/products" element={<ProductsPage />} />
              <Route path="/cart" element={<CartPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/help" element={<HelpPage />} />
              <Route path="/contact" element={<ContactPage />} />
              {/* Removed CheckoutPage route because component is missing */}
              <Route path="/checkout/success" element={<CheckoutSuccessPage />} />
              <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/order-success/:orderId" element={
                <ProtectedRoute>
                  <OrderSuccessPage />
                </ProtectedRoute>
              } />
            <Route path="/profile" element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              } />
            <Route path="/profile/tickets" element={
                <ProtectedRoute>
                  <ProfileTicketsPage />
                </ProtectedRoute>
              } />
            <Route path="/profile/settings" element={
                <ProtectedRoute>
                  <ProfileSettingsPage />
                </ProtectedRoute>
              } />
            <Route path="/profile/orders" element={
                <ProtectedRoute>
                  <ProfileOrdersPage />
                </ProtectedRoute>
              } />
              <Route path="/admin" element={
                <ProtectedRoute adminOnly>
                  <AdminDashboard />
                </ProtectedRoute>
              } />
              <Route path="/admin/products" element={
                <ProtectedRoute adminOnly>
                  <ProductManagement />
                </ProtectedRoute>
              } />
              <Route path="/admin/users" element={
                <ProtectedRoute adminOnly>
                  <UserManagement />
                </ProtectedRoute>
              } />
              <Route path="/admin/orders" element={
                <ProtectedRoute adminOnly>
                  <OrderManagement />
                </ProtectedRoute>
              } />
              <Route path="/admin/support-tickets" element={
                <ProtectedRoute adminOnly>
                  <SupportTicketManagement />
                </ProtectedRoute>
              } />
            </Routes>
            <Toaster />
          </div>
        </Router>
      </CartProvider>
    </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
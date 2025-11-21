import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const emptyProduct = {
  name: '',
  description: '',
  price: 0,
  category: '',
  stock: 0,
  images: []
};

const ProductManagement = () => {
  const [products, setProducts] = useState([]);
  const [editingProduct, setEditingProduct] = useState(null);
  const [form, setForm] = useState(emptyProduct);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API}/api/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('Failed to fetch products');
      // Set empty array to prevent rendering errors
      setProducts([]);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: name === 'price' || name === 'stock' ? Number(value) : value }));
  };

  // New state for selected files and previews
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previewUrls, setPreviewUrls] = useState([]);

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);

    const urls = files.map(file => URL.createObjectURL(file));
    setPreviewUrls(urls);
  };

  const handleAddProduct = () => {
    setForm(emptyProduct);
    setSelectedFiles([]);
    setPreviewUrls([]);
    setIsEditing(true);
    setEditingProduct(null);
  };

  const handleEditProduct = (product) => {
    setForm(product);
    setSelectedFiles([]);
    setPreviewUrls(product.images || []);
    setIsEditing(true);
    setEditingProduct(product);
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    try {
      await axios.delete(`${API}/api/products/${productId}`);
      toast.success('Product deleted');
      fetchProducts();
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      let imageUrls = form.images || [];

      if (selectedFiles.length > 0) {
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));

        const uploadResponse = await axios.post(`${API}/api/admin/upload-images`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        imageUrls = [...imageUrls, ...uploadResponse.data.urls];
      }

      const productData = { ...form, images: imageUrls };

      if (editingProduct) {
        await axios.put(`${API}/api/products/${editingProduct.id}`, productData);
        toast.success('Product updated');
      } else {
        await axios.post(`${API}/api/products`, productData);
        toast.success('Product added');
      }
      setIsEditing(false);
      fetchProducts();
    } catch (error) {
      toast.error('Failed to save product');
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setForm(emptyProduct);
    setEditingProduct(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center space-x-4">
            <a href="/admin">
              <Button className="flex items-center space-x-2 bg-black text-white hover:bg-gray-800">
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Button>
            </a>
            <h1 className="text-3xl font-bold">Manage Products</h1>
          </div>
          {!isEditing && (
            <Button onClick={handleAddProduct}>Add New Product</Button>
          )}
        </div>

        {isEditing ? (
          <form onSubmit={handleSubmit} className="space-y-4 max-w-xl">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" value={form.name} onChange={handleInputChange} required />
            </div>
            <div>
              <Label htmlFor="description">Description</Label>
              <textarea
                id="description"
                name="description"
                value={form.description}
                onChange={handleInputChange}
                className="w-full p-2 border rounded"
                required
              />
            </div>
            <div>
              <Label htmlFor="price">Price</Label>
              <Input id="price" name="price" type="number" step="0.01" value={form.price} onChange={handleInputChange} required />
            </div>
            <div>
              <Label htmlFor="category">Category</Label>
              <Input id="category" name="category" value={form.category} onChange={handleInputChange} required />
            </div>
            <div>
              <Label htmlFor="stock">Stock</Label>
              <Input id="stock" name="stock" type="number" value={form.stock} onChange={handleInputChange} required />
            </div>
            <div>
              <Label htmlFor="images">Product Images</Label>
              <Input
                id="images"
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileChange}
              />
              {previewUrls.length > 0 && (
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {previewUrls.map((url, index) => (
                    <img key={index} src={url} alt={`Preview ${index + 1}`} className="w-full h-20 object-cover rounded" />
                  ))}
                </div>
              )}
            </div>
            <div className="space-x-4">
              <Button type="submit">Save</Button>
              <Button variant="outline" onClick={handleCancel}>Cancel</Button>
            </div>
          </form>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {products.map(product => (
              <Card key={product.id}>
                <CardHeader>
                  <CardTitle>{product.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  {product.images && product.images.length > 0 && (
                    <div className="mb-4">
                      <img
                        src={product.images[0]}
                        alt={product.name}
                        className="w-full h-32 object-cover rounded"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}
                  <p>{product.description}</p>
                  <p className="font-semibold">₹{product.price.toFixed(2)}</p>
                  <p>Category: {product.category}</p>
                  <p>Stock: {product.stock}</p>
                  <div className="mt-4 flex space-x-2">
                    <Button size="sm" onClick={() => handleEditProduct(product)}>Edit</Button>
                    <Button size="sm" variant="destructive" onClick={() => handleDeleteProduct(product.id)}>Delete</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductManagement;

import React, { createContext, useContext, useState, useEffect } from 'react';
import { cart as cartApi } from '../services/api';

const CartContext = createContext(null);

export const CartProvider = ({ children }) => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCartItems = async () => {
    try {
      setLoading(true);
      const response = await cartApi.getItems();
      setItems(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch cart items');
      console.error('Error fetching cart items:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCartItems();
  }, []);

  const addToCart = async (agentId) => {
    try {
      await cartApi.addItem(agentId);
      await fetchCartItems();
    } catch (err) {
      setError('Failed to add item to cart');
      console.error('Error adding item to cart:', err);
      throw err;
    }
  };

  const removeFromCart = async (agentId) => {
    try {
      await cartApi.removeItem(agentId);
      await fetchCartItems();
    } catch (err) {
      setError('Failed to remove item from cart');
      console.error('Error removing item from cart:', err);
      throw err;
    }
  };

  const checkout = async () => {
    try {
      await cartApi.checkout();
      setItems([]);
    } catch (err) {
      setError('Failed to checkout');
      console.error('Error during checkout:', err);
      throw err;
    }
  };

  const value = {
    items,
    loading,
    error,
    addToCart,
    removeFromCart,
    checkout,
    refreshCart: fetchCartItems
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export default CartContext; 
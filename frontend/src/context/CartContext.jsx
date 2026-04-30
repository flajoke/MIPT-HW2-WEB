import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { getProductById } from '../data/products.js';

const CART_STORAGE_KEY = 'lvd-store-cart';

const CartContext = createContext(null);

const normalizeCart = (value) => {
  if (!value || typeof value !== 'object') return {};

  return Object.entries(value).reduce((acc, [productId, qty]) => {
    const product = getProductById(productId);
    const normalizedQty = Number(qty);
    if (product && normalizedQty > 0) {
      acc[productId] = Math.min(normalizedQty, product.stockQty || normalizedQty);
    }
    return acc;
  }, {});
};

export function CartProvider({ children }) {
  const [quantities, setQuantities] = useState(() => {
    try {
      return normalizeCart(JSON.parse(localStorage.getItem(CART_STORAGE_KEY)));
    } catch {
      return {};
    }
  });

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(quantities));
  }, [quantities]);

  const cartItems = useMemo(
    () =>
      Object.entries(quantities)
        .map(([productId, qty]) => {
          const product = getProductById(productId);
          return product ? { product, qty, lineTotal: product.price * qty } : null;
        })
        .filter(Boolean),
    [quantities],
  );

  const cartCount = useMemo(
    () => cartItems.reduce((sum, item) => sum + item.qty, 0),
    [cartItems],
  );

  const subtotal = useMemo(
    () => cartItems.reduce((sum, item) => sum + item.lineTotal, 0),
    [cartItems],
  );

  const addItem = (product, qty = 1) => {
    if (!product || product.stockQty <= 0) return;
    setQuantities((current) => {
      const currentQty = current[product.id] || 0;
      return {
        ...current,
        [product.id]: Math.min(currentQty + qty, product.stockQty),
      };
    });
  };

  const updateItem = (productId, qty) => {
    const product = getProductById(productId);
    if (!product) return;
    setQuantities((current) => {
      const next = { ...current };
      const normalizedQty = Math.max(0, Math.min(Number(qty) || 0, product.stockQty));
      if (normalizedQty === 0) {
        delete next[productId];
      } else {
        next[productId] = normalizedQty;
      }
      return next;
    });
  };

  const removeItem = (productId) => {
    setQuantities((current) => {
      const next = { ...current };
      delete next[productId];
      return next;
    });
  };

  const clearCart = () => setQuantities({});

  const value = {
    cartItems,
    cartCount,
    subtotal,
    addItem,
    updateItem,
    removeItem,
    clearCart,
  };

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used inside CartProvider');
  }
  return context;
};

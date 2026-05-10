import { configureStore } from '@reduxjs/toolkit';
import cartReducer from './cartSlice.js';
import ordersReducer from './ordersSlice.js';
import productsReducer from './productsSlice.js';

export const store = configureStore({
  reducer: {
    products: productsReducer,
    cart: cartReducer,
    orders: ordersReducer,
  },
});

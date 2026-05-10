import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { orderApi } from '../services/api.js';
import { fetchProducts } from './productsSlice.js';
import { getSessionId } from './session.js';

const readError = (error) => error.message || 'Ошибка корзины';

export const fetchCart = createAsyncThunk('cart/fetchCart', async (_, { rejectWithValue }) => {
  try {
    return await orderApi.getCart(getSessionId());
  } catch (error) {
    return rejectWithValue(readError(error));
  }
});

export const addCartItem = createAsyncThunk('cart/addCartItem', async ({ productId, qty = 1 }, { dispatch, rejectWithValue }) => {
  try {
    const cart = await orderApi.addCartItem(getSessionId(), { product_id: productId, qty });
    dispatch(fetchProducts());
    return cart;
  } catch (error) {
    return rejectWithValue(readError(error));
  }
});

export const updateCartItem = createAsyncThunk('cart/updateCartItem', async ({ itemId, qty }, { dispatch, rejectWithValue }) => {
  try {
    const cart = await orderApi.updateCartItem(getSessionId(), itemId, { qty });
    dispatch(fetchProducts());
    return cart;
  } catch (error) {
    return rejectWithValue(readError(error));
  }
});

export const removeCartItem = createAsyncThunk('cart/removeCartItem', async ({ itemId }, { dispatch, rejectWithValue }) => {
  try {
    await orderApi.deleteCartItem(getSessionId(), itemId);
    const cart = await orderApi.getCart(getSessionId());
    dispatch(fetchProducts());
    return cart;
  } catch (error) {
    return rejectWithValue(readError(error));
  }
});

const cartSlice = createSlice({
  name: 'cart',
  initialState: {
    cart: null,
    status: 'idle',
    actionStatus: 'idle',
    error: null,
  },
  reducers: {
    clearCartError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchCart.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchCart.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.cart = action.payload;
      })
      .addCase(fetchCart.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || action.error.message;
      })
      .addMatcher(
        (action) => [addCartItem.pending.type, updateCartItem.pending.type, removeCartItem.pending.type].includes(action.type),
        (state) => {
          state.actionStatus = 'loading';
          state.error = null;
        },
      )
      .addMatcher(
        (action) => [addCartItem.fulfilled.type, updateCartItem.fulfilled.type, removeCartItem.fulfilled.type].includes(action.type),
        (state, action) => {
          state.actionStatus = 'succeeded';
          state.cart = action.payload;
        },
      )
      .addMatcher(
        (action) => [addCartItem.rejected.type, updateCartItem.rejected.type, removeCartItem.rejected.type].includes(action.type),
        (state, action) => {
          state.actionStatus = 'failed';
          state.error = action.payload || action.error.message;
        },
      );
  },
});

export const { clearCartError } = cartSlice.actions;

export const selectCart = (state) => state.cart.cart;
export const selectCartItems = (state) => state.cart.cart?.items || [];
export const selectCartSubtotal = (state) => Number(state.cart.cart?.subtotal || 0);
export const selectCartCount = (state) => selectCartItems(state).reduce((sum, item) => sum + Number(item.qty || 0), 0);
export const selectCartStatus = (state) => state.cart.status;
export const selectCartActionStatus = (state) => state.cart.actionStatus;
export const selectCartError = (state) => state.cart.error;

export default cartSlice.reducer;

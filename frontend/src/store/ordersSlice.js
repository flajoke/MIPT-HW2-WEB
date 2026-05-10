import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { orderApi } from '../services/api.js';
import { getSessionId } from './session.js';

export const createOrder = createAsyncThunk('orders/createOrder', async ({ form, deliveryCost }, { rejectWithValue }) => {
  try {
    const address = form.deliveryType === 'pickup' ? 'Самовывоз из пункта выдачи' : form.address.trim();
    const commentParts = [
      `Способ получения: ${form.deliveryType === 'pickup' ? 'самовывоз' : 'курьер'}`,
      `Оплата: ${form.paymentType === 'cash' ? 'при получении' : 'картой онлайн'}`,
      form.comment.trim(),
    ].filter(Boolean);

    return await orderApi.createOrder({
      session_id: getSessionId(),
      customer_name: form.name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim(),
      city: form.city.trim(),
      address,
      comment: commentParts.join('\n'),
      delivery_cost: deliveryCost,
    });
  } catch (error) {
    return rejectWithValue(error.message || 'Не удалось оформить заказ');
  }
});

export const fetchOrders = createAsyncThunk('orders/fetchOrders', async (_, { rejectWithValue }) => {
  try {
    return await orderApi.getOrders({ limit: 20 });
  } catch (error) {
    return rejectWithValue(error.message || 'Не удалось загрузить заказы');
  }
});

const ordersSlice = createSlice({
  name: 'orders',
  initialState: {
    items: [],
    lastCreatedOrder: null,
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(createOrder.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(createOrder.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.lastCreatedOrder = action.payload;
        state.items = [action.payload, ...state.items.filter((order) => order.id !== action.payload.id)];
      })
      .addCase(createOrder.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || action.error.message;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.items = action.payload.items || [];
      });
  },
});

export const selectOrders = (state) => state.orders.items;
export const selectLastCreatedOrder = (state) => state.orders.lastCreatedOrder;
export const selectOrdersStatus = (state) => state.orders.status;
export const selectOrdersError = (state) => state.orders.error;

export default ordersSlice.reducer;

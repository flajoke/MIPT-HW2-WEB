import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import { catalogApi } from '../services/api.js';

const imageThemes = ['warm', 'amber', 'soft', 'neutral', 'graphite', 'festive', 'cool'];

const normalizeProduct = (product, index = 0) => {
  const categoryName = product.category?.name || 'Без категории';
  const categoryCode = product.category?.code || product.category_id;
  const availableQty = Number(product.available_qty ?? product.stock_qty ?? 0);
  const stockQty = Number(product.stock_qty ?? availableQty);
  const reservedQty = Number(product.reserved_qty ?? 0);
  const isActive = product.status === 'ACTIVE';

  return {
    id: product.id,
    sku: product.sku,
    slug: product.slug,
    name: product.name,
    categoryId: categoryCode,
    categoryUuid: product.category_id,
    category: categoryName,
    description: product.description || 'Описание товара будет дополнено менеджером каталога.',
    price: Number(product.price || 0),
    currency: product.currency || 'RUB',
    stockQty: availableQty,
    totalStockQty: stockQty,
    reservedQty,
    socketType: product.socket_type,
    wattage: Number(product.wattage || 0),
    colorTemperature: Number(product.color_temperature || 0),
    voltage: Number(product.voltage || 220),
    status: product.status,
    lifetime: '30 000 часов',
    warranty: '24 месяца',
    badges: [isActive ? 'В наличии' : 'Нет в наличии', reservedQty > 0 ? `Зарезервировано: ${reservedQty}` : 'Склад online'],
    imageTheme: imageThemes[index % imageThemes.length],
    images: product.images || [],
  };
};

export const fetchProducts = createAsyncThunk('products/fetchProducts', async (_, { rejectWithValue }) => {
  try {
    const payload = await catalogApi.getProducts({ limit: 100, sort_by: 'name', sort_order: 'asc' });
    return (payload.items || []).map(normalizeProduct);
  } catch (error) {
    return rejectWithValue(error.message || 'Не удалось загрузить товары');
  }
});

const productsSlice = createSlice({
  name: 'products',
  initialState: {
    items: [],
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.items = action.payload;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload || action.error.message;
      });
  },
});

export const selectProducts = (state) => state.products.items;
export const selectProductsStatus = (state) => state.products.status;
export const selectProductsError = (state) => state.products.error;
export const selectProductBySlug = (state, slug) => state.products.items.find((product) => product.slug === slug);
export const selectProductById = (state, productId) => state.products.items.find((product) => product.id === productId);

export default productsSlice.reducer;

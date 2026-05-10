const CATALOG_API_URL = (import.meta.env.VITE_CATALOG_API_URL || 'http://localhost:8081').replace(/\/$/, '');
const ORDER_API_URL = (import.meta.env.VITE_ORDER_API_URL || 'http://localhost:8082').replace(/\/$/, '');

async function request(baseUrl, path, options = {}) {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = payload?.error || `HTTP ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.details = payload?.details;
    throw error;
  }

  return payload;
}

const buildQuery = (params = {}) => {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const queryString = query.toString();
  return queryString ? `?${queryString}` : '';
};

export const catalogApi = {
  getProducts(params = {}) {
    return request(CATALOG_API_URL, `/api/v1/products${buildQuery(params)}`);
  },

  getProduct(productId) {
    return request(CATALOG_API_URL, `/api/v1/products/${encodeURIComponent(productId)}`);
  },
};

export const orderApi = {
  getCart(sessionId) {
    return request(ORDER_API_URL, `/api/v1/carts/${encodeURIComponent(sessionId)}`);
  },

  addCartItem(sessionId, data) {
    return request(ORDER_API_URL, `/api/v1/carts/${encodeURIComponent(sessionId)}/items`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateCartItem(sessionId, itemId, data) {
    return request(ORDER_API_URL, `/api/v1/carts/${encodeURIComponent(sessionId)}/items/${encodeURIComponent(itemId)}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  deleteCartItem(sessionId, itemId) {
    return request(ORDER_API_URL, `/api/v1/carts/${encodeURIComponent(sessionId)}/items/${encodeURIComponent(itemId)}`, {
      method: 'DELETE',
    });
  },

  createOrder(data) {
    return request(ORDER_API_URL, '/api/v1/orders', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  getOrders(params = {}) {
    return request(ORDER_API_URL, `/api/v1/orders${buildQuery(params)}`);
  },
};

export const getBackendUrls = () => ({
  catalog: CATALOG_API_URL,
  orders: ORDER_API_URL,
});

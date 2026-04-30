export const formatPrice = (value, currency = 'RUB') =>
  new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(value);

export const formatColorTemperature = (value) => {
  if (!value) return 'RGB';
  return `${value.toLocaleString('ru-RU')} K`;
};

export const getDeliveryCost = (subtotal, deliveryType) => {
  if (deliveryType === 'pickup') return 0;
  if (subtotal >= 3000) return 0;
  return 350;
};

export const createOrderNumber = () => {
  const now = new Date();
  const date = now.toISOString().slice(0, 10).replaceAll('-', '');
  const suffix = Math.floor(1000 + Math.random() * 9000);
  return `ORD-${date}-${suffix}`;
};

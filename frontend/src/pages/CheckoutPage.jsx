import { useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import OrderSummary from '../components/OrderSummary.jsx';
import { fetchCart, selectCartItems, selectCartStatus, selectCartSubtotal } from '../store/cartSlice.js';
import { createOrder, selectOrdersError, selectOrdersStatus } from '../store/ordersSlice.js';
import { fetchProducts } from '../store/productsSlice.js';
import { getDeliveryCost } from '../utils/formatters.js';

const initialForm = {
  name: '',
  phone: '',
  email: '',
  city: '',
  address: '',
  deliveryType: 'courier',
  paymentType: 'card',
  comment: '',
  agreement: false,
};

const validateForm = (form) => {
  const errors = {};
  if (form.name.trim().length < 2) errors.name = 'Укажите имя получателя';
  if (!/^\+?[\d\s()\-]{10,}$/.test(form.phone.trim())) errors.phone = 'Укажите корректный телефон';
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) errors.email = 'Укажите корректный email';
  if (form.city.trim().length < 2) errors.city = 'Укажите город';
  if (form.deliveryType === 'courier' && form.address.trim().length < 5) errors.address = 'Укажите адрес доставки';
  if (!form.agreement) errors.agreement = 'Нужно подтвердить согласие с условиями';
  return errors;
};

function CheckoutPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const cartItems = useSelector(selectCartItems);
  const subtotal = useSelector(selectCartSubtotal);
  const cartStatus = useSelector(selectCartStatus);
  const orderStatus = useSelector(selectOrdersStatus);
  const orderError = useSelector(selectOrdersError);
  const [form, setForm] = useState(initialForm);
  const [errors, setErrors] = useState({});

  const deliveryCost = useMemo(() => getDeliveryCost(subtotal, form.deliveryType), [subtotal, form.deliveryType]);

  if (cartStatus === 'loading') {
    return <div className="container"><div className="info-banner">Проверяем корзину перед оформлением...</div></div>;
  }

  if (cartItems.length === 0) {
    return <Navigate to="/cart" replace />;
  }

  const setField = (field, value) => {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: undefined }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextErrors = validateForm(form);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) return;

    try {
      const order = await dispatch(createOrder({ form, deliveryCost })).unwrap();
      localStorage.setItem('lvd-store-last-order', JSON.stringify(order));
      await dispatch(fetchCart());
      await dispatch(fetchProducts());
      navigate('/confirmation', { state: { order } });
    } catch {
      // Текст ошибки уже лежит в Redux и выводится ниже формы.
    }
  };

  const isSubmitting = orderStatus === 'loading';

  return (
    <div className="container page-stack">
      <nav className="breadcrumbs" aria-label="Хлебные крошки">
        <Link to="/cart">Корзина</Link>
        <span>/</span>
        <span>Оформление заказа</span>
      </nav>

      <div className="section-heading">
        <div>
          <span className="eyebrow">Оформление</span>
          <h1>Контактные данные и доставка</h1>
        </div>
      </div>

      <section className="checkout-layout">
        <form className="checkout-form" onSubmit={handleSubmit} noValidate>
          <fieldset>
            <legend>Получатель</legend>
            <div className="form-grid">
              <label>
                Имя и фамилия
                <input value={form.name} onChange={(event) => setField('name', event.target.value)} placeholder="Иван Иванов" />
                {errors.name && <small>{errors.name}</small>}
              </label>
              <label>
                Телефон
                <input value={form.phone} onChange={(event) => setField('phone', event.target.value)} placeholder="+7 999 000-00-00" />
                {errors.phone && <small>{errors.phone}</small>}
              </label>
              <label>
                Email
                <input type="email" value={form.email} onChange={(event) => setField('email', event.target.value)} placeholder="mail@example.com" />
                {errors.email && <small>{errors.email}</small>}
              </label>
              <label>
                Город
                <input value={form.city} onChange={(event) => setField('city', event.target.value)} placeholder="Москва" />
                {errors.city && <small>{errors.city}</small>}
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Способ получения</legend>
            <div className="radio-grid">
              <label className="radio-card">
                <input
                  type="radio"
                  name="deliveryType"
                  value="courier"
                  checked={form.deliveryType === 'courier'}
                  onChange={(event) => setField('deliveryType', event.target.value)}
                />
                <span>Курьер</span>
                <small>По адресу, от 350 ₽</small>
              </label>
              <label className="radio-card">
                <input
                  type="radio"
                  name="deliveryType"
                  value="pickup"
                  checked={form.deliveryType === 'pickup'}
                  onChange={(event) => setField('deliveryType', event.target.value)}
                />
                <span>Самовывоз</span>
                <small>Бесплатно из пункта выдачи</small>
              </label>
            </div>
            <label>
              Адрес
              <input
                value={form.address}
                onChange={(event) => setField('address', event.target.value)}
                placeholder={form.deliveryType === 'courier' ? 'Улица, дом, квартира' : 'Можно оставить пустым'}
              />
              {errors.address && <small>{errors.address}</small>}
            </label>
          </fieldset>

          <fieldset>
            <legend>Оплата</legend>
            <div className="radio-grid">
              <label className="radio-card">
                <input
                  type="radio"
                  name="paymentType"
                  value="card"
                  checked={form.paymentType === 'card'}
                  onChange={(event) => setField('paymentType', event.target.value)}
                />
                <span>Картой онлайн</span>
                <small>Учебный сценарий без реального платежа</small>
              </label>
              <label className="radio-card">
                <input
                  type="radio"
                  name="paymentType"
                  value="cash"
                  checked={form.paymentType === 'cash'}
                  onChange={(event) => setField('paymentType', event.target.value)}
                />
                <span>При получении</span>
                <small>Наличными или картой курьеру</small>
              </label>
            </div>
          </fieldset>

          <label>
            Комментарий к заказу
            <textarea value={form.comment} onChange={(event) => setField('comment', event.target.value)} placeholder="Например, удобное время доставки" rows="4" />
          </label>

          <label className="checkbox-row">
            <input type="checkbox" checked={form.agreement} onChange={(event) => setField('agreement', event.target.checked)} />
            <span>Я согласен с условиями обработки заказа и понимаю, что это учебная форма без реальной оплаты.</span>
          </label>
          {errors.agreement && <small className="form-error">{errors.agreement}</small>}
          {orderError && <div className="error-banner">Ошибка оформления: {orderError}</div>}

          <button className="button button--primary button--wide" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Отправляем заказ...' : 'Подтвердить заказ'}
          </button>
        </form>

        <OrderSummary
          subtotal={subtotal}
          deliveryCost={deliveryCost}
          note="После подтверждения order-service создаст заказ, а catalog-service спишет зарезервированный товар со склада."
        />
      </section>
    </div>
  );
}

export default CheckoutPage;

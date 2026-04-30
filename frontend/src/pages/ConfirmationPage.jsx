import { useMemo } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { formatPrice } from '../utils/formatters.js';

function readLastOrder() {
  try {
    return JSON.parse(localStorage.getItem('lvd-store-last-order'));
  } catch {
    return null;
  }
}

function ConfirmationPage() {
  const location = useLocation();
  const order = useMemo(() => location.state?.order || readLastOrder(), [location.state]);

  return (
    <div className="container page-stack">
      <section className="confirmation-card">
        <div className="confirmation-icon">✓</div>
        <span className="eyebrow">Заказ оформлен</span>
        <h1>Спасибо за заказ!</h1>
        {order ? (
          <>
            <p>
              Номер заказа <strong>{order.orderNumber}</strong> отправлен на {order.email}. Менеджер свяжется с вами для
              подтверждения деталей доставки.
            </p>
            <div className="confirmation-details">
              <div>
                <span>Получатель</span>
                <strong>{order.customerName}</strong>
              </div>
              <div>
                <span>Товаров</span>
                <strong>{order.itemsCount}</strong>
              </div>
              <div>
                <span>Доставка</span>
                <strong>{order.deliveryCost === 0 ? 'Бесплатно' : formatPrice(order.deliveryCost)}</strong>
              </div>
              <div>
                <span>Итого</span>
                <strong>{formatPrice(order.total)}</strong>
              </div>
            </div>
          </>
        ) : (
          <p>Данные последнего заказа не найдены. Можно вернуться в каталог и оформить новый заказ.</p>
        )}
        <div className="confirmation-actions">
          <Link className="button button--primary" to="/catalog">
            Вернуться в каталог
          </Link>
          <Link className="button button--ghost" to="/cart">
            Открыть корзину
          </Link>
        </div>
      </section>
    </div>
  );
}

export default ConfirmationPage;

import { useMemo } from 'react';
import { useSelector } from 'react-redux';
import { Link, useLocation } from 'react-router-dom';
import { selectLastCreatedOrder } from '../store/ordersSlice.js';
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
  const lastCreatedOrder = useSelector(selectLastCreatedOrder);
  const order = useMemo(() => location.state?.order || lastCreatedOrder || readLastOrder(), [lastCreatedOrder, location.state]);

  return (
    <div className="container page-stack">
      <section className="confirmation-card">
        <div className="confirmation-icon">✓</div>
        <span className="eyebrow">Заказ оформлен</span>
        <h1>Спасибо за заказ!</h1>
        {order ? (
          <>
            <p>
              Номер заказа <strong>{order.order_number}</strong> создан в order-service и отправлен на {order.email}.
              Менеджер свяжется с вами для подтверждения деталей доставки.
            </p>
            <div className="confirmation-details">
              <div>
                <span>Получатель</span>
                <strong>{order.customer_name}</strong>
              </div>
              <div>
                <span>Товаров</span>
                <strong>{order.items?.reduce((sum, item) => sum + item.qty, 0) || 0}</strong>
              </div>
              <div>
                <span>Статус</span>
                <strong>{order.status}</strong>
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

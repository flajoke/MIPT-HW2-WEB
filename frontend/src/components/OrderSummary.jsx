import { formatPrice } from '../utils/formatters.js';

function OrderSummary({ subtotal, deliveryCost = 0, cta, note }) {
  const total = subtotal + deliveryCost;

  return (
    <aside className="summary-card" aria-label="Итого по заказу">
      <h2>Ваш заказ</h2>
      <div className="summary-line">
        <span>Товары</span>
        <strong>{formatPrice(subtotal)}</strong>
      </div>
      <div className="summary-line">
        <span>Доставка</span>
        <strong>{deliveryCost === 0 ? 'Бесплатно' : formatPrice(deliveryCost)}</strong>
      </div>
      <div className="summary-total">
        <span>Итого</span>
        <strong>{formatPrice(total)}</strong>
      </div>
      {note && <p className="summary-note">{note}</p>}
      {cta}
    </aside>
  );
}

export default OrderSummary;

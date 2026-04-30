import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState.jsx';
import OrderSummary from '../components/OrderSummary.jsx';
import ProductVisual from '../components/ProductVisual.jsx';
import QuantityControl from '../components/QuantityControl.jsx';
import { useCart } from '../context/CartContext.jsx';
import { formatPrice } from '../utils/formatters.js';

function CartPage() {
  const { cartItems, subtotal, updateItem, removeItem } = useCart();

  if (cartItems.length === 0) {
    return <EmptyState title="Корзина пуста" text="Добавьте товары из каталога, чтобы перейти к оформлению заказа." />;
  }

  return (
    <div className="container page-stack">
      <div className="section-heading">
        <div>
          <span className="eyebrow">Корзина</span>
          <h1>Проверьте состав заказа</h1>
        </div>
        <Link to="/catalog" className="button button--ghost">
          Продолжить покупки
        </Link>
      </div>

      <section className="cart-layout">
        <div className="cart-list">
          {cartItems.map(({ product, qty, lineTotal }) => (
            <article key={product.id} className="cart-item">
              <ProductVisual product={product} size="small" />
              <div className="cart-item__content">
                <Link to={`/product/${product.slug}`} className="cart-item__title">
                  {product.name}
                </Link>
                <span>Артикул: {product.sku}</span>
                <button className="link-button" type="button" onClick={() => removeItem(product.id)}>
                  Удалить
                </button>
              </div>
              <div className="cart-item__controls">
                <QuantityControl value={qty} min={1} max={product.stockQty} onChange={(nextQty) => updateItem(product.id, nextQty)} />
                <strong>{formatPrice(lineTotal, product.currency)}</strong>
              </div>
            </article>
          ))}
        </div>

        <OrderSummary
          subtotal={subtotal}
          note="Бесплатная доставка доступна при заказе от 3 000 ₽. Итоговая стоимость доставки уточняется на следующем шаге."
          cta={
            <Link className="button button--primary button--full" to="/checkout">
              Оформить заказ
            </Link>
          }
        />
      </section>
    </div>
  );
}

export default CartPage;

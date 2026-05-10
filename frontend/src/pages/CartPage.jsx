import { useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import EmptyState from '../components/EmptyState.jsx';
import OrderSummary from '../components/OrderSummary.jsx';
import ProductVisual from '../components/ProductVisual.jsx';
import QuantityControl from '../components/QuantityControl.jsx';
import {
  removeCartItem,
  selectCartActionStatus,
  selectCartError,
  selectCartItems,
  selectCartStatus,
  selectCartSubtotal,
  updateCartItem,
} from '../store/cartSlice.js';
import { selectProducts } from '../store/productsSlice.js';
import { formatPrice } from '../utils/formatters.js';

const fallbackProduct = (item) => ({
  id: item.product_id,
  name: item.product_name,
  slug: '',
  sku: item.sku,
  imageTheme: 'warm',
  currency: 'RUB',
  stockQty: item.qty,
});

function CartPage() {
  const dispatch = useDispatch();
  const rawItems = useSelector(selectCartItems);
  const subtotal = useSelector(selectCartSubtotal);
  const cartStatus = useSelector(selectCartStatus);
  const actionStatus = useSelector(selectCartActionStatus);
  const error = useSelector(selectCartError);
  const products = useSelector(selectProducts);

  const productsById = useMemo(() => new Map(products.map((product) => [product.id, product])), [products]);
  const cartItems = useMemo(
    () => rawItems.map((item) => ({ ...item, product: productsById.get(item.product_id) || fallbackProduct(item) })),
    [productsById, rawItems],
  );

  if (cartStatus === 'loading') {
    return <div className="container"><div className="info-banner">Загружаем корзину из order-service...</div></div>;
  }

  if (cartItems.length === 0) {
    return <EmptyState title="Корзина пуста" text="Добавьте товары из каталога, чтобы перейти к оформлению заказа." />;
  }

  const isBusy = actionStatus === 'loading';

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

      {error && <div className="error-banner">Ошибка корзины: {error}</div>}

      <section className="cart-layout">
        <div className="cart-list">
          {cartItems.map((item) => {
            const product = item.product;
            const maxQty = Math.max(Number(item.qty || 1), Number(item.qty || 0) + Number(product.stockQty || 0));
            const productUrl = product.slug ? `/product/${product.slug}` : '/catalog';

            return (
              <article key={item.id} className="cart-item">
                <ProductVisual product={product} size="small" />
                <div className="cart-item__content">
                  <Link to={productUrl} className="cart-item__title">
                    {item.product_name}
                  </Link>
                  <span>Артикул: {item.sku}</span>
                  <span>Позиция backend: {item.id}</span>
                  <button className="link-button" type="button" disabled={isBusy} onClick={() => dispatch(removeCartItem({ itemId: item.id }))}>
                    Удалить
                  </button>
                </div>
                <div className="cart-item__controls">
                  <QuantityControl
                    value={item.qty}
                    min={1}
                    max={maxQty}
                    onChange={(nextQty) => dispatch(updateCartItem({ itemId: item.id, qty: nextQty }))}
                  />
                  <strong>{formatPrice(item.line_total, product.currency)}</strong>
                </div>
              </article>
            );
          })}
        </div>

        <OrderSummary
          subtotal={subtotal}
          note="Количество и состав корзины сохраняются в order-service. При оформлении заказа backend спишет зарезервированный товар со склада."
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

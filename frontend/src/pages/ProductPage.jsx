import { useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, Navigate, useParams } from 'react-router-dom';
import ProductVisual from '../components/ProductVisual.jsx';
import QuantityControl from '../components/QuantityControl.jsx';
import { addCartItem, selectCartActionStatus } from '../store/cartSlice.js';
import { selectProductBySlug, selectProducts, selectProductsStatus } from '../store/productsSlice.js';
import { formatColorTemperature, formatPrice } from '../utils/formatters.js';

function ProductPage() {
  const { slug } = useParams();
  const dispatch = useDispatch();
  const product = useSelector((state) => selectProductBySlug(state, slug));
  const products = useSelector(selectProducts);
  const productsStatus = useSelector(selectProductsStatus);
  const cartActionStatus = useSelector(selectCartActionStatus);
  const [qty, setQty] = useState(1);

  const relatedProducts = useMemo(() => {
    if (!product) return [];
    return products.filter((item) => item.categoryId === product.categoryId && item.id !== product.id).slice(0, 3);
  }, [product, products]);

  if (productsStatus === 'loading' || productsStatus === 'idle') {
    return <div className="container"><div className="info-banner">Загружаем карточку товара из catalog-service...</div></div>;
  }

  if (!product) {
    return <Navigate to="/catalog" replace />;
  }

  const isAvailable = product.status === 'ACTIVE' && product.stockQty > 0;
  const isCartBusy = cartActionStatus === 'loading';

  return (
    <div className="container page-stack">
      <nav className="breadcrumbs" aria-label="Хлебные крошки">
        <Link to="/catalog">Каталог</Link>
        <span>/</span>
        <span>{product.name}</span>
      </nav>

      <section className="product-detail">
        <div className="product-detail__visual">
          <ProductVisual product={product} size="large" />
          <div className="badge-row">
            {product.badges.map((badge) => (
              <span key={badge}>{badge}</span>
            ))}
          </div>
        </div>

        <div className="product-detail__content">
          <span className="eyebrow">{product.category}</span>
          <h1>{product.name}</h1>
          <p>{product.description}</p>

          <div className="product-price-row">
            <div className="price-block price-block--big">
              <strong>{formatPrice(product.price, product.currency)}</strong>
            </div>
            <span className={isAvailable ? 'status status--success' : 'status status--muted'}>
              {isAvailable ? `Доступно: ${product.stockQty} шт.` : 'Нет в наличии'}
            </span>
          </div>

          <div className="product-actions">
            <QuantityControl value={qty} min={1} max={Math.max(product.stockQty, 1)} onChange={setQty} />
            <button
              className="button button--primary button--wide"
              type="button"
              disabled={!isAvailable || isCartBusy}
              onClick={() => dispatch(addCartItem({ productId: product.id, qty }))}
            >
              Добавить в корзину
            </button>
          </div>

          <dl className="spec-table">
            <div>
              <dt>Артикул</dt>
              <dd>{product.sku}</dd>
            </div>
            <div>
              <dt>Цоколь / подключение</dt>
              <dd>{product.socketType}</dd>
            </div>
            <div>
              <dt>Мощность</dt>
              <dd>{product.wattage} W</dd>
            </div>
            <div>
              <dt>Цветовая температура</dt>
              <dd>{formatColorTemperature(product.colorTemperature)}</dd>
            </div>
            <div>
              <dt>Напряжение</dt>
              <dd>{product.voltage} V</dd>
            </div>
            <div>
              <dt>Остаток на складе</dt>
              <dd>{product.totalStockQty} шт.</dd>
            </div>
            <div>
              <dt>В резерве</dt>
              <dd>{product.reservedQty} шт.</dd>
            </div>
            <div>
              <dt>Гарантия</dt>
              <dd>{product.warranty}</dd>
            </div>
          </dl>
        </div>
      </section>

      {relatedProducts.length > 0 && (
        <section className="related-card">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Похожие товары</span>
              <h2>Из этой же категории</h2>
            </div>
          </div>
          <div className="related-list">
            {relatedProducts.map((item) => (
              <Link key={item.id} to={`/product/${item.slug}`}>
                {item.name}
                <span>{formatPrice(item.price, item.currency)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default ProductPage;

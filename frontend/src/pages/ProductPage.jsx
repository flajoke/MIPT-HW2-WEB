import { useMemo, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import ProductVisual from '../components/ProductVisual.jsx';
import QuantityControl from '../components/QuantityControl.jsx';
import { getProductBySlug, products } from '../data/products.js';
import { useCart } from '../context/CartContext.jsx';
import { formatColorTemperature, formatPrice } from '../utils/formatters.js';

function ProductPage() {
  const { slug } = useParams();
  const product = getProductBySlug(slug);
  const [qty, setQty] = useState(1);
  const { addItem } = useCart();

  const relatedProducts = useMemo(() => {
    if (!product) return [];
    return products.filter((item) => item.categoryId === product.categoryId && item.id !== product.id).slice(0, 3);
  }, [product]);

  if (!product) {
    return <Navigate to="/catalog" replace />;
  }

  const isAvailable = product.stockQty > 0;

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
              {product.oldPrice && <span>{formatPrice(product.oldPrice, product.currency)}</span>}
            </div>
            <span className={isAvailable ? 'status status--success' : 'status status--muted'}>
              {isAvailable ? `В наличии: ${product.stockQty} шт.` : 'Нет в наличии'}
            </span>
          </div>

          <div className="product-actions">
            <QuantityControl value={qty} min={1} max={Math.max(product.stockQty, 1)} onChange={setQty} />
            <button
              className="button button--primary button--wide"
              type="button"
              disabled={!isAvailable}
              onClick={() => addItem(product, qty)}
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
              <dt>Срок службы</dt>
              <dd>{product.lifetime}</dd>
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

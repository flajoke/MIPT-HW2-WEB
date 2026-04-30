import { Link } from 'react-router-dom';
import { useCart } from '../context/CartContext.jsx';
import { formatColorTemperature, formatPrice } from '../utils/formatters.js';
import ProductVisual from './ProductVisual.jsx';

function ProductCard({ product }) {
  const { addItem } = useCart();
  const isAvailable = product.stockQty > 0;

  return (
    <article className="product-card">
      <Link to={`/product/${product.slug}`} className="product-card__image" aria-label={product.name}>
        <ProductVisual product={product} />
      </Link>

      <div className="product-card__content">
        <div className="product-card__meta">
          <span>{product.category}</span>
          <span>{product.stockQty > 0 ? `В наличии: ${product.stockQty}` : 'Нет в наличии'}</span>
        </div>

        <Link to={`/product/${product.slug}`} className="product-card__title">
          {product.name}
        </Link>

        <p>{product.description}</p>

        <div className="spec-pills" aria-label="Ключевые характеристики">
          <span>{product.wattage}W</span>
          <span>{product.socketType}</span>
          <span>{formatColorTemperature(product.colorTemperature)}</span>
        </div>

        <div className="product-card__footer">
          <div className="price-block">
            <strong>{formatPrice(product.price, product.currency)}</strong>
            {product.oldPrice && <span>{formatPrice(product.oldPrice, product.currency)}</span>}
          </div>
          <button className="button button--primary" type="button" disabled={!isAvailable} onClick={() => addItem(product)}>
            {isAvailable ? 'В корзину' : 'Нет в наличии'}
          </button>
        </div>
      </div>
    </article>
  );
}

export default ProductCard;

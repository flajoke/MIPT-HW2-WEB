import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { addCartItem, selectCartActionStatus } from '../store/cartSlice.js';
import { formatColorTemperature, formatPrice } from '../utils/formatters.js';
import ProductVisual from './ProductVisual.jsx';

function ProductCard({ product }) {
  const dispatch = useDispatch();
  const actionStatus = useSelector(selectCartActionStatus);
  const isAvailable = product.status === 'ACTIVE' && product.stockQty > 0;
  const isCartBusy = actionStatus === 'loading';

  return (
    <article className="product-card">
      <Link to={`/product/${product.slug}`} className="product-card__image" aria-label={product.name}>
        <ProductVisual product={product} />
      </Link>

      <div className="product-card__content">
        <div className="product-card__meta">
          <span>{product.category}</span>
          <span>{product.stockQty > 0 ? `Доступно: ${product.stockQty}` : 'Нет в наличии'}</span>
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
          </div>
          <button
            className="button button--primary"
            type="button"
            disabled={!isAvailable || isCartBusy}
            onClick={() => dispatch(addCartItem({ productId: product.id, qty: 1 }))}
          >
            {isAvailable ? 'В корзину' : 'Нет в наличии'}
          </button>
        </div>
      </div>
    </article>
  );
}

export default ProductCard;

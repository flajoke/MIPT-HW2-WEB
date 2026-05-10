import { useMemo, useState } from 'react';
import { useSelector } from 'react-redux';
import ProductCard from '../components/ProductCard.jsx';
import { getBackendUrls } from '../services/api.js';
import { selectProducts, selectProductsError, selectProductsStatus } from '../store/productsSlice.js';

function CatalogPage() {
  const products = useSelector(selectProducts);
  const status = useSelector(selectProductsStatus);
  const error = useSelector(selectProductsError);
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState('all');
  const [socketType, setSocketType] = useState('Все подключения');
  const [sortMode, setSortMode] = useState('popular');

  const categoryOptions = useMemo(() => {
    const map = new Map(products.map((product) => [product.categoryId, product.category]));
    return [{ id: 'all', label: 'Все товары' }, ...Array.from(map, ([id, label]) => ({ id, label }))];
  }, [products]);

  const socketFilters = useMemo(() => {
    const sockets = Array.from(new Set(products.map((product) => product.socketType).filter(Boolean))).sort();
    return ['Все подключения', ...sockets];
  }, [products]);

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return [...products]
      .filter((product) => {
        const matchesCategory = categoryId === 'all' || product.categoryId === categoryId;
        const matchesSocket = socketType === 'Все подключения' || product.socketType === socketType;
        const matchesQuery =
          normalizedQuery.length === 0 ||
          [product.name, product.description, product.sku, product.category]
            .join(' ')
            .toLowerCase()
            .includes(normalizedQuery);

        return matchesCategory && matchesSocket && matchesQuery;
      })
      .sort((left, right) => {
        if (sortMode === 'price-asc') return left.price - right.price;
        if (sortMode === 'price-desc') return right.price - left.price;
        if (sortMode === 'stock') return right.stockQty - left.stockQty;
        return Number(right.stockQty > 0) - Number(left.stockQty > 0) || left.name.localeCompare(right.name, 'ru');
      });
  }, [categoryId, products, query, socketType, sortMode]);

  const backendUrls = getBackendUrls();

  return (
    <div className="container page-stack">
      <section className="hero-card">
        <div className="hero-card__content">
          <span className="eyebrow">Интернет-магазин светотехники</span>
          <h1>LED-лампы, светильники и декоративная подсветка</h1>
          <p>
            Каталог загружается из catalog-service, а корзина и оформление заказа работают через order-service.
            HTTP-запросы выполняются через fetch и видны во вкладке Network.
          </p>
          <div className="hero-stats" aria-label="Преимущества магазина">
            <span>{products.length} товаров из backend</span>
            <span>{categoryOptions.length - 1} категории</span>
            <span>Redux store</span>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-bulb">✦</div>
        </div>
      </section>

      <div className="api-note">
        <strong>Backend:</strong> catalog — {backendUrls.catalog}; orders — {backendUrls.orders}
      </div>

      <section className="catalog-layout">
        <aside className="filters-card" aria-label="Фильтры каталога">
          <h2>Фильтры</h2>
          <label>
            Поиск
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Название, SKU или описание" />
          </label>

          <label>
            Категория
            <select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}>
              {categoryOptions.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.label}
                </option>
              ))}
            </select>
          </label>

          <label>
            Тип подключения
            <select value={socketType} onChange={(event) => setSocketType(event.target.value)}>
              {socketFilters.map((socket) => (
                <option key={socket} value={socket}>
                  {socket}
                </option>
              ))}
            </select>
          </label>

          <label>
            Сортировка
            <select value={sortMode} onChange={(event) => setSortMode(event.target.value)}>
              <option value="popular">Сначала доступные</option>
              <option value="price-asc">Сначала дешевле</option>
              <option value="price-desc">Сначала дороже</option>
              <option value="stock">Сначала больше на складе</option>
            </select>
          </label>
        </aside>

        <div className="catalog-content">
          <div className="section-heading">
            <div>
              <span className="eyebrow">Каталог</span>
              <h2>Найдено товаров: {filteredProducts.length}</h2>
            </div>
            <p>Карточки товаров ведут на отдельную страницу с подробным описанием.</p>
          </div>

          {status === 'loading' && <div className="info-banner">Загружаем товары из catalog-service...</div>}
          {error && <div className="error-banner">Ошибка загрузки товаров: {error}</div>}

          {status !== 'loading' && filteredProducts.length > 0 ? (
            <div className="product-grid">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : null}

          {status !== 'loading' && !error && filteredProducts.length === 0 ? (
            <div className="empty-inline">
              <h3>Ничего не найдено</h3>
              <p>Измените поисковый запрос или сбросьте фильтры.</p>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}

export default CatalogPage;

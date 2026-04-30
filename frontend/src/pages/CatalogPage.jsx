import { useMemo, useState } from 'react';
import ProductCard from '../components/ProductCard.jsx';
import { categories, products } from '../data/products.js';

const socketFilters = ['Все цоколи', 'E27', 'E14', 'USB', 'Встроенный драйвер'];

function CatalogPage() {
  const [query, setQuery] = useState('');
  const [categoryId, setCategoryId] = useState('all');
  const [socketType, setSocketType] = useState('Все цоколи');
  const [sortMode, setSortMode] = useState('popular');

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return products
      .filter((product) => {
        const matchesCategory = categoryId === 'all' || product.categoryId === categoryId;
        const matchesSocket = socketType === 'Все цоколи' || product.socketType === socketType;
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
        return Number(right.oldPrice || 0) - Number(left.oldPrice || 0);
      });
  }, [categoryId, query, socketType, sortMode]);

  return (
    <div className="container page-stack">
      <section className="hero-card">
        <div className="hero-card__content">
          <span className="eyebrow">Интернет-магазин светотехники</span>
          <h1>LED-лампы, светильники и декоративная подсветка</h1>
          <p>
            Подберите свет для дома или рабочего пространства. Все данные на витрине — mock-данные, поэтому
            подключение backend для этого этапа не требуется.
          </p>
          <div className="hero-stats" aria-label="Преимущества магазина">
            <span>8 товаров</span>
            <span>3 категории</span>
            <span>Готовая корзина</span>
          </div>
        </div>
        <div className="hero-visual" aria-hidden="true">
          <div className="hero-bulb">✦</div>
        </div>
      </section>

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
              {categories.map((category) => (
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
              <option value="popular">Сначала популярные</option>
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

          {filteredProducts.length > 0 ? (
            <div className="product-grid">
              {filteredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          ) : (
            <div className="empty-inline">
              <h3>Ничего не найдено</h3>
              <p>Измените поисковый запрос или сбросьте фильтры.</p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default CatalogPage;

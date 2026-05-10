import { useSelector } from 'react-redux';
import { NavLink } from 'react-router-dom';
import { selectCartCount } from '../store/cartSlice.js';

function Header() {
  const cartCount = useSelector(selectCartCount);

  return (
    <header className="site-header">
      <div className="container header-content">
        <NavLink className="brand" to="/catalog" aria-label="Перейти в каталог LVD Store">
          <span className="brand-mark">LVD</span>
          <span className="brand-text">Light & Voltage Depot</span>
        </NavLink>

        <nav className="main-nav" aria-label="Основная навигация">
          <NavLink to="/catalog">Каталог</NavLink>
          <NavLink to="/cart" className="cart-link">
            Корзина
            {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
          </NavLink>
        </nav>
      </div>
    </header>
  );
}

export default Header;

import { Link } from 'react-router-dom';

function EmptyState({ title, text, actionText = 'Перейти в каталог', to = '/catalog' }) {
  return (
    <section className="empty-state">
      <div className="empty-state__icon">⊘</div>
      <h1>{title}</h1>
      <p>{text}</p>
      <Link className="button button--primary" to={to}>
        {actionText}
      </Link>
    </section>
  );
}

export default EmptyState;

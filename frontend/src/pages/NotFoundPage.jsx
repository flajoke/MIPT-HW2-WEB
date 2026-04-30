import EmptyState from '../components/EmptyState.jsx';

function NotFoundPage() {
  return (
    <EmptyState
      title="Страница не найдена"
      text="Такого маршрута нет в пользовательской части магазина. Вернитесь в каталог."
      actionText="Открыть каталог"
    />
  );
}

export default NotFoundPage;

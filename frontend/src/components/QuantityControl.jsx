function QuantityControl({ value, min = 1, max = 99, onChange, ariaLabel = 'Количество товара' }) {
  const setValue = (nextValue) => {
    const normalized = Math.max(min, Math.min(max, Number(nextValue) || min));
    onChange(normalized);
  };

  return (
    <div className="quantity-control" aria-label={ariaLabel}>
      <button type="button" onClick={() => setValue(value - 1)} disabled={value <= min} aria-label="Уменьшить количество">
        −
      </button>
      <input value={value} min={min} max={max} onChange={(event) => setValue(event.target.value)} inputMode="numeric" />
      <button type="button" onClick={() => setValue(value + 1)} disabled={value >= max} aria-label="Увеличить количество">
        +
      </button>
    </div>
  );
}

export default QuantityControl;

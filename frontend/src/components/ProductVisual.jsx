function ProductVisual({ product, size = 'card' }) {
  const theme = product?.imageTheme || 'warm';

  return (
    <div className={`product-visual product-visual--${size}`} data-theme={theme} aria-hidden="true">
      <div className="glow-ring" />
      <div className="bulb-shape">
        <span>✦</span>
      </div>
    </div>
  );
}

export default ProductVisual;

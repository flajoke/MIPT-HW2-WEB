function ProductVisual({ product, size = 'card' }) {
  return (
    <div className={`product-visual product-visual--${size}`} data-theme={product.imageTheme} aria-hidden="true">
      <div className="glow-ring" />
      <div className="bulb-shape">
        <span>✦</span>
      </div>
    </div>
  );
}

export default ProductVisual;

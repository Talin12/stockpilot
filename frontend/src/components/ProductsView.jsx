import { formatMoney, formatNumber } from '../format.js';
import StatusBadge from './StatusBadge.jsx';

const STATUS_TABS = [
  { id: '', label: 'All' },
  { id: 'IN_STOCK', label: 'In stock' },
  { id: 'LOW_STOCK', label: 'Low stock' },
  { id: 'OUT_OF_STOCK', label: 'Out of stock' },
];

function StockMeter({ quantity, reorder }) {
  // Full bar = 3× the reorder level, so "healthy" stock sits comfortably past the marker.
  const scale = Math.max(reorder * 3, quantity, 1);
  const tone = quantity <= 0 ? 'danger' : quantity <= reorder ? 'warning' : 'ok';
  return (
    <div className="meter" title={`${quantity} on hand · reorder at ${reorder}`}>
      <div className="meter-numbers">
        <strong>{formatNumber(quantity)}</strong>
        <span className="muted small">/ {reorder} min</span>
      </div>
      <div className="meter-track">
        <div className={`meter-fill ${tone}`} style={{ width: `${(quantity / scale) * 100}%` }} />
        <div className="meter-marker" style={{ left: `${(reorder / scale) * 100}%` }} />
      </div>
    </div>
  );
}

function RowActions({ product, actions }) {
  // Close the overflow <details> menu once an item is chosen.
  const pick = (action) => (e) => {
    e.currentTarget.closest('details')?.removeAttribute('open');
    action(product);
  };
  return (
    <div className="row-actions">
      <button className="button small" onClick={() => actions.onReceive(product)}>
        Receive
      </button>
      <button
        className="button small"
        onClick={() => actions.onShip(product)}
        disabled={product.quantity === 0}
      >
        Ship
      </button>
      <details className="menu">
        <summary className="button small ghost" aria-label={`More actions for ${product.name}`}>
          ⋯
        </summary>
        <div className="menu-popover">
          <button onClick={pick(actions.onAdjust)}>Adjust count</button>
          <button onClick={pick(actions.onEdit)}>Edit details</button>
          <button className="danger" onClick={pick(actions.onDelete)}>
            Delete
          </button>
        </div>
      </details>
    </div>
  );
}

export default function ProductsView({
  products,
  categories,
  stats,
  filters,
  onFiltersChange,
  loading,
  actions,
}) {
  const update = (patch) => onFiltersChange({ ...filters, ...patch });
  const tabCount = {
    '': stats?.total_products,
    LOW_STOCK: stats?.low_stock,
    OUT_OF_STOCK: stats?.out_of_stock,
    IN_STOCK: stats ? stats.total_products - stats.low_stock - stats.out_of_stock : undefined,
  };

  return (
    <section className="content">
      <div className="panel">
        <div className="toolbar">
          <div className="tabs" role="tablist">
            {STATUS_TABS.map((tab) => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={filters.stock_status === tab.id}
                className={`tab ${filters.stock_status === tab.id ? 'active' : ''}`}
                onClick={() => update({ stock_status: tab.id })}
              >
                {tab.label}
                {tabCount[tab.id] !== undefined && <span className="tab-count">{tabCount[tab.id]}</span>}
              </button>
            ))}
          </div>
          <div className="toolbar-inputs">
            <input
              type="search"
              placeholder="Search name, SKU or supplier…"
              value={filters.search}
              onChange={(e) => update({ search: e.target.value })}
              aria-label="Search products"
            />
            <select
              value={filters.category}
              onChange={(e) => update({ category: e.target.value })}
              aria-label="Filter by category"
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="skeleton-stack padded">
            {Array.from({ length: 6 }, (_, i) => (
              <div key={i} className="skeleton tall" />
            ))}
          </div>
        ) : products.length === 0 ? (
          <div className="empty large">
            <strong>No products match these filters.</strong>
            <span>Try clearing the search, or add a new product.</span>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table products-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Category</th>
                  <th>Location</th>
                  <th>Stock</th>
                  <th className="num">Unit price</th>
                  <th className="num">Value</th>
                  <th>Status</th>
                  <th aria-label="Actions" />
                </tr>
              </thead>
              <tbody>
                {products.map((p) => (
                  <tr key={p.id}>
                    <td data-label="Product">
                      <div className="product-cell">
                        <strong>{p.name}</strong>
                        <span className="muted small">
                          <code>{p.sku}</code> · {p.supplier || 'No supplier'}
                        </span>
                      </div>
                    </td>
                    <td data-label="Category">{p.category}</td>
                    <td data-label="Location">{p.location || '—'}</td>
                    <td data-label="Stock">
                      <StockMeter quantity={p.quantity} reorder={p.reorder_level} />
                    </td>
                    <td data-label="Unit price" className="num">
                      {formatMoney(p.unit_price)}
                    </td>
                    <td data-label="Value" className="num">
                      {formatMoney(p.unit_price * p.quantity)}
                    </td>
                    <td data-label="Status">
                      <StatusBadge status={p.stock_status} />
                    </td>
                    <td className="actions-cell">
                      <RowActions product={p} actions={actions} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

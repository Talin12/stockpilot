import { formatMoney, formatMoneyCompact, formatNumber } from '../format.js';
import ActivityFeed from './ActivityFeed.jsx';
import StatusBadge from './StatusBadge.jsx';

function Kpi({ label, value, hint, tone, onClick }) {
  const Tag = onClick ? 'button' : 'div';
  return (
    <Tag className={`kpi ${tone ?? ''} ${onClick ? 'clickable' : ''}`} onClick={onClick}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </Tag>
  );
}

function Skeleton({ rows = 3 }) {
  return (
    <div className="skeleton-stack">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton" />
      ))}
    </div>
  );
}

export default function Dashboard({ stats, movements, products, loading, onViewProducts, actions }) {
  if (loading) {
    return (
      <section className="content">
        <div className="kpi-grid">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="kpi">
              <Skeleton rows={2} />
            </div>
          ))}
        </div>
      </section>
    );
  }
  if (!stats) return null;

  const alerts = products
    .filter((p) => p.stock_status !== 'IN_STOCK')
    .sort((a, b) => a.quantity - a.reorder_level - (b.quantity - b.reorder_level))
    .slice(0, 6);
  const maxValue = Math.max(1, ...stats.categories.map((c) => c.value));

  return (
    <section className="content">
      <div className="kpi-grid">
        <Kpi label="Products" value={formatNumber(stats.total_products)} hint="Active SKUs" />
        <Kpi label="Units on hand" value={formatNumber(stats.total_units)} hint="Across all locations" />
        <Kpi
          label="Inventory value"
          value={formatMoneyCompact(stats.inventory_value)}
          hint={formatMoney(stats.inventory_value)}
          tone="accent"
        />
        <Kpi
          label="Low stock"
          value={formatNumber(stats.low_stock)}
          hint="At or below reorder level"
          tone={stats.low_stock ? 'warning' : ''}
          onClick={() => onViewProducts('LOW_STOCK')}
        />
        <Kpi
          label="Out of stock"
          value={formatNumber(stats.out_of_stock)}
          hint="Cannot fulfil orders"
          tone={stats.out_of_stock ? 'danger' : ''}
          onClick={() => onViewProducts('OUT_OF_STOCK')}
        />
      </div>

      <div className="dashboard-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>Reorder alerts</h2>
            <button className="link-button" onClick={() => onViewProducts(null)}>
              View all products →
            </button>
          </div>
          {alerts.length === 0 ? (
            <div className="empty">
              <strong>All stock above reorder levels.</strong>
              <span>Nothing needs replenishing right now.</span>
            </div>
          ) : (
            <ul className="alert-list">
              {alerts.map((p) => (
                <li key={p.id}>
                  <div className="alert-main">
                    <div className="alert-name">{p.name}</div>
                    <div className="muted small">
                      {p.sku} · {p.supplier || 'No supplier'} · reorder at {p.reorder_level}
                    </div>
                  </div>
                  <div className="alert-qty">
                    <strong>{p.quantity}</strong>
                    <StatusBadge status={p.stock_status} />
                  </div>
                  <button className="button small" onClick={() => actions.onReceive(p)}>
                    Receive
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Value by category</h2>
          </div>
          {stats.categories.length === 0 ? (
            <div className="empty">
              <strong>No products yet.</strong>
              <span>Add your first product to see category totals.</span>
            </div>
          ) : (
            <ul className="bar-list">
              {stats.categories.map((c) => (
                <li key={c.category}>
                  <div className="bar-label">
                    <span>{c.category}</span>
                    <span className="muted">{formatMoneyCompact(c.value)}</span>
                  </div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${(c.value / maxValue) * 100}%` }} />
                  </div>
                  <div className="muted small">
                    {c.products} products · {formatNumber(c.units)} units
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="panel span-2">
          <div className="panel-header">
            <h2>Recent activity</h2>
          </div>
          <ActivityFeed movements={movements.slice(0, 8)} />
        </div>
      </div>
    </section>
  );
}

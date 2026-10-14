import { MOVEMENT_LABELS, timeAgo } from '../format.js';

export default function ActivityFeed({ movements }) {
  if (movements.length === 0) {
    return (
      <div className="empty">
        <strong>No stock movements yet.</strong>
        <span>Receipts, shipments and adjustments will appear here.</span>
      </div>
    );
  }
  return (
    <ul className="activity">
      {movements.map((m) => (
        <li key={m.id}>
          <span className={`activity-icon ${m.movement_type.toLowerCase()}`} aria-hidden>
            {m.quantity_change > 0 ? '↓' : '↑'}
          </span>
          <div className="activity-body">
            <div>
              <strong>{MOVEMENT_LABELS[m.movement_type]}</strong>{' '}
              <span className={m.quantity_change > 0 ? 'positive' : 'negative'}>
                {m.quantity_change > 0 ? '+' : ''}
                {m.quantity_change}
              </span>{' '}
              × {m.product_name}
            </div>
            <div className="muted small">
              {m.product_sku} · balance {m.balance_after}
              {m.note ? ` · ${m.note}` : ''}
            </div>
          </div>
          <time className="muted small" dateTime={m.created_at}>
            {timeAgo(m.created_at)}
          </time>
        </li>
      ))}
    </ul>
  );
}

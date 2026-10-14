import { MOVEMENT_LABELS } from '../format.js';

const dateTime = new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' });

export default function MovementsView({ movements, loading }) {
  return (
    <section className="content">
      <div className="panel">
        {loading ? (
          <div className="skeleton-stack padded">
            {Array.from({ length: 8 }, (_, i) => (
              <div key={i} className="skeleton" />
            ))}
          </div>
        ) : movements.length === 0 ? (
          <div className="empty large">
            <strong>The ledger is empty.</strong>
            <span>Receive or ship stock from the Products page to start the audit trail.</span>
          </div>
        ) : (
          <div className="table-wrap">
            <table className="table ledger-table">
              <thead>
                <tr>
                  <th>When</th>
                  <th>Product</th>
                  <th>Type</th>
                  <th className="num">Change</th>
                  <th className="num">Balance</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {movements.map((m) => (
                  <tr key={m.id}>
                    <td data-label="When" className="nowrap">
                      {dateTime.format(new Date(m.created_at.endsWith('Z') || m.created_at.includes('+') ? m.created_at : `${m.created_at}Z`))}
                    </td>
                    <td data-label="Product">
                      <div className="product-cell">
                        <strong>{m.product_name}</strong>
                        <code className="muted small">{m.product_sku}</code>
                      </div>
                    </td>
                    <td data-label="Type">
                      <span className={`badge movement ${m.movement_type.toLowerCase()}`}>
                        {MOVEMENT_LABELS[m.movement_type]}
                      </span>
                    </td>
                    <td data-label="Change" className={`num ${m.quantity_change > 0 ? 'positive' : 'negative'}`}>
                      {m.quantity_change > 0 ? '+' : ''}
                      {m.quantity_change}
                    </td>
                    <td data-label="Balance" className="num">
                      {m.balance_after}
                    </td>
                    <td data-label="Note" className="muted">
                      {m.note || '—'}
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

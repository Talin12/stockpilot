import { useState } from 'react';
import Modal from './Modal.jsx';

const TYPES = [
  { id: 'RECEIVED', label: 'Receive', hint: 'Goods arriving from a supplier' },
  { id: 'SHIPPED', label: 'Ship', hint: 'Goods leaving for a customer' },
  { id: 'ADJUSTED', label: 'Adjust', hint: 'Cycle-count correction (use a negative number for losses)' },
];

export default function MovementModal({ product, initialType, onClose, onSave }) {
  const [type, setType] = useState(initialType);
  const [quantity, setQuantity] = useState(type === 'ADJUSTED' ? -1 : 1);
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const qty = Number(quantity) || 0;
  const change = type === 'SHIPPED' ? -Math.abs(qty) : type === 'RECEIVED' ? Math.abs(qty) : qty;
  const after = product.quantity + change;
  const invalid = qty === 0 || after < 0 || (type !== 'ADJUSTED' && qty < 0);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave(product, { movement_type: type, quantity: qty, note: note.trim() });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <Modal
      title={product.name}
      subtitle={`${product.sku} · ${product.quantity} on hand · reorder at ${product.reorder_level}`}
      onClose={onClose}
      size="small"
      footer={
        <>
          <button type="button" className="button ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" form="movement-form" className="button primary" disabled={saving || invalid}>
            {saving ? 'Recording…' : 'Record movement'}
          </button>
        </>
      }
    >
      <form id="movement-form" className="form-grid single" onSubmit={submit}>
        {error && (
          <div className="banner error" role="alert">
            {error}
          </div>
        )}
        <div className="segmented" role="radiogroup" aria-label="Movement type">
          {TYPES.map((t) => (
            <button
              type="button"
              key={t.id}
              role="radio"
              aria-checked={type === t.id}
              className={type === t.id ? 'active' : ''}
              onClick={() => setType(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <p className="muted small">{TYPES.find((t) => t.id === type).hint}</p>
        <label>
          Quantity
          <input
            type="number"
            step="1"
            min={type === 'ADJUSTED' ? undefined : 1}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            autoFocus
          />
        </label>
        <label>
          Reference / note
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder={type === 'SHIPPED' ? 'SO-10452' : type === 'RECEIVED' ? 'PO-7781' : 'Cycle count'}
            maxLength={255}
          />
        </label>
        <div className={`balance-preview ${after < 0 ? 'bad' : ''}`}>
          <span>{product.quantity}</span>
          <span className={change >= 0 ? 'positive' : 'negative'}>
            {change >= 0 ? '+' : '−'} {Math.abs(change)}
          </span>
          <span>=</span>
          <strong>{after}</strong>
          <span className="muted small">{after < 0 ? 'not enough stock' : 'after this movement'}</span>
        </div>
      </form>
    </Modal>
  );
}

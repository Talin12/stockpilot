import { useState } from 'react';
import Modal from './Modal.jsx';

const EMPTY = {
  sku: '',
  name: '',
  category: '',
  description: '',
  quantity: 0,
  reorder_level: 10,
  unit_price: 0,
  supplier: '',
  location: '',
};

export default function ProductModal({ product, categories, onClose, onSave }) {
  const editing = Boolean(product);
  const [form, setForm] = useState(() => ({ ...EMPTY, ...product }));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    const payload = {
      sku: form.sku.trim(),
      name: form.name.trim(),
      category: form.category.trim(),
      description: form.description.trim(),
      reorder_level: Number(form.reorder_level),
      unit_price: Number(form.unit_price),
      supplier: form.supplier.trim(),
      location: form.location.trim(),
    };
    if (!editing) payload.quantity = Number(form.quantity);
    try {
      await onSave(payload, product);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <Modal
      title={editing ? `Edit ${product.name}` : 'New product'}
      subtitle={editing ? 'Stock quantity changes go through Receive / Ship / Adjust.' : 'Add an item to the catalogue.'}
      onClose={onClose}
      footer={
        <>
          <button type="button" className="button ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" form="product-form" className="button primary" disabled={saving}>
            {saving ? 'Saving…' : editing ? 'Save changes' : 'Create product'}
          </button>
        </>
      }
    >
      <form id="product-form" className="form-grid" onSubmit={submit}>
        {error && (
          <div className="banner error span-2" role="alert">
            {error}
          </div>
        )}
        <label>
          SKU
          <input required value={form.sku} onChange={set('sku')} placeholder="ELEC-1004" maxLength={40} />
        </label>
        <label>
          Category
          <input
            required
            list="category-options"
            value={form.category}
            onChange={set('category')}
            placeholder="Electronics"
            maxLength={80}
          />
          <datalist id="category-options">
            {categories.map((c) => (
              <option key={c} value={c} />
            ))}
          </datalist>
        </label>
        <label className="span-2">
          Product name
          <input required value={form.name} onChange={set('name')} placeholder="Wireless barcode scanner" maxLength={200} />
        </label>
        {!editing && (
          <label>
            Opening quantity
            <input type="number" min="0" step="1" value={form.quantity} onChange={set('quantity')} />
          </label>
        )}
        <label>
          Reorder level
          <input type="number" min="0" step="1" value={form.reorder_level} onChange={set('reorder_level')} />
        </label>
        <label>
          Unit price (₹)
          <input type="number" min="0" step="0.01" value={form.unit_price} onChange={set('unit_price')} />
        </label>
        <label>
          Bin location
          <input value={form.location} onChange={set('location')} placeholder="A1-03" maxLength={80} />
        </label>
        <label className={editing ? '' : 'span-2'}>
          Supplier
          <input value={form.supplier} onChange={set('supplier')} placeholder="ScanTech India" maxLength={120} />
        </label>
        <label className="span-2">
          Description
          <textarea rows={3} value={form.description} onChange={set('description')} maxLength={2000} />
        </label>
      </form>
    </Modal>
  );
}

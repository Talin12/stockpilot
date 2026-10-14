import { useState } from 'react';
import Modal from './Modal.jsx';

export default function ConfirmModal({ title, message, confirmLabel, onCancel, onConfirm }) {
  const [busy, setBusy] = useState(false);
  return (
    <Modal
      title={title}
      onClose={onCancel}
      size="small"
      footer={
        <>
          <button className="button ghost" onClick={onCancel}>
            Cancel
          </button>
          <button
            className="button danger"
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              await onConfirm();
            }}
          >
            {busy ? 'Working…' : confirmLabel}
          </button>
        </>
      }
    >
      <p>{message}</p>
    </Modal>
  );
}

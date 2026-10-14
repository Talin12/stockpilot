import { STATUS_LABELS } from '../format.js';

export default function StatusBadge({ status }) {
  return <span className={`badge ${status.toLowerCase().replaceAll('_', '-')}`}>{STATUS_LABELS[status]}</span>;
}

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
});
const compactCurrency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  notation: 'compact',
  maximumFractionDigits: 1,
});
const number = new Intl.NumberFormat('en-IN');

export const formatMoney = (value) => currency.format(value ?? 0);
export const formatMoneyCompact = (value) => compactCurrency.format(value ?? 0);
export const formatNumber = (value) => number.format(value ?? 0);

export function timeAgo(iso) {
  const then = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : `${iso}Z`);
  const seconds = Math.max(0, Math.round((Date.now() - then.getTime()) / 1000));
  if (seconds < 60) return 'just now';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return then.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export const STATUS_LABELS = {
  IN_STOCK: 'In stock',
  LOW_STOCK: 'Low stock',
  OUT_OF_STOCK: 'Out of stock',
};

export const MOVEMENT_LABELS = {
  RECEIVED: 'Received',
  SHIPPED: 'Shipped',
  ADJUSTED: 'Adjusted',
};

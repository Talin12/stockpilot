// All calls are relative: Nginx (Docker) or the Ingress (Kubernetes) routes /api to FastAPI.
async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (response.status === 204) return null;

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(describeError(body) || `Request failed (${response.status})`);
  }
  return body;
}

function describeError(body) {
  if (!body?.detail) return null;
  if (typeof body.detail === 'string') return body.detail;
  // FastAPI validation errors: [{loc: [...], msg: '...'}]
  return body.detail
    .map((err) => `${err.loc?.slice(-1)[0] ?? 'field'}: ${err.msg.replace(/^Value error, /, '')}`)
    .join('; ');
}

function query(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, value);
  });
  const text = search.toString();
  return text ? `?${text}` : '';
}

export const api = {
  info: () => request('/api/info'),
  stats: () => request('/api/stats'),
  categories: () => request('/api/categories'),
  products: (filters = {}) => request(`/api/products${query(filters)}`),
  createProduct: (data) => request('/api/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) =>
    request(`/api/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/api/products/${id}`, { method: 'DELETE' }),
  movements: (limit = 20) => request(`/api/movements?limit=${limit}`),
  recordMovement: (id, data) =>
    request(`/api/products/${id}/movements`, { method: 'POST', body: JSON.stringify(data) }),
};

import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import Sidebar from './components/Sidebar.jsx';
import Dashboard from './components/Dashboard.jsx';
import ProductsView from './components/ProductsView.jsx';
import MovementsView from './components/MovementsView.jsx';
import ProductModal from './components/ProductModal.jsx';
import MovementModal from './components/MovementModal.jsx';
import ConfirmModal from './components/ConfirmModal.jsx';
import Toasts from './components/Toasts.jsx';

const TITLES = {
  dashboard: ['Dashboard', 'Live overview of stock health and warehouse activity'],
  products: ['Products', 'Catalogue, stock levels and reorder points'],
  movements: ['Stock ledger', 'Every receipt, shipment and adjustment, newest first'],
};

const REFRESH_MS = 30_000;

// Hash routing (#/products) keeps views deep-linkable without a router dependency.
const viewFromHash = () => {
  const name = window.location.hash.replace(/^#\/?/, '');
  return name in TITLES ? name : 'dashboard';
};

export default function App() {
  const [view, setViewState] = useState(viewFromHash);
  const setView = useCallback((next) => {
    window.location.hash = next === 'dashboard' ? '' : `/${next}`;
    setViewState(next);
  }, []);

  useEffect(() => {
    const onHash = () => setViewState(viewFromHash());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [info, setInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]); // filtered list for the Products page
  const [allProducts, setAllProducts] = useState([]); // unfiltered, feeds dashboard alerts
  const [categories, setCategories] = useState([]);
  const [movements, setMovements] = useState([]);
  const [filters, setFilters] = useState({ search: '', category: '', stock_status: '' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [productModal, setProductModal] = useState(null); // {product?}
  const [movementModal, setMovementModal] = useState(null); // {product, type}
  const [confirmDelete, setConfirmDelete] = useState(null); // product
  const [toasts, setToasts] = useState([]);
  const toastId = useRef(0);
  const filtersRef = useRef(filters);
  filtersRef.current = filters;

  const notify = useCallback((message, tone = 'success') => {
    // (crypto.randomUUID is unavailable on plain-HTTP origins such as an Ingress host)
    const id = ++toastId.current;
    setToasts((current) => [...current, { id, message, tone }]);
    setTimeout(() => setToasts((current) => current.filter((t) => t.id !== id)), 4000);
  }, []);

  const loadOverview = useCallback(async () => {
    const [statsData, movementData, categoryData, infoData, everything] = await Promise.all([
      api.stats(),
      api.movements(view === 'movements' ? 200 : 20),
      api.categories(),
      api.info(),
      api.products(),
    ]);
    setStats(statsData);
    setAllProducts(everything);
    setMovements(movementData);
    setCategories(categoryData);
    setInfo(infoData);
  }, [view]);

  const loadProducts = useCallback(async () => {
    setProducts(await api.products(filtersRef.current));
  }, []);

  const refresh = useCallback(
    async ({ quiet = false } = {}) => {
      if (!quiet) setLoading(true);
      try {
        await Promise.all([loadOverview(), loadProducts()]);
        setError(null);
      } catch (err) {
        setError(err.message || 'Unable to reach the StockPilot API');
      } finally {
        setLoading(false);
      }
    },
    [loadOverview, loadProducts],
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const timer = setInterval(() => refresh({ quiet: true }), REFRESH_MS);
    return () => clearInterval(timer);
  }, [refresh]);

  // Debounce search/filter changes so typing doesn't fire a request per keystroke.
  const firstFilterRun = useRef(true);
  useEffect(() => {
    if (firstFilterRun.current) {
      firstFilterRun.current = false;
      return undefined;
    }
    const timer = setTimeout(() => {
      loadProducts().catch((err) => setError(err.message));
    }, 250);
    return () => clearTimeout(timer);
  }, [filters, loadProducts]);

  async function saveProduct(data, existing) {
    if (existing) {
      await api.updateProduct(existing.id, data);
      notify(`Updated ${data.name}`);
    } else {
      await api.createProduct(data);
      notify(`Added ${data.name} to the catalogue`);
    }
    setProductModal(null);
    refresh({ quiet: true });
  }

  async function saveMovement(product, data) {
    const movement = await api.recordMovement(product.id, data);
    const verb = { RECEIVED: 'Received', SHIPPED: 'Shipped', ADJUSTED: 'Adjusted' }[data.movement_type];
    notify(`${verb} ${Math.abs(movement.quantity_change)} × ${product.name} — ${movement.balance_after} on hand`);
    setMovementModal(null);
    refresh({ quiet: true });
  }

  async function deleteProduct(product) {
    try {
      await api.deleteProduct(product.id);
      notify(`Deleted ${product.name}`);
      refresh({ quiet: true });
    } catch (err) {
      notify(err.message, 'error');
    } finally {
      setConfirmDelete(null);
    }
  }

  const actions = {
    onReceive: (product) => setMovementModal({ product, type: 'RECEIVED' }),
    onShip: (product) => setMovementModal({ product, type: 'SHIPPED' }),
    onAdjust: (product) => setMovementModal({ product, type: 'ADJUSTED' }),
    onEdit: (product) => setProductModal({ product }),
    onDelete: (product) => setConfirmDelete(product),
  };

  const [title, subtitle] = TITLES[view];

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        onNavigate={(next) => {
          setView(next);
          setSidebarOpen(false);
        }}
        stats={stats}
        info={info}
        healthy={!error && !!info}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="main">
        <header className="topbar">
          <button
            className="icon-button menu-button"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
          >
            <span />
            <span />
            <span />
          </button>
          <div className="topbar-titles">
            <h1>{title}</h1>
            <p>{subtitle}</p>
          </div>
          <div className="topbar-actions">
            <button className="button ghost" onClick={() => refresh()} disabled={loading}>
              {loading ? 'Refreshing…' : 'Refresh'}
            </button>
            <button className="button primary" onClick={() => setProductModal({})}>
              + New product
            </button>
          </div>
        </header>

        {error && (
          <div className="banner error" role="alert">
            <div>
              <strong>Backend unreachable.</strong> {error}. Check that the API pods are Ready
              (<code>kubectl get pods</code>) or that <code>docker compose</code> is running.
            </div>
            <button className="button small" onClick={() => refresh()}>
              Retry
            </button>
          </div>
        )}

        {view === 'dashboard' && (
          <Dashboard
            stats={stats}
            movements={movements}
            products={allProducts}
            loading={loading && !stats}
            onViewProducts={(status) => {
              setFilters((f) => ({ ...f, stock_status: status ?? '' }));
              setView('products');
            }}
            actions={actions}
          />
        )}
        {view === 'products' && (
          <ProductsView
            products={products}
            categories={categories}
            stats={stats}
            filters={filters}
            onFiltersChange={setFilters}
            loading={loading && products.length === 0}
            actions={actions}
          />
        )}
        {view === 'movements' && <MovementsView movements={movements} loading={loading && !stats} />}
      </main>

      {productModal && (
        <ProductModal
          product={productModal.product}
          categories={categories}
          onClose={() => setProductModal(null)}
          onSave={saveProduct}
        />
      )}
      {movementModal && (
        <MovementModal
          product={movementModal.product}
          initialType={movementModal.type}
          onClose={() => setMovementModal(null)}
          onSave={saveMovement}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title="Delete product?"
          message={`${confirmDelete.name} (${confirmDelete.sku}) and its full stock history will be removed. This cannot be undone.`}
          confirmLabel="Delete product"
          onCancel={() => setConfirmDelete(null)}
          onConfirm={() => deleteProduct(confirmDelete)}
        />
      )}
      <Toasts toasts={toasts} />
    </div>
  );
}

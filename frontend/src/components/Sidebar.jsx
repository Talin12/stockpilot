const NAV = [
  { id: 'dashboard', label: 'Dashboard', icon: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z' },
  { id: 'products', label: 'Products', icon: 'M20 7l-8-4-8 4m16 0v10l-8 4m8-14l-8 4m0 10L4 17V7m8 14V11M4 7l8 4' },
  { id: 'movements', label: 'Stock ledger', icon: 'M4 6h16M4 12h16M4 18h10' },
];

export default function Sidebar({ view, onNavigate, stats, info, healthy, open, onClose }) {
  const counts = {
    products: stats?.total_products,
    movements: null,
    dashboard: stats ? stats.low_stock + stats.out_of_stock || null : null,
  };

  return (
    <>
      <div className={`sidebar-backdrop ${open ? 'visible' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark" aria-hidden>
            <svg viewBox="0 0 32 32">
              <path d="M8 12l8-4 8 4-8 4-8-4z" fill="currentColor" />
              <path
                d="M8 16l8 4 8-4M8 20l8 4 8-4"
                fill="none"
                stroke="currentColor"
                strokeOpacity=".6"
                strokeWidth="2"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          <div>
            <div className="brand-name">StockPilot</div>
            <div className="brand-sub">Central Warehouse · Mumbai</div>
          </div>
        </div>

        <nav className="nav" aria-label="Main">
          <div className="nav-label">Workspace</div>
          {NAV.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              aria-current={view === item.id ? 'page' : undefined}
            >
              <svg viewBox="0 0 24 24" aria-hidden>
                <path d={item.icon} />
              </svg>
              <span>{item.label}</span>
              {counts[item.id] ? (
                <span className={`nav-count ${item.id === 'dashboard' ? 'alert' : ''}`}>
                  {counts[item.id]}
                </span>
              ) : null}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="pipeline-card">
            <div className="pipeline-title">Delivery pipeline</div>
            <ol className="pipeline-steps">
              {['Test', 'Build', 'Scan', 'Push', 'Deploy'].map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
          <div className="env-row">
            <span className={`status-dot ${healthy ? 'ok' : 'down'}`} />
            <span>{healthy ? 'API healthy' : 'API offline'}</span>
          </div>
          {info && (
            <div className="build-meta" title="Image tag = Git commit SHA">
              <span className="env-pill">{info.environment}</span>
              <span>v{info.version}</span>
              <code>{info.git_sha.slice(0, 7)}</code>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

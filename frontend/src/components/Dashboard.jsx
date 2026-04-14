import { useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";

const MXN = (n) => new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN", maximumFractionDigits: 0 }).format(n);
const PCT = (n) => `${n.toFixed(1)}%`;

const PALETTE = ["#6366f1","#10b981","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#ec4899","#84cc16","#f97316","#14b8a6"];
const ORIGIN_COLORS = { MX: "#10b981", CN: "#ef4444", US: "#6366f1", HK: "#f59e0b" };

function originColor(o) { return ORIGIN_COLORS[o] || "#94a3b8"; }

// ── Sub-components ────────────────────────────────────────────────────────────

function Stat({ label, value, sub, color }) {
  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <p className="stat-value" style={color ? { color } : {}}>{value}</p>
      {sub && <p className="stat-sub">{sub}</p>}
    </div>
  );
}

function SectionHeader({ letter, title }) {
  return (
    <div className="section-header">
      <span className="section-badge">{letter}</span>
      <h2 className="section-title">{title}</h2>
    </div>
  );
}

function HhiBadge({ hhi }) {
  if (hhi < 1500) return <span className="badge badge--green">Fragmentado / Competitivo (HHI {hhi.toFixed(0)})</span>;
  if (hhi < 2500) return <span className="badge badge--yellow">Moderadamente concentrado (HHI {hhi.toFixed(0)})</span>;
  return <span className="badge badge--red">Altamente concentrado (HHI {hhi.toFixed(0)})</span>;
}

function AgeBadge({ months }) {
  if (months === null || months === undefined) return <span className="age-badge">N/A</span>;
  if (months < 12) return <span className="age-badge age-badge--new">{months}mo ← NUEVO</span>;
  if (months < 24) return <span className="age-badge age-badge--mid">{months}mo</span>;
  return <span className="age-badge age-badge--old">{months}mo</span>;
}

// ── Sortable column header ────────────────────────────────────────────────────

function SortTh({ label, field, sort, onSort }) {
  const active = sort.field === field;
  const arrow = active ? (sort.dir === "asc" ? " ↑" : " ↓") : " ↕";
  return (
    <th
      className={`sortable-th${active ? " sortable-th--active" : ""}`}
      onClick={() => onSort(field)}
    >
      {label}<span className="sort-arrow">{arrow}</span>
    </th>
  );
}

function MefsScore({ score, notes }) {
  const color = score >= 75 ? "#10b981" : score >= 55 ? "#f59e0b" : "#ef4444";
  const verdict =
    score >= 75 ? "FACTIBLE — Mercado accesible con producto diferenciado y buena ejecución."
    : score >= 55 ? "POSIBLE — Requiere diferenciación fuerte y capital para review velocity."
    : "ALTO RIESGO — Considera otra categoría o sub-nicho.";

  const radius = 52;
  const circ = 2 * Math.PI * radius;
  const dash = (score / 100) * circ;

  return (
    <div className="mefs-wrapper">
      <div className="mefs-gauge">
        <svg viewBox="0 0 120 120" width="140" height="140">
          <circle cx="60" cy="60" r={radius} fill="none" stroke="#1e293b" strokeWidth="12" />
          <circle
            cx="60" cy="60" r={radius} fill="none"
            stroke={color} strokeWidth="12"
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
            transform="rotate(-90 60 60)"
          />
          <text x="60" y="55" textAnchor="middle" fill={color} fontSize="22" fontWeight="bold">{score.toFixed(0)}</text>
          <text x="60" y="72" textAnchor="middle" fill="#94a3b8" fontSize="10">/ 100</text>
        </svg>
        <p className="mefs-verdict" style={{ color }}>{verdict}</p>
      </div>
      <ul className="mefs-notes">
        {notes.map((n, i) => (
          <li key={i} className={`mefs-note mefs-note--${n.type}`}>
            {n.type === "good" ? "✔" : n.type === "warn" ? "⚠" : "✗"} {n.text}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────

export default function Dashboard({ data, fileName, onReset }) {
  const { marketSize, hhi, top3Share, top5Share, brandBreakdown,
          competitors, freshness, margins, origins, cnShare, mxShare, mefs } = data;

  // ── Block A: participation input ──────────────────────────────────────────
  const [participation, setParticipation] = useState("");
  const participationPct = Math.min(100, Math.max(0, parseFloat(participation) || 0));
  const estimatedMonthly = marketSize.revMXN * (participationPct / 100);
  const estimatedAnnual  = marketSize.annualMXN * (participationPct / 100);

  // ── Block C: sortable competitors ────────────────────────────────────────
  const [compSort, setCompSort] = useState({ field: "date", dir: "desc" });

  const toggleSort = (field) => {
    setCompSort((prev) =>
      prev.field === field
        ? { field, dir: prev.dir === "asc" ? "desc" : "asc" }
        : { field, dir: "desc" }
    );
  };

  const sortedCompetitors = [...competitors].sort((a, b) => {
    let av = a[compSort.field];
    let bv = b[compSort.field];

    // nulls always last
    if (av == null && bv == null) return 0;
    if (av == null) return 1;
    if (bv == null) return -1;

    // Date objects → numeric
    if (av instanceof Date) av = av.getTime();
    if (bv instanceof Date) bv = bv.getTime();

    if (typeof av === "string") av = av.toLowerCase();
    if (typeof bv === "string") bv = bv.toLowerCase();

    const cmp = av < bv ? -1 : av > bv ? 1 : 0;
    return compSort.dir === "asc" ? cmp : -cmp;
  });

  return (
    <div className="dashboard">
      {/* Header */}
      <div className="dash-header">
        <div>
          <h1 className="dash-title">Helium 10 Xray — Market Analysis</h1>
          <p className="dash-file">📄 {fileName}</p>
          <p className="dash-file">{data.uniqueCount} ASINs únicos de {data.rawCount} filas</p>
        </div>
        <button className="btn-reset" onClick={onReset}>↩ Nuevo archivo</button>
      </div>

      {/* ── A. Market Size ── */}
      <section className="dash-section">
        <SectionHeader letter="A" title="Tamaño de Mercado (Estimado Mensual)" />
        <div className="stat-grid">
          <Stat label="Revenue mensual (MXN)" value={MXN(marketSize.revMXN)} />
          <Stat label="Estimado anual (MXN)" value={MXN(marketSize.annualMXN)} sub="×12 meses" />
          <Stat label="Productos únicos" value={marketSize.uniqueProducts} />
          <Stat label="Marcas únicas" value={marketSize.uniqueBrands} />
        </div>

        {/* Participation estimator */}
        <div className="participation-box">
          <p className="participation-label">
            Estima tu participación de mercado
          </p>
          <div className="participation-input-row">
            <input
              type="number"
              className="participation-input"
              min="0"
              max="100"
              step="0.1"
              placeholder="ej. 5"
              value={participation}
              onChange={(e) => setParticipation(e.target.value)}
            />
            <span className="participation-pct-symbol">%</span>
          </div>
          {participationPct > 0 && (
            <div className="stat-grid participation-results">
              <Stat
                label="Tu ingreso mensual estimado"
                value={MXN(estimatedMonthly)}
                color="#6366f1"
              />
              <Stat
                label="Tu ingreso anual estimado"
                value={MXN(estimatedAnnual)}
                sub={`${PCT(participationPct)} del mercado`}
                color="#6366f1"
              />
            </div>
          )}
        </div>
      </section>

      {/* ── B. HHI + Brand Breakdown ── */}
      <section className="dash-section">
        <SectionHeader letter="B" title="Concentración de Mercado (HHI) + Marcas" />
        <div className="hhi-row">
          <HhiBadge hhi={hhi} />
          <span className="badge badge--blue">Top-3: {PCT(top3Share)}</span>
          <span className="badge badge--blue">Top-5: {PCT(top5Share)}</span>
        </div>

        <div className="two-col">
          {/* Bar chart top 10 brands */}
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={brandBreakdown.slice(0, 10)} layout="vertical" margin={{ left: 8, right: 24 }}>
                <XAxis type="number" tickFormatter={(v) => `${v.toFixed(0)}%`} tick={{ fill: "#94a3b8", fontSize: 11 }} />
                <YAxis type="category" dataKey="brand" width={120} tick={{ fill: "#e2e8f0", fontSize: 11 }} />
                <Tooltip formatter={(v) => `${v.toFixed(1)}%`} contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                <Bar dataKey="share" name="Share" radius={[0, 4, 4, 0]}>
                  {brandBreakdown.slice(0, 10).map((_, i) => (
                    <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Brand table with Antigüedad column */}
          <div className="table-scroll">
            <table className="dash-table">
              <thead>
                <tr>
                  <th>Marca</th>
                  <th>Revenue</th>
                  <th>Share</th>
                  <th>Inicio</th>
                  <th>Antigüedad</th>
                  <th>País</th>
                </tr>
              </thead>
              <tbody>
                {brandBreakdown.map((b, i) => (
                  <tr key={i}>
                    <td>{b.brand}</td>
                    <td>{MXN(b.rev)}</td>
                    <td>
                      <span className={b.share >= 10 ? "tag tag--green" : b.share >= 5 ? "tag tag--yellow" : "tag tag--gray"}>
                        {PCT(b.share)}
                      </span>
                    </td>
                    <td>{b.startDate}</td>
                    <td><AgeBadge months={b.ageMo} /></td>
                    <td>
                      <span className="origin-tag" style={{ background: originColor(b.origin) + "33", color: originColor(b.origin) }}>
                        {b.origin}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── C. Competitors (sortable) ── */}
      <section className="dash-section">
        <SectionHeader letter="C" title="Top 10 Competidores — por Fecha de Entrada" />
        <div className="table-scroll">
          <table className="dash-table">
            <thead>
              <tr>
                <SortTh label="Marca"       field="brand"  sort={compSort} onSort={toggleSort} />
                <SortTh label="Entrada"     field="date"   sort={compSort} onSort={toggleSort} />
                <SortTh label="Antigüedad"  field="months" sort={compSort} onSort={toggleSort} />
                <SortTh label="Revenue"     field="rev"    sort={compSort} onSort={toggleSort} />
                <SortTh label="Share"       field="share"  sort={compSort} onSort={toggleSort} />
                <SortTh label="País"        field="origin" sort={compSort} onSort={toggleSort} />
              </tr>
            </thead>
            <tbody>
              {sortedCompetitors.map((c, i) => (
                <tr key={i}>
                  <td>{c.brand}</td>
                  <td>{c.date ? c.date.toLocaleDateString("es-MX", { month: "short", year: "numeric" }) : "N/A"}</td>
                  <td><AgeBadge months={c.months} /></td>
                  <td>{MXN(c.rev)}</td>
                  <td>{PCT(c.share)}</td>
                  <td>
                    <span className="origin-tag" style={{ background: originColor(c.origin) + "33", color: originColor(c.origin) }}>
                      {c.origin}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ── D. Market Freshness ── */}
      {freshness && (
        <section className="dash-section">
          <SectionHeader letter="D" title="Frescura del Mercado" />
          <div className="two-col">
            <div className="chart-box">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={freshness.chartData} cx="50%" cy="50%" innerRadius={60} outerRadius={100}
                    dataKey="value" nameKey="name" label={({ name, pct: p }) => `${name} (${p.toFixed(0)}%)`}
                    labelLine={{ stroke: "#475569" }}>
                    {freshness.chartData.map((_, i) => (
                      <Cell key={i} fill={["#10b981","#6366f1","#ef4444","#f59e0b"][i % 4]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v, n, { payload }) => [`${v} productos (${payload.pct.toFixed(1)}%)`, payload.name]} contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="freshness-stats">
              <Stat label="Productos con fecha" value={freshness.total} />
              <Stat label="Edad promedio" value={`${freshness.avgAgeMo.toFixed(0)} meses`} sub={`${(freshness.avgAgeMo / 12).toFixed(1)} años`} />
              <Stat label="< 12 meses" value={`${freshness.new12} (${PCT(freshness.pct12)})`}
                color={freshness.pct12 >= 30 ? "#10b981" : freshness.pct12 >= 15 ? "#f59e0b" : "#ef4444"} />
              <Stat label="< 24 meses" value={`${freshness.new24} (${PCT(freshness.pct24)})`} />
              <Stat label="> 36 meses" value={`${freshness.old36p} (${PCT(freshness.pct36p)})`} />
              <div className="freshness-verdict">
                {freshness.pct12 >= 30
                  ? <span className="badge badge--green">✔ DINÁMICO — Nuevos sellers siguen entrando</span>
                  : freshness.pct12 >= 15
                  ? <span className="badge badge--yellow">⚠ MODERADO — Jugadores maduros dominan</span>
                  : <span className="badge badge--red">✗ MADURO / BLOQUEADO — Alta barrera de entrada</span>}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* ── E. Margins ── */}
      {margins && (
        <section className="dash-section">
          <SectionHeader letter="E" title="Márgenes & Precio Promedio (Top Sellers)" />
          <div className="stat-grid stat-grid--3">
            <Stat label="Precio promedio" value={MXN(margins.avgPrice)}
              color={margins.avgPrice >= 600 ? "#10b981" : margins.avgPrice >= 350 ? "#f59e0b" : "#ef4444"} />
            <Stat label="Margen bruto promedio" value={PCT(margins.avgMargin)}
              sub="Después de FBA fees, antes de COGS"
              color={margins.avgMargin >= 70 ? "#10b981" : margins.avgMargin >= 60 ? "#f59e0b" : "#ef4444"} />
            <Stat label="Productos con datos de fee" value={margins.total} />
          </div>
          <div className="two-col">
            <div className="chart-box">
              <p className="chart-label">Distribución de Precios</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={margins.priceBuckets} margin={{ left: 0, right: 16 }}>
                  <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} />
                  <Tooltip formatter={(v, n, { payload }) => [`${v} productos (${payload.pct.toFixed(1)}%)`]} contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                  <Bar dataKey="count" name="Productos" radius={[4, 4, 0, 0]}>
                    {margins.priceBuckets.map((b, i) => (
                      <Cell key={i} fill={b.label.includes("500–799") ? "#10b981" : PALETTE[i % PALETTE.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="table-scroll">
              <table className="dash-table">
                <thead>
                  <tr><th>Marca</th><th>Precio</th><th>FBA Fee</th><th>Margen</th><th>ASIN Rev</th></tr>
                </thead>
                <tbody>
                  {margins.topSellers.map((d, i) => (
                    <tr key={i}>
                      <td>{d.brand}</td>
                      <td>{MXN(d.price)}</td>
                      <td>{MXN(d.fees)}</td>
                      <td><span className={d.margin >= 70 ? "tag tag--green" : "tag tag--yellow"}>{PCT(d.margin)}</span></td>
                      <td>{MXN(d.rev)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      )}

      {/* ── F. Origins ── */}
      <section className="dash-section">
        <SectionHeader letter="F" title="Origen de Sellers" />
        <div className="two-col">
          <div className="chart-box">
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={origins} cx="50%" cy="50%" outerRadius={100}
                  dataKey="count" nameKey="origin"
                  label={({ origin, pct: p }) => `${origin} ${p.toFixed(0)}%`}
                  labelLine={{ stroke: "#475569" }}>
                  {origins.map((o, i) => (
                    <Cell key={i} fill={originColor(o.origin)} />
                  ))}
                </Pie>
                <Tooltip formatter={(v, n, { payload }) => [`${v} (${payload.pct.toFixed(1)}%)`, payload.origin]} contentStyle={{ background: "#1e293b", border: "none", borderRadius: 8 }} />
                <Legend formatter={(v) => <span style={{ color: "#e2e8f0" }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="origins-list">
            {origins.map((o, i) => (
              <div key={i} className="origin-row">
                <span className="origin-tag" style={{ background: originColor(o.origin) + "33", color: originColor(o.origin), minWidth: 48 }}>{o.origin}</span>
                <div className="origin-bar-wrap">
                  <div className="origin-bar" style={{ width: `${o.pct}%`, background: originColor(o.origin) }} />
                </div>
                <span className="origin-pct">{PCT(o.pct)}</span>
                <span className="origin-count">{o.count} sellers</span>
              </div>
            ))}
            <div className="origins-verdict">
              {cnShare > 50
                ? <span className="badge badge--red">⚠ Dominancia China &gt;50% — competencia de precio muy alta</span>
                : cnShare > 30
                ? <span className="badge badge--yellow">⚠ China {cnShare.toFixed(0)}% — presión de precio moderada-alta</span>
                : <span className="badge badge--green">✔ China &lt;30% — menor presión de precio</span>}
              {mxShare >= 40 && (
                <span className="badge badge--green">✔ Sellers MX = {mxShare.toFixed(0)}% — mercado abierto a jugadores locales</span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── MEFS Score ── */}
      <section className="dash-section">
        <SectionHeader letter="★" title="Resumen Ejecutivo — MEFS Score" />
        <MefsScore score={mefs.score} notes={mefs.notes} />
      </section>
    </div>
  );
}

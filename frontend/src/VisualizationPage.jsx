import React, { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  AreaChart, Area, BarChart, Bar, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Cell, PieChart, Pie, ReferenceLine,
} from "recharts";
import "./VisualizationPage.css";

/* ──────────── constants ──────────── */
const CITIES = ["Chennai", "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Coimbatore"];
const CANDIDATE_PORTS = [8000, 8001, 8002];
let activeApiBase = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const resolveApiBase = async () => {
  try { await axios.get(`${activeApiBase}/api/health`, { timeout: 1200 }); return activeApiBase; } catch (_) {}
  for (const port of CANDIDATE_PORTS) {
    const url = `http://127.0.0.1:${port}`;
    try { await axios.get(`${url}/api/health`, { timeout: 1200 }); activeApiBase = url; return url; } catch (_) {}
  }
  return activeApiBase;
};

function getAqiColor(aqi) {
  if (aqi <= 50)  return { bg: "#10b981", label: "Good",               glow: "rgba(16,185,129,0.3)" };
  if (aqi <= 100) return { bg: "#f59e0b", label: "Moderate",           glow: "rgba(245,158,11,0.3)" };
  if (aqi <= 150) return { bg: "#f97316", label: "Unhealthy (Sensitive)", glow: "rgba(249,115,22,0.3)" };
  if (aqi <= 200) return { bg: "#ef4444", label: "Unhealthy",           glow: "rgba(239,68,68,0.3)" };
  if (aqi <= 300) return { bg: "#a855f7", label: "Very Unhealthy",      glow: "rgba(168,85,247,0.3)" };
  return              { bg: "#e11d48", label: "Hazardous",             glow: "rgba(225,29,72,0.3)" };
}

const POLLUTANT_COLORS = {
  pm25: "#06b6d4", pm10: "#f59e0b", no2: "#a855f7",
  so2: "#f97316", co: "#ef4444", o3: "#10b981",
};

const POLLUTANT_META = {
  pm25: { name: "PM2.5", unit: "µg/m³", safeLimit: 60 },
  pm10: { name: "PM10",  unit: "µg/m³", safeLimit: 100 },
  no2:  { name: "NO₂",   unit: "µg/m³", safeLimit: 80 },
  so2:  { name: "SO₂",   unit: "µg/m³", safeLimit: 80 },
  co:   { name: "CO",    unit: "ppm",    safeLimit: 4.0 },
  o3:   { name: "O₃",    unit: "µg/m³", safeLimit: 100 },
};

const TTStyle = {
  background: "rgba(15,23,42,0.96)",
  border: "1px solid rgba(255,255,255,0.12)",
  borderRadius: "10px",
  padding: "10px 14px",
  color: "#f8fafc",
  fontSize: "13px",
};

const AqiTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const v = payload[0].value;
  const c = getAqiColor(v);
  return (
    <div style={TTStyle}>
      <div style={{ marginBottom: 4, color: "#94a3b8", fontSize: 11 }}>{label}</div>
      <div style={{ color: c.bg, fontWeight: 700, fontSize: 18 }}>{Math.round(v)} AQI</div>
      <div style={{ color: c.bg, fontSize: 11 }}>{c.label}</div>
    </div>
  );
};

const PollutantTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={TTStyle}>
      <div style={{ marginBottom: 6, color: "#94a3b8", fontSize: 11 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color, fontSize: 13 }}>
          <strong>{p.name}</strong>: {p.value}
          {p.name === "CO" ? " ppm" : " µg/m³"}
        </div>
      ))}
    </div>
  );
};

function buildTimelineData(dashData) {
  if (!dashData) return [];
  return (dashData.timeline || []).map((step) => ({
    label: step.label,
    aqi: Math.round(step.aqi),
    type: step.type,
  }));
}

function buildPollutantRadarData(pollutants) {
  if (!pollutants) return [];
  return Object.entries(POLLUTANT_META).map(([key, meta]) => {
    const val = pollutants[key] ?? 0;
    const pct = Math.min(100, Math.round((val / meta.safeLimit) * 100));
    return { pollutant: meta.name, value: pct, raw: val, limit: meta.safeLimit };
  });
}

function buildCityComparisonData(ranking) {
  return (ranking || []).map((row) => ({
    city: row.city,
    aqi: Math.round(row.aqi),
    color: getAqiColor(row.aqi).bg,
  }));
}

function buildDiseaseRiskData(diseaseData) {
  if (!diseaseData?.diseases) return [];
  const keys = ["asthma", "bronchitis", "ihd", "copd"];
  const icons = { asthma: "Asthma", bronchitis: "Bronchitis", ihd: "IHD", copd: "COPD" };
  return keys.map((k) => ({
    name: icons[k],
    score: diseaseData.diseases[k]?.prone_score ?? 0,
    color: diseaseData.diseases[k]?.color ?? "#06b6d4",
  }));
}

function buildPollutantBreakdownData(pollutants) {
  if (!pollutants) return [];
  return Object.entries(POLLUTANT_META).map(([key, meta]) => ({
    name: meta.name,
    value: pollutants[key] ?? 0,
    fill: POLLUTANT_COLORS[key],
  }));
}

function getFallbackDiseaseData(aqi, pollutants = {}) {
  const pm25 = pollutants.pm25 || 35.0;
  const pm10 = pollutants.pm10 || 55.0;
  const so2  = pollutants.so2  || 12.0;
  const co   = pollutants.co   || 0.4;
  const o3   = pollutants.o3   || 45.0;
  const getStatus = (s) => s < 30 ? "#10b981" : s < 55 ? "#f59e0b" : s < 80 ? "#f97316" : "#ef4444";
  const as = Math.min(100, Math.round(aqi * 0.3 + pm25 * 0.4 + o3 * 0.2));
  const br = Math.min(100, Math.round(aqi * 0.25 + pm10 * 0.3 + so2 * 0.35));
  const ih = Math.min(100, Math.round(aqi * 0.35 + pm25 * 0.45 + co * 5.0));
  const cp = Math.min(100, Math.round(aqi * 0.3 + pm25 * 0.35 + pm10 * 0.2));
  return {
    diseases: {
      asthma:    { prone_score: as, color: getStatus(as) },
      bronchitis:{ prone_score: br, color: getStatus(br) },
      ihd:       { prone_score: ih, color: getStatus(ih) },
      copd:      { prone_score: cp, color: getStatus(cp) },
    }
  };
}

export default function VisualizationPage() {
  const navigate = useNavigate();

  const [selectedCity, setSelectedCity] = useState("Chennai");
  const [data, setData]         = useState(null);
  const [ranking, setRanking]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(new Date().toLocaleTimeString());
  const [activeChart, setActiveChart] = useState("timeline");

  const fetchData = useCallback(async (city, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);
    try {
      const baseUrl = await resolveApiBase();
      const [dashRes, rankRes] = await Promise.all([
        axios.get(`${baseUrl}/api/live-dashboard/${city}`),
        axios.get(`${baseUrl}/api/ranking`),
      ]);
      if (dashRes.data?.current) {
        setData(dashRes.data);
        setRanking(rankRes.data.ranking || []);
        setLastRefreshed(new Date().toLocaleTimeString());
      } else {
        throw new Error("Invalid payload structure.");
      }
    } catch (err) {
      setError("Unable to connect to live AQI backend. Please verify uvicorn is running.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(selectedCity); }, [selectedCity, fetchData]);

  const timelineData   = buildTimelineData(data);
  const radarData      = buildPollutantRadarData(data?.current?.pollutants);
  const cityCompData   = buildCityComparisonData(ranking);
  const diseaseData    = (data?.disease_assessment?.diseases || data?.personalized_advisories?.diseases)
    ? (data.disease_assessment || data.personalized_advisories)
    : getFallbackDiseaseData(data?.current?.aqi || 85, data?.current?.pollutants || {});
  const diseaseRisk    = buildDiseaseRiskData(diseaseData);
  const pollBreakdown  = buildPollutantBreakdownData(data?.current?.pollutants);
  const aqiStyle       = data ? getAqiColor(data.current.aqi) : getAqiColor(50);

  const CHART_TABS = [
    { key: "timeline",   label: "📈 AQI Timeline",        desc: "Past → Live → TCN Forecast" },
    { key: "pollutants", label: "🧪 Pollutant Radar",      desc: "% of safe-limit per pollutant" },
    { key: "cities",     label: "🏙️ City Comparison",      desc: "Live AQI across all stations" },
    { key: "disease",    label: "🫀 Disease Risk",         desc: "Vulnerability scores by disease" },
    { key: "breakdown",  label: "📊 Pollutant Breakdown",  desc: "Absolute concentrations" },
  ];

  return (
    <div className="vis-page">

      {/* HEADER */}
      <header className="vis-header">
        <div className="vis-header-inner">
          <div className="vis-logo-group">
            <div className="vis-logo-icon">AQI</div>
            <div>
              <span className="vis-brand-title">AeroRisk <span className="vis-live-tag">LIVE</span></span>
              <span className="vis-brand-sub">Data Visualization Centre</span>
            </div>
          </div>

          <div className="vis-city-selector">
            <span className="vis-city-label">Station:</span>
            {CITIES.map((c) => (
              <button
                key={c}
                className={`vis-city-chip ${selectedCity === c ? "active" : ""}`}
                onClick={() => setSelectedCity(c)}
              >{c}</button>
            ))}
          </div>

          <div className="vis-header-actions">
            <div className="vis-live-badge">
              <span className="vis-pulse-dot" />
              <span>LIVE DATA</span>
            </div>
            <button
              className={`vis-refresh-btn ${refreshing ? "spinning" : ""}`}
              onClick={() => fetchData(selectedCity, true)}
            >🔄 Sync</button>
            <button className="vis-back-btn" onClick={() => navigate("/")}>
              ← Dashboard
            </button>
          </div>
        </div>
      </header>

      {/* HERO KPI STRIP */}
      {data && !loading && (
        <div className="vis-hero-strip" style={{ borderColor: aqiStyle.bg, boxShadow: `0 0 40px ${aqiStyle.glow}` }}>
          <div className="vis-hero-inner">
            <div className="vis-hero-city">
              <span className="vis-flag">🇮🇳</span>
              <div>
                <h1 className="vis-hero-title">{data.city} Air Quality</h1>
                <p className="vis-hero-sub">Station: {data.station_name} · Source: {data.source?.toUpperCase()} API · Synced: {lastRefreshed}</p>
              </div>
            </div>

            <div className="vis-hero-kpis">
              <div className="vis-kpi-card" style={{ borderColor: aqiStyle.bg }}>
                <span className="vis-kpi-val" style={{ color: aqiStyle.bg }}>{Math.round(data.current.aqi)}</span>
                <span className="vis-kpi-lbl">Live AQI</span>
                <span className="vis-kpi-tag" style={{ backgroundColor: aqiStyle.bg }}>{aqiStyle.label}</span>
              </div>
              {data.forecast && (
                <div className="vis-kpi-card" style={{ borderColor: getAqiColor(data.forecast.predicted_aqi).bg }}>
                  <span className="vis-kpi-val" style={{ color: getAqiColor(data.forecast.predicted_aqi).bg }}>
                    {Math.round(data.forecast.predicted_aqi)}
                  </span>
                  <span className="vis-kpi-lbl">Tomorrow (TCN)</span>
                  <span className="vis-kpi-tag" style={{ backgroundColor: getAqiColor(data.forecast.predicted_aqi).bg }}>
                    {data.forecast.trend}
                  </span>
                </div>
              )}
              <div className="vis-kpi-card" style={{ borderColor: "#06b6d4" }}>
                <span className="vis-kpi-val" style={{ color: "#06b6d4" }}>
                  {data.current.pollutants?.pm25 ?? "—"}
                </span>
                <span className="vis-kpi-lbl">PM2.5 µg/m³</span>
                <span className="vis-kpi-tag" style={{ backgroundColor: "#06b6d4" }}>Fine Particles</span>
              </div>
              <div className="vis-kpi-card" style={{ borderColor: "#a855f7" }}>
                <span className="vis-kpi-val" style={{ color: "#a855f7" }}>
                  {data.current.pollutants?.no2 ?? "—"}
                </span>
                <span className="vis-kpi-lbl">NO₂ µg/m³</span>
                <span className="vis-kpi-tag" style={{ backgroundColor: "#a855f7" }}>Nitrogen Dioxide</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* LOADING */}
      {loading && (
        <div className="vis-loading">
          <div className="vis-spinner" />
          <p>Fetching visualization data for <strong>{selectedCity}</strong>...</p>
        </div>
      )}

      {/* ERROR */}
      {error && (
        <div className="vis-error">
          <span className="vis-error-icon">⚠️</span>
          <h2>Connection Error</h2>
          <p>{error}</p>
          <button className="vis-retry-btn" onClick={() => fetchData(selectedCity)}>Retry</button>
        </div>
      )}

      {/* CHARTS */}
      {data && !loading && (
        <main className="vis-main">

          {/* Tab Nav */}
          <div className="vis-tab-nav">
            {CHART_TABS.map((tab) => (
              <button
                key={tab.key}
                className={`vis-tab-btn ${activeChart === tab.key ? "active" : ""}`}
                onClick={() => setActiveChart(tab.key)}
              >
                <span>{tab.label}</span>
                <span className="vis-tab-desc">{tab.desc}</span>
              </button>
            ))}
          </div>

          {/* 1. AQI TIMELINE */}
          {activeChart === "timeline" && (
            <div className="vis-chart-card">
              <div className="vis-chart-header">
                <div>
                  <h2>📈 AQI Chronological Timeline</h2>
                  <p>Past observations → Live current reading → TCN-HAA neural network forecast</p>
                </div>
                <div className="vis-chart-legend">
                  <span className="legend-dot" style={{ background: "#94a3b8" }} /> Historical
                  <span className="legend-dot" style={{ background: "#06b6d4" }} /> Live
                  <span className="legend-dot" style={{ background: "#a855f7" }} /> TCN Forecast
                </div>
              </div>

              <ResponsiveContainer width="100%" height={360}>
                <AreaChart data={timelineData} margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                  <defs>
                    <linearGradient id="aqiGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#06b6d4" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="label"
                    stroke="#475569"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    angle={-25}
                    textAnchor="end"
                    height={50}
                  />
                  <YAxis stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, "auto"]} />
                  <Tooltip content={<AqiTooltip />} />
                  <ReferenceLine y={50}  stroke="#10b981" strokeDasharray="4 4" label={{ value: "Good",      fill: "#10b981", fontSize: 10, position: "insideTopRight" }} />
                  <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: "Moderate",  fill: "#f59e0b", fontSize: 10, position: "insideTopRight" }} />
                  <ReferenceLine y={150} stroke="#f97316" strokeDasharray="4 4" label={{ value: "Sensitive", fill: "#f97316", fontSize: 10, position: "insideTopRight" }} />
                  <Area
                    type="monotone"
                    dataKey="aqi"
                    stroke="#06b6d4"
                    strokeWidth={2.5}
                    fill="url(#aqiGrad)"
                    dot={(props) => {
                      const { cx, cy, payload } = props;
                      const c = payload.type === "LIVE" ? "#06b6d4" : payload.type === "TCN_PREDICTION" ? "#a855f7" : "#475569";
                      const r = payload.type === "LIVE" ? 7 : 4;
                      return <circle key={`dot-${cx}-${cy}`} cx={cx} cy={cy} r={r} fill={c} stroke="rgba(15,23,42,0.8)" strokeWidth={2} />;
                    }}
                  />
                </AreaChart>
              </ResponsiveContainer>

              {/* Timeline chips */}
              <div className="vis-timeline-row">
                {timelineData.map((step, i) => {
                  const s = getAqiColor(step.aqi);
                  const isLive = step.type === "LIVE";
                  const isTcn  = step.type === "TCN_PREDICTION";
                  return (
                    <div key={i}
                      className={`vis-tl-chip ${isLive ? "is-live" : isTcn ? "is-tcn" : ""}`}
                      style={{ borderColor: isLive ? "#06b6d4" : isTcn ? "#a855f7" : "rgba(255,255,255,0.08)" }}
                    >
                      <span className="tl-chip-aqi" style={{ color: s.bg }}>{step.aqi}</span>
                      <span className="tl-chip-cat" style={{ color: s.bg, fontSize: 10 }}>{s.label}</span>
                      <span className="tl-chip-label">{step.label}</span>
                      {isLive && <span className="tl-live-dot" />}
                      {isTcn  && <span className="tl-tcn-badge">TCN</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 2. POLLUTANT RADAR */}
          {activeChart === "pollutants" && (
            <div className="vis-chart-card">
              <div className="vis-chart-header">
                <div>
                  <h2>🧪 Multi-Pollutant Radar Analysis</h2>
                  <p>Pollutant concentrations expressed as % of WHO/CPCB safe exposure limits for {data.city}</p>
                </div>
                <div className="vis-chart-legend">
                  <span className="legend-dot" style={{ background: "#06b6d4" }} /> % of Safe Limit
                  <span className="legend-dot" style={{ background: "#ef4444" }} /> Exceeded (&gt;100%)
                </div>
              </div>

              <div className="vis-radar-layout">
                <ResponsiveContainer width="55%" height={380}>
                  <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="pollutant" tick={{ fill: "#94a3b8", fontSize: 13, fontWeight: 600 }} />
                    <PolarRadiusAxis angle={90} domain={[0, 120]} tick={{ fill: "#64748b", fontSize: 10 }} tickCount={4} />
                    <Radar
                      name="% of Safe Limit"
                      dataKey="value"
                      stroke="#06b6d4"
                      fill="#06b6d4"
                      fillOpacity={0.22}
                      strokeWidth={2}
                      dot={{ r: 5, fill: "#06b6d4" }}
                    />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const d = payload[0].payload;
                        const exceeded = d.value > 100;
                        return (
                          <div style={TTStyle}>
                            <div style={{ fontWeight: 700, color: exceeded ? "#ef4444" : "#06b6d4", fontSize: 15 }}>{d.pollutant}</div>
                            <div style={{ color: "#94a3b8" }}>Raw: <strong style={{ color: "#f8fafc" }}>{d.raw}</strong></div>
                            <div style={{ color: "#94a3b8" }}>Safe Limit: <strong style={{ color: "#f8fafc" }}>{d.limit}</strong></div>
                            <div style={{ color: exceeded ? "#ef4444" : "#10b981", fontWeight: 700, marginTop: 4 }}>
                              {d.value}% of safe limit {exceeded ? "⚠️ EXCEEDED" : "✅ Safe"}
                            </div>
                          </div>
                        );
                      }}
                    />
                    <Legend formatter={() => "% of Safe Limit"} wrapperStyle={{ color: "#94a3b8" }} />
                  </RadarChart>
                </ResponsiveContainer>

                <div className="vis-pollutant-stats">
                  {radarData.map((p) => {
                    const exceeded = p.value > 100;
                    const color = exceeded ? "#ef4444" : p.value > 70 ? "#f59e0b" : "#10b981";
                    return (
                      <div key={p.pollutant} className="vis-poll-stat-card" style={{ borderColor: color }}>
                        <div className="poll-stat-name" style={{ color }}>{p.pollutant}</div>
                        <div className="poll-stat-raw">{p.raw} <span>/ {p.limit}</span></div>
                        <div className="poll-stat-bar-track">
                          <div className="poll-stat-bar-fill"
                            style={{ width: `${Math.min(100, p.value)}%`, backgroundColor: color }} />
                        </div>
                        <div className="poll-stat-pct" style={{ color }}>{p.value}% {exceeded ? "⚠️" : ""}</div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* 3. CITY COMPARISON */}
          {activeChart === "cities" && (
            <div className="vis-chart-card">
              <div className="vis-chart-header">
                <div>
                  <h2>🏙️ Indian Cities AQI Comparison</h2>
                  <p>Live AQI ranking across all monitored Indian stations — lowest to highest pollution</p>
                </div>
              </div>

              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={cityCompData} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="city" stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <YAxis stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, "auto"]} />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (!active || !payload?.length) return null;
                      const c = getAqiColor(payload[0].value);
                      return (
                        <div style={TTStyle}>
                          <div style={{ color: "#94a3b8" }}>{label}</div>
                          <div style={{ color: c.bg, fontWeight: 700, fontSize: 18 }}>{payload[0].value} AQI</div>
                          <div style={{ color: c.bg }}>{c.label}</div>
                        </div>
                      );
                    }}
                  />
                  <Bar dataKey="aqi" radius={[6, 6, 0, 0]}>
                    {cityCompData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.color}
                        opacity={entry.city === selectedCity ? 1 : 0.6}
                        stroke={entry.city === selectedCity ? "#fff" : "transparent"}
                        strokeWidth={entry.city === selectedCity ? 1.5 : 0}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <div className="vis-city-rank-grid">
                {cityCompData.slice().sort((a, b) => a.aqi - b.aqi).map((c, i) => {
                  const s = getAqiColor(c.aqi);
                  const isActive = c.city === selectedCity;
                  return (
                    <div key={c.city}
                      className={`vis-city-rank-card ${isActive ? "active" : ""}`}
                      style={{ borderColor: isActive ? s.bg : "rgba(255,255,255,0.08)" }}
                      onClick={() => setSelectedCity(c.city)}
                    >
                      <span className="rank-num" style={{ color: s.bg }}>#{i + 1}</span>
                      <span className="rank-city">{c.city}</span>
                      <span className="rank-aqi" style={{ color: s.bg }}>{c.aqi}</span>
                      <span className="rank-label" style={{ backgroundColor: s.bg }}>{s.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* 4. DISEASE RISK */}
          {activeChart === "disease" && (
            <div className="vis-chart-card">
              <div className="vis-chart-header">
                <div>
                  <h2>🫀 Disease Vulnerability Risk Chart</h2>
                  <p>Clinically computed prone-risk index (0–100%) for {data.city} based on live pollutant concentrations</p>
                </div>
              </div>

              <div className="vis-disease-layout">
                <div className="vis-disease-gauges">
                  {diseaseRisk.map((d) => {
                    const circumference = 2 * Math.PI * 42;
                    const filled = (d.score / 100) * circumference;
                    const label = d.score < 30 ? "Low" : d.score < 55 ? "Moderate" : d.score < 80 ? "High" : "Critical";
                    return (
                      <div key={d.name} className="vis-gauge-card">
                        <svg width="110" height="110" viewBox="0 0 110 110">
                          <circle cx="55" cy="55" r="42" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="10" />
                          <circle
                            cx="55" cy="55" r="42" fill="none"
                            stroke={d.color} strokeWidth="10"
                            strokeDasharray={`${filled} ${circumference - filled}`}
                            strokeLinecap="round"
                            transform="rotate(-90 55 55)"
                            style={{ filter: `drop-shadow(0 0 6px ${d.color})` }}
                          />
                          <text x="55" y="51" textAnchor="middle" fill={d.color} fontSize="17" fontWeight="800">{d.score}%</text>
                          <text x="55" y="65" textAnchor="middle" fill="#94a3b8" fontSize="10">{label}</text>
                        </svg>
                        <div className="vis-gauge-name">{d.name}</div>
                        <div className="vis-gauge-bar-track">
                          <div className="vis-gauge-bar-fill"
                            style={{ width: `${d.score}%`, backgroundColor: d.color, boxShadow: `0 0 8px ${d.color}` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="vis-disease-bars">
                  <h3>Comparative Vulnerability Index</h3>
                  {diseaseRisk.slice().sort((a, b) => b.score - a.score).map((d) => (
                    <div key={d.name} className="vis-dis-bar-row">
                      <span className="vis-dis-bar-name">{d.name}</span>
                      <div className="vis-dis-bar-track">
                        <div className="vis-dis-bar-fill"
                          style={{ width: `${d.score}%`, background: `linear-gradient(90deg, ${d.color}cc, ${d.color})`, boxShadow: `0 0 10px ${d.color}55` }} />
                        <span className="vis-dis-bar-val" style={{ color: d.color }}>{d.score}%</span>
                      </div>
                    </div>
                  ))}

                  <div className="vis-disease-legend">
                    <span className="dis-leg-item"><span style={{ background: "#10b981" }} />0–29: Low Risk</span>
                    <span className="dis-leg-item"><span style={{ background: "#f59e0b" }} />30–54: Moderate</span>
                    <span className="dis-leg-item"><span style={{ background: "#f97316" }} />55–79: High Risk</span>
                    <span className="dis-leg-item"><span style={{ background: "#ef4444" }} />80–100: Critical</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 5. POLLUTANT BREAKDOWN */}
          {activeChart === "breakdown" && (
            <div className="vis-chart-card">
              <div className="vis-chart-header">
                <div>
                  <h2>📊 Pollutant Concentration Breakdown</h2>
                  <p>Absolute pollutant readings for {data.city} compared against CPCB/WHO safe thresholds</p>
                </div>
              </div>

              <div className="vis-breakdown-layout">
                <div className="vis-breakdown-pie">
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={pollBreakdown}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={110}
                        paddingAngle={3}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        labelLine={{ stroke: "rgba(255,255,255,0.2)" }}
                      >
                        {pollBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill}
                            style={{ filter: `drop-shadow(0 0 6px ${entry.fill}88)` }} />
                        ))}
                      </Pie>
                      <Tooltip
                        content={({ active, payload }) => {
                          if (!active || !payload?.length) return null;
                          const p = payload[0].payload;
                          return (
                            <div style={TTStyle}>
                              <div style={{ color: p.fill, fontWeight: 700 }}>{p.name}</div>
                              <div style={{ color: "#94a3b8" }}>Value: <strong style={{ color: "#f8fafc" }}>{p.value}</strong></div>
                            </div>
                          );
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="vis-breakdown-bar">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart
                      data={Object.entries(POLLUTANT_META).map(([key, meta]) => ({
                        name: meta.name,
                        Measured: data.current.pollutants?.[key] ?? 0,
                        "Safe Limit": meta.safeLimit,
                      }))}
                      margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                      <XAxis dataKey="name" stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 11 }} />
                      <YAxis stroke="#475569" tick={{ fill: "#94a3b8", fontSize: 10 }} />
                      <Tooltip content={<PollutantTooltip />} />
                      <Legend formatter={(v) => <span style={{ color: "#94a3b8", fontSize: 12 }}>{v}</span>} />
                      <Bar dataKey="Measured" radius={[4, 4, 0, 0]}>
                        {Object.keys(POLLUTANT_META).map((key, i) => (
                          <Cell key={i} fill={POLLUTANT_COLORS[key]} />
                        ))}
                      </Bar>
                      <Bar dataKey="Safe Limit" fill="rgba(255,255,255,0.12)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="vis-breakdown-table">
                <table>
                  <thead>
                    <tr>
                      <th>Pollutant</th>
                      <th>Measured</th>
                      <th>Safe Limit</th>
                      <th>% of Limit</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(POLLUTANT_META).map(([key, meta]) => {
                      const val = data.current.pollutants?.[key] ?? 0;
                      const pct = Math.round((val / meta.safeLimit) * 100);
                      const exceeded = pct > 100;
                      const statusColor = pct > 100 ? "#ef4444" : pct > 70 ? "#f59e0b" : "#10b981";
                      return (
                        <tr key={key}>
                          <td>
                            <span className="poll-name-dot" style={{ background: POLLUTANT_COLORS[key] }} />
                            <strong>{meta.name}</strong>
                          </td>
                          <td style={{ color: POLLUTANT_COLORS[key], fontWeight: 700 }}>
                            {val} {meta.unit}
                          </td>
                          <td style={{ color: "#64748b" }}>{meta.safeLimit} {meta.unit}</td>
                          <td>
                            <div className="table-pct-bar">
                              <div style={{ width: `${Math.min(100, pct)}%`, background: statusColor }} />
                            </div>
                            <span style={{ color: statusColor, fontWeight: 600 }}>{pct}%</span>
                          </td>
                          <td>
                            <span className="poll-status-badge"
                              style={{ background: `${statusColor}22`, color: statusColor, border: `1px solid ${statusColor}55` }}>
                              {exceeded ? "⚠️ Exceeded" : pct > 70 ? "⚡ Elevated" : "✅ Safe"}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TCN Feature Contributions (always shown at bottom) */}
          {data?.forecast?.feature_contributions?.length > 0 && (
            <div className="vis-chart-card vis-tcn-card">
              <div className="vis-chart-header">
                <div>
                  <h2>🧠 TCN-HAA Feature Contribution Explainability</h2>
                  <p>Percentage weight of each pollutant in the TCN forecast prediction for {data.city}</p>
                </div>
              </div>

              <div className="vis-tcn-layout">
                <ResponsiveContainer width="45%" height={260}>
                  <PieChart>
                    <Pie
                      data={data.forecast.feature_contributions}
                      cx="50%" cy="50%"
                      outerRadius={100}
                      dataKey="percentage"
                      nameKey="feature"
                      label={({ feature, percentage }) => `${feature} ${percentage}%`}
                    >
                      {data.forecast.feature_contributions.map((fc, i) => (
                        <Cell key={i} fill={fc.color} style={{ filter: `drop-shadow(0 0 5px ${fc.color}88)` }} />
                      ))}
                    </Pie>
                    <Tooltip
                      content={({ active, payload }) => {
                        if (!active || !payload?.length) return null;
                        const p = payload[0].payload;
                        return (
                          <div style={TTStyle}>
                            <div style={{ color: p.color, fontWeight: 700 }}>{p.feature}</div>
                            <div style={{ color: "#94a3b8" }}>Contribution: <strong style={{ color: p.color }}>{p.percentage}%</strong></div>
                          </div>
                        );
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>

                <div className="vis-tcn-bars">
                  {data.forecast.feature_contributions.map((fc, i) => (
                    <div key={i} className="vis-tcn-bar-row">
                      <span className="vis-tcn-feat">{fc.feature}</span>
                      <div className="vis-tcn-track">
                        <div className="vis-tcn-fill"
                          style={{ width: `${fc.percentage}%`, background: `linear-gradient(90deg,${fc.color}88,${fc.color})` }} />
                      </div>
                      <span className="vis-tcn-pct" style={{ color: fc.color }}>{fc.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </main>
      )}

      {/* FOOTER */}
      <footer className="vis-footer">
        <div className="vis-footer-inner">
          <span>🍃 AeroRisk LIVE — Visualization Centre</span>
          <span>Data: Open-Meteo · CPCB · US EPA · TCN-HAA Neural Engine</span>
          <span>© 2026 AeroRisk System</span>
        </div>
      </footer>

    </div>
  );
}

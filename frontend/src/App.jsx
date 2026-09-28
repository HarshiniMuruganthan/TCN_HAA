import React, { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

const CITIES = ["Chennai", "Delhi", "Mumbai", "Bengaluru", "Hyderabad", "Coimbatore"];
const CANDIDATE_PORTS = [8000, 8001, 8002];

let activeApiBase = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const resolveApiBase = async () => {
  try {
    await axios.get(`${activeApiBase}/api/health`, { timeout: 1200 });
    return activeApiBase;
  } catch (e) {
    // Probe
  }

  for (const port of CANDIDATE_PORTS) {
    const targetUrl = `http://127.0.0.1:${port}`;
    try {
      await axios.get(`${targetUrl}/api/health`, { timeout: 1200 });
      activeApiBase = targetUrl;
      return targetUrl;
    } catch (e) {
      // Continue
    }
  }
  return activeApiBase;
};

// Standard AQI.in & US EPA Color Mapping
function getAqiColor(aqi) {
  if (aqi <= 50) return {
    bg: "#10b981", border: "rgba(16, 185, 129, 0.4)", text: "#10b981", label: "Good", risk: "Low Risk",
    desc: "Air quality is considered satisfactory, and air pollution poses little or no risk.", light: "rgba(16, 185, 129, 0.1)"
  };
  if (aqi <= 100) return {
    bg: "#f59e0b", border: "rgba(245, 158, 11, 0.4)", text: "#f59e0b", label: "Moderate", risk: "Moderate Risk",
    desc: "Air quality is acceptable; sensitive individuals should take precautions outdoors.", light: "rgba(245, 158, 11, 0.1)"
  };
  if (aqi <= 150) return {
    bg: "#f97316", border: "rgba(249, 115, 22, 0.4)", text: "#f97316", label: "Unhealthy for Sensitive", risk: "Elevated Risk",
    desc: "Members of sensitive groups may experience health effects. The general public is less likely to be affected.", light: "rgba(249, 115, 22, 0.1)"
  };
  if (aqi <= 200) return {
    bg: "#ef4444", border: "rgba(239, 68, 68, 0.4)", text: "#ef4444", label: "Unhealthy", risk: "High Risk",
    desc: "Everyone may begin to experience health effects; sensitive groups may experience more serious effects.", light: "rgba(239, 68, 68, 0.1)"
  };
  if (aqi <= 300) return {
    bg: "#a855f7", border: "rgba(168, 85, 247, 0.4)", text: "#a855f7", label: "Very Unhealthy", risk: "Very High Risk",
    desc: "Health alert: everyone may experience more serious health effects.", light: "rgba(168, 85, 247, 0.1)"
  };
  return {
    bg: "#e11d48", border: "rgba(225, 29, 72, 0.4)", text: "#e11d48", label: "Hazardous", risk: "Severe Risk",
    desc: "Health warnings of emergency conditions. The entire population is likely to be affected.", light: "rgba(225, 29, 72, 0.1)"
  };
}

const POLLUTANT_META = {
  pm25: { name: "PM2.5", label: "Fine Particulate Matter", unit: "µg/m³", limit: 60, desc: "Tiny inhaled particles entering deep lungs." },
  pm10: { name: "PM10", label: "Coarse Particulate Matter", unit: "µg/m³", limit: 100, desc: "Inhalable dust, pollen, and mold spores." },
  no2:  { name: "NO₂", label: "Nitrogen Dioxide", unit: "µg/m³", limit: 80, desc: "Traffic & power plant emission gas." },
  so2:  { name: "SO₂", label: "Sulfur Dioxide", unit: "µg/m³", limit: 80, desc: "Industrial fossil fuel combustion." },
  co:   { name: "CO", label: "Carbon Monoxide", unit: "ppm", limit: 4.0, desc: "Odorless toxic vehicle exhaust gas." },
  o3:   { name: "O₃", label: "Ground-Level Ozone", unit: "µg/m³", limit: 100, desc: "Photochemical smog formed by sunlight + exhaust." },
};

// Client-side fallback disease vulnerability calculator
function getFallbackDiseaseData(aqi, pollutants = {}) {
  const pm25 = pollutants.pm25 || 35.0;
  const pm10 = pollutants.pm10 || 55.0;
  const no2 = pollutants.no2 || 20.0;
  const so2 = pollutants.so2 || 12.0;
  const co = pollutants.co || 0.4;
  const o3 = pollutants.o3 || 45.0;

  const asthmaScore = Math.min(100, Math.round((aqi * 0.3) + (pm25 * 0.4) + (o3 * 0.2)));
  const bronchitisScore = Math.min(100, Math.round((aqi * 0.25) + (pm10 * 0.3) + (so2 * 0.35)));
  const ihdScore = Math.min(100, Math.round((aqi * 0.35) + (pm25 * 0.45) + (co * 5.0)));
  const copdScore = Math.min(100, Math.round((aqi * 0.3) + (pm25 * 0.35) + (pm10 * 0.2)));

  const getStatus = (score) => {
    if (score < 30) return { status: "Low Vulnerability", badge: "Low Prone Risk", color: "#10b981" };
    if (score < 55) return { status: "Moderate Vulnerability", badge: "Moderately Prone", color: "#f59e0b" };
    if (score < 80) return { status: "High Vulnerability", badge: "Highly Prone", color: "#f97316" };
    return { status: "Critical Hazard", badge: "Extremely Prone", color: "#ef4444" };
  };

  const astStat = getStatus(asthmaScore);
  const brStat = getStatus(bronchitisScore);
  const ihdStat = getStatus(ihdScore);
  const copdStat = getStatus(copdScore);

  return {
    highest_risk_disease: ihdScore >= asthmaScore ? "Ischemic Heart Disease (IHD)*" : "Asthma",
    highest_risk_score: Math.max(asthmaScore, bronchitisScore, ihdScore, copdScore),
    highest_risk_status: "High Vulnerability",
    diseases: {
      asthma: {
        disease_name: "Asthma",
        full_name: "Bronchial Asthma & Hyperresponsiveness",
        icon: "🫁",
        prone_score: asthmaScore,
        prone_status: astStat.status,
        badge: astStat.badge,
        color: astStat.color,
        physiological_mechanism: "Elevated PM2.5 and reactive oxidant gases penetrate deep into the terminal bronchioles, triggering neurogenic inflammation, mast cell degranulation, mucus plugging, and acute smooth muscle bronchospasm.",
        key_triggers: ["PM2.5 (Fine Particles)", "Ground-Level Ozone (O₃)", "NO₂ (Traffic Gas)"],
        clinical_guidance: [
          "Shift high-intensity cardio exercises indoors into air-conditioned, HEPA-filtered rooms.",
          "Keep quick-relief rescue inhaler (Albuterol/Salbutamol) readily accessible at all times.",
          "Wear a certified N95 respirator mask tightly fitted over nose and mouth outdoors.",
          "Monitor Peak Expiratory Flow Rate (PEFR); initiate asthma action plan if readings fall.",
        ],
        alert_summary: "Elevated risk of airway hyperresponsiveness, wheezing, and sudden bronchospasm episodes.",
      },
      bronchitis: {
        disease_name: "Bronchitis",
        full_name: "Acute & Chronic Bronchitis (Airway Mucosal Inflammation)",
        icon: "💨",
        prone_score: bronchitisScore,
        prone_status: brStat.status,
        badge: brStat.badge,
        color: brStat.color,
        physiological_mechanism: "Inhaled coarse particulates (PM10) and sulfur dioxide react with mucosal moisture to form acidic irritants, causing goblet cell hyperplasia, thick viscous phlegm production, epithelial shedding, and frequent paroxysmal coughing fits.",
        key_triggers: ["SO₂ (Industrial Combustion)", "PM10 (Coarse Inhalables)", "NO₂ (Emissions)"],
        clinical_guidance: [
          "Avoid cold morning outdoor air and dusty vehicular corridors that trigger severe cough spasms.",
          "Perform saline steam inhalation in the evening to soothe inflamed tracheal membranes.",
          "Stay well hydrated to thin bronchial secretions and aid mucociliary clearance.",
          "Consult physician if sputum becomes purulent (yellow/green) or fever develops.",
        ],
        alert_summary: "High probability of bronchial mucosal swelling, heavy sputum production, and persistent cough.",
      },
      ihd: {
        disease_name: "Ischemic Heart Disease (IHD)*",
        full_name: "Ischemic Heart Disease (Coronary Artery Disease & Myocardial Infarction)",
        icon: "❤️",
        prone_score: ihdScore,
        prone_status: ihdStat.status,
        badge: ihdStat.badge,
        color: ihdStat.color,
        physiological_mechanism: "Inhaled ultrafine PM2.5 translocates across alveolar-capillary membranes into vascular circulation, provoking systemic oxidative stress, endothelial dysfunction, coronary vasoconstriction, and rupture of vulnerable atherosclerotic plaques. Concurrently, CO forms carboxyhemoglobin, reducing myocardial oxygen delivery.",
        key_triggers: ["Ultrafine PM2.5 Infiltration", "Carbon Monoxide (CO)", "Traffic Combustion Nanoparticles"],
        clinical_guidance: [
          "Strictly avoid heavy outdoor manual exertion, uphill cycling, or fast running.",
          "Carry emergency sublingual Nitroglycerin if diagnosed with ischemic angina.",
          "Monitor blood pressure and report chest pressure, pain radiating to left arm/jaw immediately.",
          "Stay indoors in climate-controlled air; maintain routine cardiovascular medications.",
        ],
        alert_summary: "Critical cardiovascular threat: Elevated danger of acute myocardial ischemia and coronary events.",
      },
      copd: {
        disease_name: "COPD",
        full_name: "Chronic Obstructive Pulmonary Disease (Emphysema & Chronic Airflow Limitation)",
        icon: "🫁",
        prone_score: copdScore,
        prone_status: copdStat.status,
        badge: copdStat.badge,
        color: copdStat.color,
        physiological_mechanism: "Severe neutrophilic airway inflammation, loss of alveolar elastic recoil, and air trapping. Pollutants cripple local antibacterial defense, often precipitating acute infectious exacerbations of COPD (AECOPD) with rapid decline in FEV1.",
        key_triggers: ["PM2.5 Penetration into Alveoli", "Sulfur Dioxide (SO₂)", "Oxidative Gas Stress"],
        clinical_guidance: [
          "Remain indoors; do not step outside without strict N95 respirator seal.",
          "Monitor oxygen saturation (SpO2) using a pulse oximeter twice daily; alert doctor if SpO2 drops below 90%.",
          "Have long-acting bronchodilators (LABA/LAMA) and standby rescue inhalers readily available.",
          "Run continuous indoor HEPA air filtration to prevent indoor particulate accumulation.",
        ],
        alert_summary: "High hazard of acute COPD exacerbation, severe dyspnea, and respiratory compromise.",
      },
    },
  };
}

export default function App() {
  const [selectedCity, setSelectedCity] = useState("Chennai");
  const [searchQuery, setSearchQuery] = useState("");

  // Specific Disease Tab Selection State
  const [selectedDiseaseTab, setSelectedDiseaseTab] = useState("asthma");

  // Exposure Risk Simulator States
  const [simProfile, setSimProfile] = useState("asthma");
  const [simActivity, setSimActivity] = useState("running");
  const [simDuration, setSimDuration] = useState(60);
  const [simResult, setSimResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const [data, setData] = useState(null);
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefreshed, setLastRefreshed] = useState(new Date().toLocaleTimeString());

  const fetchCityDashboard = async (city, isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError(null);

    try {
      const baseUrl = await resolveApiBase();
      const [dashRes, rankRes] = await Promise.all([
        axios.get(`${baseUrl}/api/live-dashboard/${city}`),
        axios.get(`${baseUrl}/api/ranking`),
      ]);
      if (dashRes.data && dashRes.data.current) {
        setData(dashRes.data);
        setRanking(rankRes.data.ranking || []);
        setLastRefreshed(new Date().toLocaleTimeString());
        
        // Run initial exposure simulation
        runExposureSimulation(city, simProfile, simActivity, simDuration, baseUrl);
      } else {
        throw new Error("Invalid payload structure received from backend.");
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      setError(`Unable to connect to live AQI backend server. Please verify uvicorn backend is running.`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const runExposureSimulation = async (city, prof, act, dur, baseUrl = null) => {
    setSimLoading(true);
    try {
      const api = baseUrl || await resolveApiBase();
      const res = await axios.get(
        `${api}/api/simulate-exposure?city=${city}&profile=${prof}&activity=${act}&duration_minutes=${dur}`
      );
      setSimResult(res.data);
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setSimLoading(false);
    }
  };

  useEffect(() => {
    fetchCityDashboard(selectedCity);
  }, [selectedCity]);

  // Re-run simulation when controls change
  const handleSimChange = (prof, act, dur) => {
    setSimProfile(prof);
    setSimActivity(act);
    setSimDuration(dur);
    runExposureSimulation(selectedCity, prof, act, dur);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    const matched = CITIES.find(c => c.toLowerCase() === searchQuery.trim().toLowerCase());
    if (matched) {
      setSelectedCity(matched);
      setSearchQuery("");
    } else {
      alert(`City '${searchQuery}' not found in active stations. Try: ${CITIES.join(", ")}`);
    }
  };

  const aqiStyle = data ? getAqiColor(data.current.aqi) : getAqiColor(50);
  const forecastAqiStyle = data?.forecast ? getAqiColor(data.forecast.predicted_aqi) : null;

  // Disease assessment data (from backend or high-precision fallback)
  const diseaseData = (data?.disease_assessment && data.disease_assessment.diseases)
    ? data.disease_assessment
    : (data?.personalized_advisories && data.personalized_advisories.diseases)
      ? data.personalized_advisories
      : getFallbackDiseaseData(data?.current?.aqi || 85, data?.current?.pollutants || {});

  const currentDiseaseInfo = diseaseData?.diseases?.[selectedDiseaseTab] || diseaseData?.diseases?.asthma;

  return (
    <div className="aqi-in-app">
      {/* ── 1. Header ─────────────────────────────────────────────── */}
      <header className="aqi-header">
        <div className="aqi-header-container">
          <div className="aqi-logo-group">
            <div className="aqi-logo-icon">AQI</div>
            <div className="aqi-logo-text">
              <span className="aqi-brand-title">AeroRisk <span className="aqi-tag-live">LIVE</span></span>
              <span className="aqi-brand-subtitle">Explainable Real-Time Air Quality Monitoring, TCN Prediction & Disease Risk System</span>
            </div>
          </div>

          <div className="aqi-header-center">
            <form onSubmit={handleSearchSubmit} className="aqi-search-form">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Search City (e.g. Chennai, Mumbai, Delhi)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="aqi-search-input"
              />
              <button type="submit" className="aqi-search-btn">Search</button>
            </form>
          </div>

          <div className="aqi-header-right">
            <div className="live-feed-badge">
              <span className="live-pulse-dot"></span>
              <span>LIVE STATION FEED</span>
            </div>
            <button
              className={`aqi-refresh-button ${refreshing ? "spinning" : ""}`}
              onClick={() => fetchCityDashboard(selectedCity, true)}
              title="Sync Live Observations"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </header>

      {/* ── 2. City Selector Bar ──────────────────────────────────── */}
      <div className="aqi-city-bar">
        <div className="aqi-city-bar-inner">
          <div className="location-breadcrumbs">
            <span className="country-flag">🇮🇳</span>
            <span>India</span>
            <span className="crumb-sep">/</span>
            <strong>{selectedCity} Air Quality</strong>
          </div>

          <div className="city-quick-selector">
            <span className="quick-label">Select City:</span>
            {CITIES.map((c) => (
              <button
                key={c}
                className={`quick-city-chip ${selectedCity === c ? "active" : ""}`}
                onClick={() => setSelectedCity(c)}
              >
                {c}
              </button>
            ))}
          </div>

          <span className="sync-timestamp">Last Synced: {lastRefreshed}</span>
        </div>
      </div>

      {loading ? (
        <div className="aqi-loading-screen">
          <div className="aqi-spinner"></div>
          <p>Fetching real-time station observations for <strong>{selectedCity}</strong>...</p>
        </div>
      ) : error ? (
        <div className="aqi-error-screen">
          <span className="error-icon">⚠️</span>
          <h2>Live Connection Error</h2>
          <p>{error}</p>
          <button className="aqi-retry-btn" onClick={() => fetchCityDashboard(selectedCity)}>
            Retry Connecting to Live Station
          </button>
        </div>
      ) : data ? (
        <main className="aqi-main-wrapper">

          {/* ── SMART AQI ALERT BANNER ──────────────────────────────── */}
          {data.smart_alert && (
            <div className={`smart-alert-banner severity-${data.smart_alert.severity.toLowerCase()}`}>
              <div className="smart-alert-left">
                <span className="smart-alert-icon">{data.smart_alert.icon}</span>
                <div>
                  <div className="smart-alert-badge-row">
                    <span className="smart-alert-badge">{data.smart_alert.type}</span>
                    <strong className="smart-alert-title">{data.smart_alert.title}</strong>
                  </div>
                  <p className="smart-alert-msg">{data.smart_alert.message}</p>
                </div>
              </div>
              {data.smart_alert.trend_delta > 0 && (
                <div className="smart-alert-meta">
                  <span className="delta-tag">Proactive Early Warning</span>
                  <strong>+{data.smart_alert.trend_delta} AQI Delta</strong>
                </div>
              )}
            </div>
          )}

          {/* ── 5-STEP TIMELINE ─────────────────────────────────────── */}
          <section className="timeline-section">
            <div className="timeline-header">
              <span className="timeline-tag">CHRONOLOGICAL TIMELINE</span>
              <h3>Past → Live Current → TCN Future Forecast</h3>
            </div>

            <div className="timeline-grid">
              {(data.timeline || []).map((step, idx) => {
                const isLive = step.type === "LIVE";
                const isTcn = step.type === "TCN_PREDICTION";
                const stepStyle = getAqiColor(step.aqi);

                return (
                  <div
                    key={idx}
                    className={`timeline-step-card ${isLive ? "is-live" : isTcn ? "is-tcn" : ""}`}
                  >
                    <div className="step-top-status">
                      <span className="step-status-tag">{step.status}</span>
                      {isLive && <span className="live-dot-pulse"></span>}
                    </div>

                    <div className="step-score" style={{ color: stepStyle.bg }}>
                      {Math.round(step.aqi)}
                    </div>

                    <div className="step-category-pill" style={{ backgroundColor: stepStyle.bg, color: "#fff" }}>
                      {stepStyle.label}
                    </div>

                    <span className="step-date-label">{step.label}</span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── 3. Main Hero AQI Banner ────────────────────────────── */}
          <section className="aqi-hero-banner" style={{ borderColor: aqiStyle.border }}>
            <div className="hero-top-info">
              <div>
                <h1 className="hero-city-title">Air Quality in {data.city}</h1>
                <p className="hero-station-name">Station Location: <strong>{data.station_name}</strong> • Source: <strong>{data.source.toUpperCase()} API</strong></p>
              </div>

              <div className="hero-status-tag" style={{ backgroundColor: aqiStyle.bg }}>
                {aqiStyle.label}
              </div>
            </div>

            <div className="hero-main-grid">
              {/* Big AQI Score Display */}
              <div className="aqi-card-primary" style={{ background: aqiStyle.light, borderColor: aqiStyle.bg }}>
                <div className="aqi-score-box" style={{ backgroundColor: aqiStyle.bg }}>
                  <span className="score-val">{Math.round(data.current.aqi)}</span>
                  <span className="score-unit">AQI (US EPA)</span>
                </div>

                <div className="aqi-details-box">
                  <div className="detail-line">
                    <span>Air Risk Status:</span>
                    <strong style={{ color: aqiStyle.bg }}>{aqiStyle.risk}</strong>
                  </div>
                  <div className="detail-line">
                    <span>Dominant Pollutant:</span>
                    <strong className="pollutant-highlight">{data.early_warning?.dominant_pollutant || "PM2.5"}</strong>
                  </div>
                  <p className="aqi-health-desc">"{aqiStyle.desc}"</p>
                </div>
              </div>

              {/* TCN PREDICTION BOX */}
              <div className="aqi-card-forecast">
                <div className="forecast-tag-header">
                  <span className="forecast-badge">TCN-HAA AI FORECAST ENGINE</span>
                  <span className="forecast-time">Tomorrow's Prediction</span>
                </div>

                {data.forecast ? (
                  <div className="forecast-content">
                    <div className="forecast-flex">
                      <div>
                        <span className="forecast-big-val" style={{ color: forecastAqiStyle?.bg || "#10b981" }}>
                          {Math.round(data.forecast.predicted_aqi)}
                        </span>
                        <span className="forecast-sub">Tomorrow's Predicted AQI</span>
                      </div>
                      <div className="forecast-trend-pill" style={{ color: forecastAqiStyle?.bg, borderColor: forecastAqiStyle?.bg }}>
                        {data.forecast.trend} ({data.forecast.delta >= 0 ? `+${data.forecast.delta}` : data.forecast.delta})
                      </div>
                    </div>

                    <div className="explainability-box">
                      <span className="explain-title">🧠 TCN Prediction Factor Contributions:</span>
                      <div className="explain-bars">
                        {(data.forecast.feature_contributions || []).map((fc, i) => (
                          <div key={i} className="explain-row">
                            <div className="explain-label-row">
                              <span>{fc.feature}</span>
                              <strong>{fc.percentage}%</strong>
                            </div>
                            <div className="explain-track">
                              <div
                                className="explain-fill"
                                style={{ width: `${fc.percentage}%`, backgroundColor: fc.color }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="no-forecast">Sequence records updating...</p>
                )}
              </div>
            </div>

            {/* EPA 6-Band Scale */}
            <div className="aqi-scale-bar-wrapper">
              <span className="scale-title">US EPA Air Quality Index Scale:</span>
              <div className="aqi-scale-bar">
                <div className="scale-segment" style={{ backgroundColor: "#10b981" }}>
                  <span>0 - 50</span>
                  <strong>Good</strong>
                </div>
                <div className="scale-segment" style={{ backgroundColor: "#f59e0b" }}>
                  <span>51 - 100</span>
                  <strong>Moderate</strong>
                </div>
                <div className="scale-segment" style={{ backgroundColor: "#f97316" }}>
                  <span>101 - 150</span>
                  <strong>Unhealthy for Sensitive</strong>
                </div>
                <div className="scale-segment" style={{ backgroundColor: "#ef4444" }}>
                  <span>151 - 200</span>
                  <strong>Unhealthy</strong>
                </div>
                <div className="scale-segment" style={{ backgroundColor: "#a855f7" }}>
                  <span>201 - 300</span>
                  <strong>Very Unhealthy</strong>
                </div>
                <div className="scale-segment" style={{ backgroundColor: "#e11d48" }}>
                  <span>301+</span>
                  <strong>Hazardous</strong>
                </div>
              </div>
            </div>
          </section>

          {/* ══════════════════════════════════════════════════════════════
              SPECIFIC DISEASE PRONE VULNERABILITY ASSESSMENT
              ══════════════════════════════════════════════════════════════ */}
          <section className="disease-section">
            <div className="disease-header">
              <h2>🫀 Disease-Specific AQI Vulnerability & Prone Assessment</h2>
              <p>Clinically grounded exposure risk evaluation assessing whether current air quality in {data.city} makes individuals prone to <strong>Asthma</strong>, <strong>Bronchitis</strong>, <strong>Ischemic Heart Disease (IHD)*</strong>, and <strong>COPD</strong>.</p>
            </div>

            {/* Highest Vulnerability Banner */}
            <div className="disease-highest-banner">
              <div className="dh-left">
                <span className="dh-icon">⚠️</span>
                <div>
                  <strong>Primary Pathological Vulnerability: {diseaseData.highest_risk_disease}</strong>
                  <span>Current atmospheric conditions in {data.city} impose highest clinical strain on this condition.</span>
                </div>
              </div>
              <span className="dh-badge">
                Vulnerability Score: {diseaseData.highest_risk_score}% ({diseaseData.highest_risk_status})
              </span>
            </div>

            {/* 4 Disease Cards Grid / Tabs */}
            <div className="disease-grid-tabs">
              {[
                { key: "asthma", name: "Asthma", icon: "🫁", sub: "Airway Hyperresponsiveness" },
                { key: "bronchitis", name: "Bronchitis", icon: "💨", sub: "Mucosal Inflammation" },
                { key: "ihd", name: "Ischemic Heart Disease (IHD)*", icon: "❤️", sub: "Cardiovascular / Plaque Risk" },
                { key: "copd", name: "COPD", icon: "🫁", sub: "Chronic Airflow Limitation" },
              ].map((item) => {
                const info = diseaseData?.diseases?.[item.key] || {};
                const isSelected = selectedDiseaseTab === item.key;
                return (
                  <div
                    key={item.key}
                    className={`disease-tab-card ${isSelected ? "selected" : ""}`}
                    style={isSelected ? { borderColor: info.color || "#06b6d4" } : {}}
                    onClick={() => setSelectedDiseaseTab(item.key)}
                  >
                    <div className="dt-top-row">
                      <span className="dt-icon">{item.icon}</span>
                      <span className="dt-badge" style={{ backgroundColor: info.color || "#f59e0b" }}>
                        {info.badge || "Evaluating"}
                      </span>
                    </div>

                    <div className="dt-name">{item.name}</div>
                    <span className="dt-sub">{item.sub}</span>

                    <div className="dt-score-row">
                      <span className="dt-score-label">Prone Vulnerability:</span>
                      <span className="dt-score-val" style={{ color: info.color || "#f59e0b" }}>
                        {info.prone_score}%
                      </span>
                    </div>

                    <div className="dt-meter-track">
                      <div
                        className="dt-meter-fill"
                        style={{ width: `${info.prone_score || 50}%`, backgroundColor: info.color || "#f59e0b" }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Detailed Medical Diagnostics Panel for Selected Disease */}
            {currentDiseaseInfo && (
              <div className="disease-detail-panel" style={{ borderColor: currentDiseaseInfo.color }}>
                <div className="detail-panel-header">
                  <div className="dp-title-group">
                    <div className="dp-icon">{currentDiseaseInfo.icon}</div>
                    <div>
                      <h3>{currentDiseaseInfo.full_name}</h3>
                      <p>Clinical evaluation for {data.city} based on live multi-pollutant concentrations</p>
                    </div>
                  </div>

                  <div className="dp-status-group">
                    <span className="dp-status-badge" style={{ backgroundColor: currentDiseaseInfo.color }}>
                      {currentDiseaseInfo.badge}
                    </span>
                    <div className="dp-score-circle" style={{ borderColor: currentDiseaseInfo.color, color: currentDiseaseInfo.color }}>
                      <span className="dp-score-num">{currentDiseaseInfo.prone_score}%</span>
                      <span className="dp-score-lbl">Risk Index</span>
                    </div>
                  </div>
                </div>

                <div className="disease-diag-grid">
                  {/* Physiological Mechanism */}
                  <div className="diag-card">
                    <div className="diag-card-title">
                      <span>🔬 Pathophysiological Trigger Mechanism</span>
                    </div>
                    <p className="diag-mechanism-text">{currentDiseaseInfo.physiological_mechanism}</p>

                    <div className="diag-triggers-row">
                      <span className="trigger-label">Active Trigger Pollutants:</span>
                      {(currentDiseaseInfo.key_triggers || []).map((trig, idx) => (
                        <span key={idx} className="trigger-chip">{trig}</span>
                      ))}
                    </div>
                  </div>

                  {/* Clinical Actions & Preventive Guidance */}
                  <div className="diag-card">
                    <div className="diag-card-title">
                      <span>💡 Clinical Action & Preventive Protocol</span>
                    </div>
                    <ul className="diag-guidance-list">
                      {(currentDiseaseInfo.clinical_guidance || []).map((step, idx) => (
                        <li key={idx}>{step}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Emergency Alert Strip */}
                <div className="disease-alert-strip">
                  <span className="alert-icon-sym">⚡</span>
                  <strong>Clinical Advisory:</strong> {currentDiseaseInfo.alert_summary}
                </div>
              </div>
            )}
          </section>


          {/* ── PERSONALIZED EXPOSURE RISK SIMULATOR ─────────────────── */}
          <section className="simulator-section">
            <div className="simulator-header">
              <h2>Personalized Exposure Risk Simulator</h2>
              <p>Simulate your individual physiological pollution dose based on your specific disease profile, planned activity, and exposure duration.</p>
            </div>

            <div className="simulator-container">
              {/* Interactive Control Controls */}
              <div className="sim-controls-card">
                <h3>Simulation Inputs</h3>

                {/* 1. Profile Select with Specific Diseases */}
                <div className="sim-form-group">
                  <label>1. Health & Disease Vulnerability Profile:</label>
                  <div className="sim-chips-grid">
                    {[
                      { key: "asthma", label: "Asthma (Airway Hyperresponsiveness)", icon: "🫁" },
                      { key: "bronchitis", label: "Bronchitis (Airway Mucosal Inflammation)", icon: "💨" },
                      { key: "ihd", label: "Ischemic Heart Disease (IHD)* (Cardiovascular)", icon: "❤️" },
                      { key: "copd", label: "COPD (Chronic Airflow Limitation)", icon: "🫁" },
                      { key: "general", label: "General Population (Baseline)", icon: "👤" },
                    ].map((p) => (
                      <button
                        key={p.key}
                        className={`sim-chip ${simProfile === p.key ? "selected" : ""}`}
                        onClick={() => handleSimChange(p.key, simActivity, simDuration)}
                      >
                        <span>{p.icon}</span>
                        <span>{p.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 2. Activity Select */}
                <div className="sim-form-group">
                  <label>2. Planned Physical Activity:</label>
                  <div className="sim-chips-grid">
                    {[
                      { key: "walking", label: "Walking (1.2x)", icon: "🚶" },
                      { key: "running", label: "Running / Cardio (3.5x)", icon: "🏃" },
                      { key: "cycling", label: "Cycling (2.8x)", icon: "🚴" },
                      { key: "outdoor_work", label: "Outdoor Work (2.2x)", icon: "🔨" },
                      { key: "travelling", label: "Travelling (1.0x)", icon: "🚗" },
                    ].map((a) => (
                      <button
                        key={a.key}
                        className={`sim-chip ${simActivity === a.key ? "selected" : ""}`}
                        onClick={() => handleSimChange(simProfile, a.key, simDuration)}
                      >
                        <span>{a.icon}</span>
                        <span>{a.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 3. Duration Select */}
                <div className="sim-form-group">
                  <label>3. Exposure Duration:</label>
                  <div className="sim-duration-chips">
                    {[
                      { val: 15, label: "15 min" },
                      { val: 30, label: "30 min" },
                      { val: 60, label: "1 Hour" },
                      { val: 120, label: "2 Hours" },
                      { val: 240, label: "4 Hours" },
                    ].map((d) => (
                      <button
                        key={d.val}
                        className={`dur-chip ${simDuration === d.val ? "selected" : ""}`}
                        onClick={() => handleSimChange(simProfile, simActivity, d.val)}
                      >
                        {d.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Simulation Result Output Card */}
              {simLoading ? (
                <div className="sim-result-loading">
                  <div className="aqi-spinner"></div>
                  <p>Calculating physiological dose for {selectedCity}...</p>
                </div>
              ) : simResult ? (
                <div className="sim-result-card" style={{ borderColor: simResult.color }}>
                  <div className="sim-result-header">
                    <div>
                      <span className="sim-level-badge" style={{ backgroundColor: simResult.color }}>
                        {simResult.level_icon} {simResult.exposure_level}
                      </span>
                      <h4 className="sim-city-title">Simulation Output for {simResult.city} (AQI {roundVal(simResult.current_aqi)})</h4>
                    </div>

                    <div className="sim-score-circle" style={{ borderColor: simResult.color, color: simResult.color }}>
                      <span className="sim-score-num">{simResult.risk_score}</span>
                      <span className="sim-score-sub">Risk Score</span>
                    </div>
                  </div>

                  <div className="sim-metrics-row">
                    <div className="sim-metric-box">
                      <span>Outdoor Advisability:</span>
                      <strong style={{ color: simResult.color }}>{simResult.advisable_status}</strong>
                    </div>
                    <div className="sim-metric-box">
                      <span>Max Safe Outdoor Time:</span>
                      <strong>{simResult.max_recommended_duration}</strong>
                    </div>
                    <div className="sim-metric-box">
                      <span>Dominant Risk Culprit:</span>
                      <strong className="pollutant-highlight">{simResult.dominant_pollutant}</strong>
                    </div>
                  </div>

                  {/* Why Rationale List */}
                  <div className="sim-why-box">
                    <strong>Why this assessment?</strong>
                    <ul>
                      {(simResult.why_factors || []).map((factor, idx) => (
                        <li key={idx}>
                          <span className="why-bullet">•</span>
                          <span>{factor}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Clinical Recommendation */}
                  <div className="sim-recommendation-box" style={{ borderColor: simResult.color }}>
                    <strong>💡 Clinical Recommendation:</strong>
                    <p>{simResult.recommendation}</p>
                  </div>
                </div>
              ) : null}
            </div>
          </section>

          {/* ── 4. Major Pollutants Breakdown Grid ─────────────────── */}
          <section className="aqi-section">
            <div className="aqi-section-title">
              <h2>Major Pollutants Concentration in {data.city}</h2>
              <p>Real-time pollutant breakdown measured against WHO & CPCB ambient air safety guidelines</p>
            </div>

            <div className="pollutants-card-grid">
              {Object.entries(POLLUTANT_META).map(([key, meta]) => {
                const val = data.current.pollutants[key];
                const ratio = val ? val / meta.limit : 0;
                const statusColor = ratio <= 0.5 ? "#10b981" : ratio <= 1.0 ? "#f59e0b" : "#ef4444";

                return (
                  <div key={key} className="pollutant-box">
                    <div className="pollutant-header">
                      <div>
                        <span className="pollutant-code">{meta.name}</span>
                        <span className="pollutant-full">{meta.label}</span>
                      </div>
                      <span className="pollutant-limit">Safe Limit: {meta.limit} {meta.unit}</span>
                    </div>

                    <div className="pollutant-reading">
                      <span className="reading-val">{val !== null && val !== undefined ? val : "N/A"}</span>
                      <span className="reading-unit">{val !== null ? meta.unit : ""}</span>
                    </div>

                    <div className="pollutant-progress-track">
                      <div
                        className="pollutant-progress-fill"
                        style={{ width: `${Math.min(100, ratio * 100)}%`, backgroundColor: statusColor }}
                      ></div>
                    </div>

                    <div className="pollutant-footer">
                      <span className="pollutant-desc">{meta.desc}</span>
                      <span className="pollutant-status-pill" style={{ color: statusColor, borderColor: statusColor }}>
                        {ratio <= 0.5 ? "Good" : ratio <= 1.0 ? "Moderate" : "Exceeded"}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ── 5. Monitored Cities Ranking Table ─────────────────────── */}
          <section className="aqi-section">
            <div className="aqi-section-title">
              <h2>Monitored Indian Cities AQI Ranking</h2>
              <p>Live national ranking of monitored cities ordered from cleanest to most polluted</p>
            </div>

            <div className="ranking-table-container">
              <table className="aqi-ranking-table">
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>City</th>
                    <th>Live AQI</th>
                    <th>Air Quality Category</th>
                    <th>Health Risk level</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {ranking.map((row) => {
                    const rowStyle = getAqiColor(row.aqi);
                    const isSelected = selectedCity.toLowerCase() === row.city.toLowerCase();
                    return (
                      <tr
                        key={row.rank}
                        className={isSelected ? "active-city-row" : ""}
                        onClick={() => setSelectedCity(row.city)}
                      >
                        <td><span className={`rank-badge r-${row.rank}`}>#{row.rank}</span></td>
                        <td>
                          <div className="city-cell-content">
                            <strong>{row.city}</strong>
                            {isSelected && <span className="active-tag">Active</span>}
                          </div>
                        </td>
                        <td>
                          <span className="aqi-table-score" style={{ color: rowStyle.bg }}>
                            {Math.round(row.aqi)}
                          </span>
                        </td>
                        <td>
                          <span className="aqi-table-cat" style={{ backgroundColor: rowStyle.bg, color: "#fff" }}>
                            {row.category}
                          </span>
                        </td>
                        <td>{row.health_risk}</td>
                        <td>
                          <button className="view-city-link">View Station →</button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>
        </main>
      ) : null}

      {/* ── 6. Footer ─────────────────────────────────────────────── */}
      <footer className="aqi-footer">
        <div className="footer-inner-container">
          <div className="footer-top-row">
            <div className="footer-brand">
              <span className="f-logo">🍃 AeroRisk LIVE</span>
              <p>India's Real-Time Air Quality Monitoring, TCN-HAA Forecast & Disease-Specific Exposure Protection Engine</p>
            </div>
            <div className="footer-citations">
              <span>Data Sources: Open-Meteo Air Quality, CPCB Ground Stations, EPA Standards</span>
            </div>
          </div>
          <div className="footer-bottom-row">
            <p>© 2026 AeroRisk System. All real-time AQI observation metrics, predictive neural outputs, and disease vulnerability evaluations are updated hourly.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function roundVal(val) {
  return Math.round(val || 0);
}
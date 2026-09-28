"""
personalized_health_service.py
------------------------------
Generates clinically grounded disease vulnerability and health risk assessments
specifically evaluating whether ambient AQI and multi-pollutant exposure make individuals
prone to:
1. Asthma (Airway Hyperresponsiveness & Bronchoconstriction)
2. Bronchitis (Bronchial Mucosa Inflammation & Hypersecretion)
3. Ischemic Heart Disease (IHD)* (Myocardial Oxygen Debt & Plaque Rupture)
4. COPD (Chronic Obstructive Pulmonary Disease & Alveolar Exacerbation)

Criteria:
- Based on World Health Organization (WHO) and Central Pollution Control Board (CPCB)
  National Ambient Air Quality Standards (NAAQS):
  * PM2.5 24-hr safe limit: 60 µg/m³ (WHO guideline: 15 µg/m³)
  * PM10 24-hr safe limit: 100 µg/m³ (WHO guideline: 45 µg/m³)
  * NO2 24-hr safe limit: 80 µg/m³
  * SO2 24-hr safe limit: 80 µg/m³
  * CO 8-hr safe limit: 2.0 - 4.0 ppm
  * O3 8-hr safe limit: 100 µg/m³
- Normalized tiered scaling aligns with standard AQI bands (Good, Moderate, Unhealthy for Sensitive,
  Unhealthy, Very Unhealthy, Hazardous) instead of uncalibrated raw summations.
"""

from typing import Any


def _calculate_base_vulnerability(aqi: float) -> float:
    """
    Computes baseline physiological vulnerability percentage [0 - 100%]
    aligned with US EPA / CPCB AQI bands:
    - 0 to 50 (Good): 5% to 20%
    - 51 to 100 (Moderate): 20% to 45%
    - 101 to 150 (Unhealthy for Sensitive): 45% to 68%
    - 151 to 200 (Unhealthy): 68% to 82%
    - 201 to 300 (Very Unhealthy): 82% to 92%
    - 301+ (Hazardous): 92% to 100%
    """
    if aqi <= 50:
        return max(5.0, (aqi / 50.0) * 20.0)
    elif aqi <= 100:
        return 20.0 + ((aqi - 50.0) / 50.0) * 25.0
    elif aqi <= 150:
        return 45.0 + ((aqi - 100.0) / 50.0) * 23.0
    elif aqi <= 200:
        return 68.0 + ((aqi - 150.0) / 50.0) * 14.0
    elif aqi <= 300:
        return 82.0 + ((aqi - 200.0) / 100.0) * 10.0
    else:
        return min(100.0, 92.0 + ((aqi - 300.0) / 200.0) * 8.0)


def _categorize_vulnerability(score: float):
    """
    Standardized clinical vulnerability categorization.
    """
    if score <= 25.0:
        return {
            "status": "Low Vulnerability",
            "badge": "Low Prone Risk",
            "color": "#10b981",
        }
    elif score <= 50.0:
        return {
            "status": "Moderate Vulnerability",
            "badge": "Moderately Prone",
            "color": "#f59e0b",
        }
    elif score <= 75.0:
        return {
            "status": "Elevated Vulnerability",
            "badge": "Highly Prone",
            "color": "#f97316",
        }
    else:
        return {
            "status": "Critical Hazard",
            "badge": "Extremely Prone",
            "color": "#ef4444",
        }


def get_disease_prone_assessment(aqi: float, pollutants: dict[str, float | None]) -> dict[str, Any]:
    """
    Evaluates susceptibility and specific disease vulnerability against current AQI
    and specific pollutant levels (PM2.5, PM10, NO2, SO2, CO, O3) using calibrated NAAQS ratios.
    """
    pm25 = float(pollutants.get("pm25") or 0.0)
    pm10 = float(pollutants.get("pm10") or 0.0)
    no2 = float(pollutants.get("no2") or 0.0)
    so2 = float(pollutants.get("so2") or 0.0)
    co = float(pollutants.get("co") or 0.0)
    o3 = float(pollutants.get("o3") or 0.0)

    # Base AQI severity band
    if aqi <= 50:
        overall_category = "Good"
        overall_color = "#10b981"
        overall_risk = "Low Risk"
    elif aqi <= 100:
        overall_category = "Moderate"
        overall_color = "#f59e0b"
        overall_risk = "Moderate Risk"
    elif aqi <= 150:
        overall_category = "Unhealthy for Sensitive Groups"
        overall_color = "#f97316"
        overall_risk = "Elevated Risk"
    elif aqi <= 200:
        overall_category = "Unhealthy"
        overall_color = "#ef4444"
        overall_risk = "High Risk"
    elif aqi <= 300:
        overall_category = "Very Unhealthy"
        overall_color = "#8b5cf6"
        overall_risk = "Very High Risk"
    else:
        overall_category = "Hazardous"
        overall_color = "#881337"
        overall_risk = "Severe Emergency Risk"

    base_vuln = _calculate_base_vulnerability(aqi)

    # NAAQS Pollutant Ratios (against 24-hr safe limits)
    pm25_ratio = pm25 / 60.0
    pm10_ratio = pm10 / 100.0
    o3_ratio = o3 / 100.0
    no2_ratio = no2 / 80.0
    so2_ratio = so2 / 80.0
    co_ratio = co / 2.0

    diseases = {}

    # =========================================================================
    # 1. ASTHMA (Bronchial Hyperresponsiveness & Acute Bronchospasm)
    # =========================================================================
    # Primary triggers: Fine PM2.5 (deep alveolar), O3 (bronchoconstrictor), NO2
    asthma_multiplier = 0.8 + 0.25 * max(pm25_ratio, o3_ratio)
    asthma_score = round(min(100.0, max(5.0, base_vuln * asthma_multiplier)), 1)
    ast_meta = _categorize_vulnerability(asthma_score)

    asthma_triggers = []
    if o3_ratio > 0.8:
        asthma_triggers.append(f"O₃ ({round(o3, 1)} µg/m³ - Ozone Irritation)")
    if pm25_ratio > 0.6:
        asthma_triggers.append(f"PM2.5 ({round(pm25, 1)} µg/m³ - Fine Particulates)")
    if no2_ratio > 0.6:
        asthma_triggers.append(f"NO₂ ({round(no2, 1)} µg/m³ - Traffic Gas)")
    if not asthma_triggers:
        asthma_triggers.append("Ambient Particulates (Within Benign Limits)")

    if asthma_score <= 25.0:
        asthma_mechanism = (
            "Atmospheric particulate concentrations remain within safe physiological limits. "
            "Minimal bronchial smooth muscle stimulation and normal airway patency."
        )
        asthma_guidance = [
            "Safe for regular outdoor jogging, sports, and cardiovascular training.",
            "Continue standard prescribed maintenance or controller inhaler routine.",
        ]
        asthma_alert = "Air quality poses minimal bronchospasm threat."
    elif asthma_score <= 50.0:
        asthma_mechanism = (
            "Mild airway surface irritation caused by ambient fine particles and ozone. "
            "Sensitive individuals may experience throat scratchiness or mild cough upon exertion."
        )
        asthma_guidance = [
            "Keep quick-relief rescue inhaler (e.g., Albuterol/Salbutamol) readily available.",
            "Avoid intense outdoor cardio sessions during peak midday traffic hours.",
            "Rinse mouth and stay hydrated after returning from outdoors.",
        ]
        asthma_alert = "Mild airway irritation possible during extended outdoor exertion."
    elif asthma_score <= 75.0:
        asthma_mechanism = (
            "Elevated oxidant gases (O₃/PM2.5) penetrate deep into the terminal bronchioles, "
            "triggering neurogenic inflammation, mucus plugging, and acute smooth muscle bronchospasm."
        )
        asthma_guidance = [
            "Shift cardiovascular workouts indoors into air-conditioned, HEPA-filtered rooms.",
            "Pre-medicate with prescribed bronchodilator prior to mandatory outdoor commutes.",
            "Wear a certified N95/FFP2 respirator mask tightly fitted over nose and mouth outdoors.",
            "Monitor peak expiratory flow rate (PEFR); initiate asthma action plan if readings fall below 80%.",
        ]
        asthma_alert = "Elevated risk of wheezing, chest tightness, and sudden asthmatic episodes."
    else:
        asthma_mechanism = (
            "Severe particulate pollution overwhelms mucociliary clearance and induces severe diffuse "
            "bronchospasm, profound ventilation-perfusion mismatch, and hypoxemia in asthmatic individuals."
        )
        asthma_guidance = [
            "Strictly stay indoors; seal windows and doors, and run HEPA air filtration continuously.",
            "N95/KN95 respirator mask mandatory for any brief step outdoors.",
            "Have emergency nebulization and rescue medication on standby.",
            "Seek emergency medical evaluation immediately if rescue inhaler fails to relieve dyspnea within 15 minutes.",
        ]
        asthma_alert = "Critical emergency threat: High likelihood of severe, life-threatening asthma attacks."

    diseases["asthma"] = {
        "disease_name": "Asthma",
        "full_name": "Bronchial Asthma & Hyperresponsiveness",
        "icon": "🫁",
        "prone_score": asthma_score,
        "prone_status": ast_meta["status"],
        "badge": ast_meta["badge"],
        "color": ast_meta["color"],
        "physiological_mechanism": asthma_mechanism,
        "key_triggers": asthma_triggers,
        "clinical_guidance": asthma_guidance,
        "alert_summary": asthma_alert,
    }

    # =========================================================================
    # 2. BRONCHITIS (Bronchial Mucosa Inflammation & Hypersecretion)
    # =========================================================================
    # Primary triggers: Coarse PM10 (deposits in conducting airways), SO2 & NO2 (acidic mucosal irritants)
    bronch_ratio = max(pm10_ratio, so2_ratio, no2_ratio)
    bronchitis_multiplier = 0.65 + 0.35 * bronch_ratio
    bronchitis_score = round(min(100.0, max(5.0, base_vuln * bronchitis_multiplier)), 1)
    br_meta = _categorize_vulnerability(bronchitis_score)

    bronch_triggers = []
    if pm10_ratio > 0.6:
        bronch_triggers.append(f"PM10 ({round(pm10, 1)} µg/m³ - Coarse Dust)")
    if so2_ratio > 0.5:
        bronch_triggers.append(f"SO₂ ({round(so2, 1)} µg/m³ - Acidic Gas)")
    if no2_ratio > 0.5:
        bronch_triggers.append(f"NO₂ ({round(no2, 1)} µg/m³ - Combustion Gas)")
    if not bronch_triggers:
        bronch_triggers.append("Conducting Airway Irritants (Within Normal Range)")

    if bronchitis_score <= 25.0:
        bronchitis_mechanism = (
            "Bronchial ciliated epithelium operates with healthy mucociliary clearance. "
            "No mucosal edema or hypersecretion detected."
        )
        bronchitis_guidance = [
            "Normal respiratory endurance; outdoor walking and activities are completely safe.",
            "Maintain general lung health and adequate daily hydration.",
        ]
        bronchitis_alert = "Minimal risk of bronchial inflammation or persistent cough."
    elif bronchitis_score <= 50.0:
        bronchitis_mechanism = (
            "Inhaled coarse particulates (PM10) and trace combustion gases deposit along the trachea "
            "and primary bronchi, causing mild mucosal hyperemia and reflexive cough."
        )
        bronchitis_guidance = [
            "Individuals with chronic bronchitis should avoid dusty roads and construction zones.",
            "Stay well-hydrated to keep bronchial secretions thin and easily cleared.",
            "Consider evening saline steam inhalation to soothe irritated tracheal passages.",
        ]
        bronchitis_alert = "Mild throat irritation, throat clearing, and dry cough may manifest."
    elif bronchitis_score <= 75.0:
        bronchitis_mechanism = (
            "SO2 and NO2 react with moisture on bronchial mucosa forming sulfurous and nitrous acids. "
            "This causes goblet cell hyperplasia, thick viscous phlegm production, epithelial shedding, "
            "and frequent paroxysmal coughing fits."
        )
        bronchitis_guidance = [
            "Avoid exposure to cold outdoor air and vehicular exhaust which trigger sudden cough spasms.",
            "Wear a particulate-filtering mask (N95) outdoors to trap coarse and fine irritants.",
            "Use expectorants or warm hydration if productive sputum develops.",
            "Consult physician if sputum becomes purulent (yellow/green) or if low-grade fever accompanies cough.",
        ]
        bronchitis_alert = "High probability of bronchial mucosal swelling, heavy phlegm, and persistent coughing."
    else:
        bronchitis_mechanism = (
            "Extensive chemical denudation of the bronchial protective lining. Loss of ciliary motility "
            "traps pollutants in bronchial lobes, inducing secondary bacterial colonization risk and severe "
            "tracheobronchitis."
        )
        bronchitis_guidance = [
            "Strict home isolation in purified indoor air until ambient pollution subsides.",
            "Avoid all chemical fumes, incense, and tobacco smoke in the domestic environment.",
            "Administer prescribed anti-inflammatory inhalers and mucolytics as directed by pulmonologist.",
            "Seek hospital care if coughing causes severe pleuritic chest pain or hemoptysis (blood in sputum).",
        ]
        bronchitis_alert = "Severe acute tracheobronchitis risk: Damaging bronchial inflammation with relentless coughing."

    diseases["bronchitis"] = {
        "disease_name": "Bronchitis",
        "full_name": "Acute & Chronic Bronchitis (Airway Mucosal Inflammation)",
        "icon": "💨",
        "prone_score": bronchitis_score,
        "prone_status": br_meta["status"],
        "badge": br_meta["badge"],
        "color": br_meta["color"],
        "physiological_mechanism": bronchitis_mechanism,
        "key_triggers": bronch_triggers,
        "clinical_guidance": bronchitis_guidance,
        "alert_summary": bronchitis_alert,
    }

    # =========================================================================
    # 3. ISCHEMIC HEART DISEASE (IHD)* (Coronary Plaque & Myocardial Oxygen Debt)
    # =========================================================================
    # Primary triggers: Ultrafine PM2.5 (bloodstream translocation) & Carbon Monoxide (CO - carboxyhemoglobin)
    ihd_ratio = max(pm25_ratio, co_ratio)
    ihd_multiplier = 0.65 + 0.35 * ihd_ratio
    ihd_score = round(min(100.0, max(5.0, base_vuln * ihd_multiplier)), 1)
    ihd_meta = _categorize_vulnerability(ihd_score)

    ihd_triggers = []
    if pm25_ratio > 0.6:
        ihd_triggers.append(f"PM2.5 ({round(pm25, 1)} µg/m³ - Microvascular Infiltration)")
    if co_ratio > 0.5:
        ihd_triggers.append(f"CO ({round(co, 2)} ppm - Carboxyhemoglobin Induction)")
    if not ihd_triggers:
        ihd_triggers.append("Cardiovascular Pollutants (Within Normal Range)")

    if ihd_score <= 25.0:
        ihd_mechanism = (
            "Vascular endothelium is uncompromised by particulate translocation. "
            "Normal systemic arterial elasticity, microvascular tone, and cardiac oxygen delivery."
        )
        ihd_guidance = [
            "Cardiovascular exercise and daily brisk walking are strongly encouraged.",
            "Maintain routine heart-healthy diet and blood pressure management.",
        ]
        ihd_alert = "Low ambient cardiovascular stress; heart workload remains normal."
    elif ihd_score <= 50.0:
        ihd_mechanism = (
            "Mild systemic oxidative stress. Sub-micron PM2.5 enters capillary circulation, "
            "causing subtle autonomic nervous system imbalances and slight elevation in peripheral arterial resistance."
        )
        ihd_guidance = [
            "Patients with pre-existing coronary artery disease (CAD) should take prescribed antiplatelet/statin medications.",
            "Avoid strenuous morning walks in congested intersections or foggy weather.",
            "Check resting blood pressure and heart rate periodically.",
        ]
        ihd_alert = "Moderate vascular stress: Patients with known angina should pace physical exertion."
    elif ihd_score <= 75.0:
        ihd_mechanism = (
            "Inhaled PM2.5 stimulates pulmonary cytokine release (IL-6, TNF-alpha) causing systemic vascular "
            "endothelial inflammation. CO binds hemoglobin to form carboxyhemoglobin, directly decreasing oxygen "
            "supply to myocardium. Together they promote platelet aggregation, coronary vasoconstriction, and plaque instability."
        )
        ihd_guidance = [
            "Strictly avoid heavy outdoor manual exertion, uphill cycling, or fast running.",
            "Carry emergency sublingual Nitroglycerin if diagnosed with ischemic angina.",
            "Monitor for cardiac warning signs: chest tightness, pressure radiating to jaw/left arm, or unexplained diaphoresis.",
            "Stay indoors in a climate-controlled room; avoid sudden temperature changes.",
        ]
        ihd_alert = "Significant risk of acute myocardial ischemia, angina pectoris, and cardiac arrhythmias."
    else:
        ihd_mechanism = (
            "Severe blood hypercoagulability, acute endothelial dysfunction, and coronary vasospasm. "
            "Massive systemic inflammatory surge triggers rupture of vulnerable coronary atherosclerotic plaques, "
            "precipitating acute myocardial infarction (heart attack) and lethal ventricular dysrhythmias."
        )
        ihd_guidance = [
            "Absolute restriction of outdoor physical activities for all cardiac and hypertensive patients.",
            "Remain in a sealed, HEPA air-purified environment with relaxed physical resting state.",
            "Keep emergency cardiology and ambulance helpline numbers on immediate speed dial.",
            "CALL 108 / EMERGENCY HOSPITAL IMMEDIATELY upon any chest pressure, palpitations, or fainting.",
        ]
        ihd_alert = "Extreme cardiovascular emergency alert: High danger of acute myocardial infarction."

    diseases["ihd"] = {
        "disease_name": "Ischemic Heart Disease (IHD)*",
        "full_name": "Ischemic Heart Disease (Coronary Artery Disease & Myocardial Infarction)",
        "icon": "❤️",
        "prone_score": ihd_score,
        "prone_status": ihd_meta["status"],
        "badge": ihd_meta["badge"],
        "color": ihd_meta["color"],
        "physiological_mechanism": ihd_mechanism,
        "key_triggers": ihd_triggers,
        "clinical_guidance": ihd_guidance,
        "alert_summary": ihd_alert,
    }

    # =========================================================================
    # 4. COPD (Chronic Obstructive Pulmonary Disease & Alveolar Exacerbation)
    # =========================================================================
    # Primary triggers: Alveolar deposition of PM2.5 & PM10, SO2, O3
    copd_ratio = (pm25_ratio * 0.55) + (pm10_ratio * 0.25) + (o3_ratio * 0.20)
    copd_multiplier = 0.70 + 0.30 * copd_ratio
    copd_score = round(min(100.0, max(5.0, base_vuln * copd_multiplier)), 1)
    copd_meta = _categorize_vulnerability(copd_score)

    copd_triggers = []
    if pm25_ratio > 0.6:
        copd_triggers.append(f"PM2.5 ({round(pm25, 1)} µg/m³ - Alveolar Infiltration)")
    if pm10_ratio > 0.6:
        copd_triggers.append(f"PM10 ({round(pm10, 1)} µg/m³ - Inhalables)")
    if o3_ratio > 0.7:
        copd_triggers.append(f"O₃ ({round(o3, 1)} µg/m³ - Oxidant Gas)")
    if not copd_triggers:
        copd_triggers.append("Alveolar Irritants (Within Normal Range)")

    if copd_score <= 25.0:
        copd_mechanism = (
            "Ambient air produces minimal supplemental alveolar strain. Basal lung compliance and gas exchange "
            "remain stable at baseline."
        )
        copd_guidance = [
            "Maintain routine daily pulmonary rehabilitation and breathing exercises.",
            "Regular maintenance inhalers as directed by chest specialist.",
        ]
        copd_alert = "Stable respiratory baseline; negligible risk of acute COPD flare-up."
    elif copd_score <= 50.0:
        copd_mechanism = (
            "Particulates cause minor macrophage activation in damaged peripheral bronchioles, "
            "increasing dyspnea on exertion and mild carbon dioxide retention."
        )
        copd_guidance = [
            "Limit outdoor activities to shaded, traffic-free areas.",
            "Ensure regular intake of prescribed long-acting bronchodilators (LABA/LAMA).",
            "Perform pursed-lip breathing to relieve shortness of breath during movement.",
        ]
        copd_alert = "Increased breathlessness during walking; manage activity pacing."
    elif copd_score <= 75.0:
        copd_mechanism = (
            "Severe neutrophilic airway inflammation, loss of alveolar elastic recoil, and air trapping. "
            "Pollutants cripple local antibacterial defense, often precipitating severe acute infectious "
            "exacerbations of COPD (AECOPD) with rapid decline in FEV1."
        )
        copd_guidance = [
            "Remain indoors; do not step outside without strict N95 respirator seal.",
            "Monitor oxygen saturation (SpO2) using a pulse oximeter twice daily; alert doctor if SpO2 drops below 90%.",
            "Have oral steroids and standby rescue inhalers readily available per COPD action plan.",
            "Run continuous indoor HEPA air filtration to prevent indoor particulate accumulation.",
        ]
        copd_alert = "High hazard of acute exacerbation, severe dyspnea, and respiratory compromise."
    else:
        copd_mechanism = (
            "Catastrophic small-airway closure, profound hypoxemia, alveolar hypoventilation, "
            "and hypercapnic respiratory failure requiring emergency non-invasive positive pressure "
            "ventilation (BiPAP) or mechanical support."
        )
        copd_guidance = [
            "Strict total confinement in hospital-grade HEPA purified room.",
            "Check oxygen concentrator / supplemental oxygen cylinders for full operational readiness.",
            "Continuous pulse oximetry monitoring.",
            "IMMEDIATELY CALL EMERGENCY MEDICAL SERVICES if resting respiratory rate > 25/min or lips show cyanosis.",
        ]
        copd_alert = "Critical respiratory failure hazard: Immediate hospital intervention may be necessary."

    diseases["copd"] = {
        "disease_name": "COPD",
        "full_name": "Chronic Obstructive Pulmonary Disease (Emphysema & Chronic Airflow Limitation)",
        "icon": "🫁",
        "prone_score": copd_score,
        "prone_status": copd_meta["status"],
        "badge": copd_meta["badge"],
        "color": copd_meta["color"],
        "physiological_mechanism": copd_mechanism,
        "key_triggers": copd_triggers,
        "clinical_guidance": copd_guidance,
        "alert_summary": copd_alert,
    }

    # Summary analysis
    highest_disease = max(diseases.values(), key=lambda d: d["prone_score"])

    return {
        "overall_category": overall_category,
        "overall_color": overall_color,
        "overall_risk": overall_risk,
        "highest_risk_disease": highest_disease["disease_name"],
        "highest_risk_score": highest_disease["prone_score"],
        "highest_risk_status": highest_disease["prone_status"],
        "diseases": diseases,
    }


def get_personalized_advisories(aqi: float, pollutants: dict[str, float | None]) -> dict[str, Any]:
    """
    Main entry point for health risk assessment.
    Returns calibrated disease prone evaluation for Asthma, Bronchitis, Ischemic Heart Disease (IHD)*, and COPD.
    """
    return get_disease_prone_assessment(aqi, pollutants)

# Research Charter and Project Scope: Quantifying Solar Curtailment & Storage Requirements in India

## 1. Executive Summary & Problem Statement

India has expanded its solar power capacity rapidly to meet ambitious renewable energy goals. However, spatial and temporal mismatches between peak solar generation (midday hours) and peak electricity demand (evening hours), combined with transmission grid congestion, result in significant **solar curtailment**.

This project quantifies state-level solar curtailment across India from **2015 to 2016**, isolates the primary grid and infrastructure drivers, and models optimal **Battery Energy Storage System (BESS)** and **Pumped Hydro Energy Storage System (PHESS)** storage capacities needed to absorb wasted energy and prevent economic loss.

---

## 2. Core & Secondary Research Questions

### Primary Research Question

- **How much solar energy is lost due to inadequate transmission and storage infrastructure across Indian states, and where should India prioritize future storage investments?**

### Supporting Research Questions

1. **State Rankings & Extent**: Which Indian states experience the highest absolute solar generation loss (MU/GWh) and highest Curtailment Ratio (%)?
2. **Temporal Trends**: Is curatailment worsening overtime as total solar penetration increases year-over-year?
3. **Storage Deficit Index (SDI)**: What is the required MWh battery storage capacity for top curtailment states to absorb midday generation suplusses?
4. **Scenario Planning**: What is the net financial benefit (PPA tariff savings) and carbon ofset (tCO2 avoied) under different BESS deployment scenarios?

## 3. Scope Boundaries & Boundary Conditions

### In-scope

- **Geographic Coverage**: All Indian States and Union Territories with commissioned utility-scale solar capacity.
- **Temporal Coverage**: Monthly-time series panel data spanning **FY 2015-16 to FY 2015-26**
- **Primary Analytics Stack**:
  - **Core Data Layer**: SQLite relational database
  - **Analytics & ML**: Pandas, SciPy, Scikit-learn
  - **Geospatial & Visualization**: GeoPandas (state choropleths), Matplotlib, Seaborn, Plotly
  - **Decision Support**: Interactive Streamlit dashboard with BESS what-if-scenario sliders.

### Out-of-Scope (Phase 1 baseline)

- **Real-time 15 minute dispath optimization across all 28 states** (restricted to phase 2 Advanced Research for select states like Rajasthan/Gujarat to prevent data fragmentation).
- **tbd**

## 5. Primary Deliverables & Output Artifacts

1. **`data/processes/energy_master.db`**: Unified, indexes SQLite database containing staging and production tables.
2. **`outputs/figures/`**: Publication ready spatial heatmaps, correlation matrices, and regression diagnostic plots
3. **`app/streamlit_app.py`**: Multi-page interactive policy dashboard featuring state profiles and interactive BESS expansion sliders.
4. **`docs/reports/final_executive_summary.md`**: Decision-support report framing findings as actionable infrastructure policy recommendations.

# Solar Curtailment Project

Data pipeline, feature engineering, and exploratory analysis of Indian state-level solar generation, installed solar capacity, monthly peak electricity demand, and weather/irradiance data (2015–2026)

## Pipeline Overview

1. **Data Collection & Integration (`1.Data-Collection-and-Basic-Processing-Notebook.ipynb`)**
   - Extracts monthly solar generation and yearly installed solar capacity from NITI Aayog ICeD endpoints.
   - Downloads and parses monthly CEA *Power Supply Position – Peak* PDF reports into structured peak demand/met records.
   - Pulls monthly solar irradiance (`ALLSKY_SFC_SW_DWN`) and temperature (`T2M`) data from the NASA POWER API.
   - Loads datasets into a SQLite database (`energy_master.db`) and joins them into `MASTER_DF.csv`.

2. **Feature Engineering (`2.Feature-Engineering-Notebook.ipynb`)**
   - Builds calendar features (`days_in_month`, `hours_in_month`, `is_monsoon`, `month_sin`, `month_cos`).
   - Computes physics/weather metrics (`pr_temp_adjusted`, `potential_generation_mu`) and utilization/curtailment proxies (`cuf_actual`, `curtailment_proxy_mu`, `curtailment_ratio`).
   - Adds grid-stress indicators (`solar_penetration_ratio`, `solar-surplus-risk`) and 3-month rolling metrics (`gen_roll3_mu`, `curtailment_roll3_mu`) saved to `MASTER_DF_FEATURE_ENGINEERED.csv`.

3. **Exploratory Data Analysis (`3.Exploratory-Data-Analysis-Notebook.ipynb`)**
   - Tracks generation, capacity, curtailment proxy/ratio, and peak demand trends across states and financial years.
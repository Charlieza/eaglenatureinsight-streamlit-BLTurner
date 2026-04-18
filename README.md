# EagleNatureInsight™ — BL Turner Group

Nature intelligence platform built for **BL Turner Group (Pty) Ltd**, tailored to their
organic waste-to-fertiliser and biogas operation at Portion 159 of New Guelderland,
KwaDukuza (iLembe District, KwaZulu-Natal). 100 tonnes/day nameplate anaerobic digestion
(AD) capacity, drawing feedstock from eThekwini Metropolitan Municipality, iLembe and
uMgungundlovu districts, with digestate fertiliser supplied to KZN farmlands.

Developed by **Space Eagle Enterprise (Pty) Ltd** for the TNFD / Conservation X Labs /
UNDP **Nature Intelligence for Business Grand Challenge** SME user-testing phase
(Jan – April 2026).

## Features

- TNFD **LEAP** (Locate, Evaluate, Assess, Prepare) workflow
- TNFD Core Global Disclosure Metrics dashboard
- Nature Positive Initiative (NPI) State of Nature indicators
- **Waste sourcing intelligence** tailored to BL Turner: site map of feedstock sources,
  frequency of collection, tonnage, seasonality, and continuity-of-supply risks
- Indicative monetary exposures in USD (revenue-at-risk, landfill diversion benefit)
- Satellite imagery for the main site (Sentinel-2, NDVI, land cover, flood, heat)
- Downloadable PDF report for funders, regulators, and off-takers

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Configure Earth Engine service-account credentials in `.streamlit/secrets.toml`
under the `[earthengine]` key.

## Login
Default pilot credentials (change in `.streamlit/secrets.toml` for production):
- Username: `admin-blturner`
- Password: `BLTurnerPilot2026!`

## Contact
Dr Charles Mpho Takalana · Space Eagle Enterprise (Pty) Ltd · charles@spaceeagle.space

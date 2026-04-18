# BL Turner Nature Intelligence Platform

Files:
- `bl_turner_platform.py` — Streamlit app for the BL Turner circular-economy platform.

## What it includes
- Login gate
- BL Turner-specific business framing
- TNFD-style dependency and impact sections
- Plain-language narrative outputs
- Map input via coordinates or drawn polygon
- Earth Engine metrics and historical charts
- Units of nature / units of money table
- Visual evidence panels

## Login
By default the app accepts:
- username: `admin`
- password: `spaceeagle-demo`

For production, add to Streamlit secrets:

```toml
[auth]
username = "your_username"
password = "your_password"
```

## Run
```bash
streamlit run bl_turner_platform.py
```

## Notes
- The current default coordinates are a KwaDukuza-area placeholder and should be replaced with the exact BL Turner site coordinates once confirmed.
- The app is built to use the existing Earth Engine helper functions already developed for the Panuka platform.

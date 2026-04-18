from __future__ import annotations

import io
import math
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
import matplotlib.pyplot as plt
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_WIDTH, PAGE_HEIGHT = A4

BRAND = {
    "primary": colors.HexColor("#163d63"),
    "accent": colors.HexColor("#1f8f5f"),
    "warn": colors.HexColor("#d9911a"),
    "danger": colors.HexColor("#c0392b"),
    "muted": colors.HexColor("#6b7280"),
    "bg": colors.HexColor("#f6f8fb"),
    "card": colors.white,
    "border": colors.HexColor("#e5e7eb"),
    "text": colors.HexColor("#111827"),
    "subtext": colors.HexColor("#4b5563"),
}

ABBREVIATIONS = {
    "AD": "Anaerobic Digestion",
    "CHP": "Combined Heat and Power",
    "CHIRPS": "Climate Hazards Group InfraRed Precipitation with Station data",
    "ET": "Evapotranspiration",
    "GHG": "Greenhouse gas",
    "IND1": "State of Nature Indicator 1: Ecosystem extent",
    "IND2": "State of Nature Indicator 2: Ecosystem condition",
    "IND3": "State of Nature Indicator 3: Landscape intactness",
    "IND4": "State of Nature Indicator 4: Species extinction risk",
    "LEAP": "Locate, Evaluate, Assess and Prepare",
    "LST": "Land surface temperature",
    "MODIS": "Moderate Resolution Imaging Spectroradiometer",
    "NDVI": "Normalized Difference Vegetation Index",
    "NPI": "Nature Positive Initiative",
    "PDSI": "Palmer Drought Severity Index",
    "SME": "Small and medium-sized enterprise",
    "SoN": "State of Nature",
    "TNFD": "Taskforce on Nature-related Financial Disclosures",
    "tpd": "tonnes per day",
    "tCO₂e": "tonnes of CO₂ equivalent",
    "KZN": "KwaZulu-Natal",
    "DC": "Distribution Centre",
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TitleBrand", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22, leading=26, textColor=BRAND["primary"], spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SubBrand", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=10, leading=14, textColor=BRAND["subtext"], spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="SectionBrand", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=14, leading=18, textColor=BRAND["primary"], spaceBefore=8, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="SmallBrand", parent=styles["Heading3"], fontName="Helvetica-Bold",
        fontSize=11, leading=14, textColor=BRAND["text"], spaceBefore=6, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BodyBrand", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=9.5, leading=13, textColor=BRAND["text"], spaceAfter=6, alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="MutedBrand", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.5, leading=12, textColor=BRAND["subtext"], spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="TableCell", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=8.0, leading=10, textColor=BRAND["text"], alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="TableHead", parent=styles["BodyText"], fontName="Helvetica-Bold",
        fontSize=8.0, leading=10, textColor=colors.white, alignment=TA_LEFT,
    ))
    return styles


_STYLES = _styles()


def _safe_text(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def has_data(value: Any) -> bool:
    if value is None or value == "":
        return False
    try:
        return not math.isnan(float(value))
    except Exception:
        text = str(value).strip()
        return bool(text) and text != "—"


def fmt_num(value: Any, digits: int = 2, suffix: str = "") -> str:
    if not has_data(value):
        return "Not available"
    try:
        num = float(value)
    except Exception:
        return str(value)
    return f"{num:.{digits}f}{suffix}"


def _resolve_logo_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "assets" / "logo.png",
        Path(__file__).resolve().parent / "assets" / "logo.png",
        Path("assets") / "logo.png",
    ]
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            pass
    return candidates[-1]


def add_report_header(story: List[Any], preset: str, category: str, hist_start: int, hist_end: int) -> None:
    logo_path = _resolve_logo_path()
    try:
        if logo_path.exists():
            logo = Image(str(logo_path))
            logo._restrictSize(4.2 * cm, 2.2 * cm)
            story.append(logo)
            story.append(Spacer(1, 0.2 * cm))
    except Exception:
        pass

    story.append(Paragraph("EagleNatureInsight™ — BL Turner Group", _STYLES["TitleBrand"]))
    story.append(Paragraph("Organic waste-to-fertiliser & biogas — TNFD-aligned nature intelligence report", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        f"Report date: {date.today().strftime('%d %B %Y')}<br/>"
        f"Site view: {_safe_text(preset)}<br/>"
        f"Business category: {_safe_text(category)}<br/>"
        f"Historical period: {hist_start} to {hist_end}",
        _STYLES["SubBrand"],
    ))
    story.append(Spacer(1, 0.15 * cm))


def classify_indicator(metric_name, value):
    try:
        if value is None or value == "":
            return "—"
        v = float(value)
    except Exception:
        return "—"
    if metric_name == "rain_anom_pct":
        if v <= -20: return "High concern"
        if v <= -10: return "Warning"
        if v <= -5: return "Watch"
        return "Favourable"
    if metric_name == "lst_mean":
        if v > 33: return "High concern"
        if v > 30: return "Warning"
        if v > 28: return "Watch"
        return "Favourable"
    if metric_name == "flood_risk":
        if v >= 0.5: return "High concern"
        if v >= 0.2: return "Warning"
        if v > 0: return "Watch"
        return "Favourable"
    if metric_name == "ndvi_trend":
        if v < -0.05: return "High concern"
        if v < -0.02: return "Warning"
        if v < 0: return "Watch"
        return "Favourable"
    if metric_name == "travel_time_to_market":
        if v > 180: return "High concern"
        if v > 120: return "Warning"
        if v > 60: return "Watch"
        return "Favourable"
    if metric_name == "fire_risk":
        if v > 10: return "Warning"
        if v > 0: return "Watch"
        return "Favourable"
    return "Watch"


def _fit_image(source: Any, max_width: float, max_height: float) -> Optional[Image]:
    try:
        img = Image(source)
        img._restrictSize(max_width, max_height)
        return img
    except Exception:
        return None


def _normalize_image_input(img: Any) -> Optional[io.BytesIO]:
    if img is None:
        return None
    if isinstance(img, io.BytesIO):
        img.seek(0)
        return img
    if isinstance(img, (bytes, bytearray)):
        return io.BytesIO(img)
    return None


def _metric_table(items: List[Tuple[str, str]], col_widths: Tuple[float, float]) -> Table:
    data = [[Paragraph(f"<b>{k}</b>", _STYLES["BodyBrand"]), Paragraph(v, _STYLES["BodyBrand"])] for k, v in items]
    tbl = Table(data, colWidths=col_widths, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND["card"]),
        ("BOX", (0, 0), (-1, -1), 0.5, BRAND["border"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, BRAND["border"]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return tbl


def _matrix_table(rows: List[List[str]], col_widths: Tuple[float, ...]) -> Table:
    wrapped_rows: List[List[Any]] = []
    for r_idx, row in enumerate(rows):
        wrapped_row = []
        for cell in row:
            text = _safe_text(cell, "")
            style = _STYLES["TableHead"] if r_idx == 0 else _STYLES["TableCell"]
            wrapped_row.append(Paragraph(text, style))
        wrapped_rows.append(wrapped_row)
    tbl = Table(wrapped_rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT", splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, BRAND["border"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LEADING", (0, 0), (-1, -1), 11),
    ]))
    return tbl


def _add_bullets(story: List[Any], items: Iterable[str]) -> None:
    for item in items:
        story.append(Paragraph(f"• {_safe_text(item)}", _STYLES["BodyBrand"]))


def _section_rule(story: List[Any]) -> None:
    story.append(Spacer(1, 0.1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.7, color=BRAND["border"]))
    story.append(Spacer(1, 0.15 * cm))


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(BRAND["muted"])
    canvas.drawRightString(PAGE_WIDTH - 1.6 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.drawString(1.6 * cm, 1.2 * cm, "BL Turner Group · EagleNatureInsight™ report")
    canvas.restoreState()


def _derive_findings(metrics: Dict[str, Any]) -> List[str]:
    findings: List[str] = []
    try:
        ra = metrics.get("rain_anom_pct")
        if ra is not None and float(ra) < -10:
            findings.append(
                f"Recent rainfall is {fmt_num(ra, 1, '%')} relative to the baseline, which increases pressure "
                "on process water and municipal supply for slurry preparation."
            )
    except Exception:
        pass
    try:
        fl = metrics.get("flood_risk")
        if fl is not None and float(fl) > 0.1:
            findings.append(
                f"Mapped 1-in-100-year flood depth of {fmt_num(fl, 2, ' m')} around the plant means "
                "digester tanks, CHP units and switchgear need flood-resilient siting and bunds."
            )
    except Exception:
        pass
    try:
        lst = metrics.get("lst_mean")
        if lst is not None and float(lst) > 30:
            findings.append(
                f"Recent land surface temperature of about {fmt_num(lst, 1, ' °C')} raises CHP cooling load, "
                "odour volatility at reception bays, and worker heat-safety risk."
            )
    except Exception:
        pass
    try:
        tt = metrics.get("travel_time_to_market")
        if tt is not None and float(tt) > 90:
            findings.append(
                f"Travel time to the main feedstock market (eThekwini) is about {fmt_num(tt, 0, ' minutes')}, "
                "which is meaningful for meat, blood and perishable food-waste loads."
            )
    except Exception:
        pass
    if not findings:
        findings = [
            "The site sits in a mixed environmental setting typical of KZN coastal industrial land.",
            "Water, heat, flood and vegetation indicators should be read together, not in isolation.",
            "The LEAP structure is used to turn satellite indicators into business-relevant interpretation.",
        ]
    return findings[:4]


def build_automated_risk_flags(metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    flags: List[Dict[str, str]] = []

    def add_flag(level, title, current_value, meaning, action):
        flags.append({"Level": level, "Flag": title, "Current value": current_value, "Why it matters": meaning, "Suggested action": action})

    try:
        v = metrics.get("rain_anom_pct")
        if v is not None and float(v) <= -15:
            f = float(v)
            add_flag("High", "Dry conditions",
                     f"{f:.1f}%",
                     f"Rainfall is {abs(f):.1f}% below the baseline, raising process-water cost and supply risk for slurry preparation.",
                     f"Lock in municipal water contracts and size on-site storage for at least a week while rainfall stays near {abs(f):.1f}% below baseline.")
    except Exception:
        pass
    try:
        v = metrics.get("lst_mean")
        if v is not None and float(v) >= 30:
            f = float(v)
            add_flag("High", "Heat stress",
                     f"{f:.1f} °C",
                     f"Surface heat is {f:.1f} °C, raising CHP cooling load, odour volatility, and worker-safety risk.",
                     f"Review CHP chillers, reception-hall ventilation, and shaded worker rest areas while heat remains near {f:.1f} °C.")
    except Exception:
        pass
    try:
        v = metrics.get("flood_risk")
        if v is not None and float(v) >= 0.5:
            f = float(v)
            add_flag("High", "Flood exposure",
                     f"{f:.2f} m",
                     f"Mapped 1-in-100-year flood depth of {f:.2f} m could compromise digester tanks, CHP units, switchgear and feedstock-handling infrastructure.",
                     f"Raise critical infrastructure above the {f:.2f} m flood line, build tank bunds, and clear drainage before each rainy season.")
    except Exception:
        pass
    try:
        v = metrics.get("travel_time_to_market")
        if v is not None and float(v) > 120:
            f = float(v)
            add_flag("Moderate", "Long-haul feedstock risk",
                     f"{f:.0f} min",
                     f"Travel time to the main feedstock market is about {f:.0f} minutes, increasing diesel cost, driver hours and spoilage risk for meat, blood and perishable food loads.",
                     "Explore a refrigerated transfer station closer to eThekwini, and off-peak collection windows.")
    except Exception:
        pass
    try:
        v = metrics.get("fire_risk")
        if v is not None and float(v) > 5:
            f = float(v)
            add_flag("Moderate", "Fire signal in landscape",
                     f"{f:.1f}",
                     f"A recent burned-area signal of {f:.1f} sits in the surrounding landscape. The plant handles flammable biogas.",
                     "Maintain firebreaks, avoid dry-vegetation build-up near gas storage, and align with municipal fire response plans.")
    except Exception:
        pass

    if not flags:
        add_flag("Monitor", "No dominant automated flag", "Current conditions",
                 "The current indicator set does not show a single dominant automated warning. Seasonal review still matters.",
                 "Continue routine monitoring and update the assessment before each seasonal operational review.")
    return flags


def _tnfd_core_metrics_table_pdf(metrics: Dict[str, Any]) -> Table:
    rows = [
        ["TNFD core metric", "Proxy used here", "Value", "Meaning / TNFD link"],
        ["C1.0 Spatial footprint",
         "Plant site footprint",
         fmt_num(metrics.get("area_ha"), 2, " ha"),
         "Size of the area screened (nominal 1.5 ha at Portion 159)."],
        ["C1.1 Ecosystem extent change",
         "Tree cover, cropland, forest-loss",
         f"Tree {fmt_num(metrics.get('tree_cover_context_pct', metrics.get('tree_pct')), 1, '%')} · "
         f"Crop {fmt_num(metrics.get('cropland_pct'), 1, '%')} · "
         f"Forest loss {fmt_num(metrics.get('forest_loss_pct'), 1, '%')}",
         "Used as proxy for ecosystem extent change. Aligns with NPI IND1."],
        ["C2.5 GHG emissions (screening)",
         "Landfill diversion at 100 tpd",
         "~9,125 tCO₂e/year avoided (indicative)",
         "Screening figure at ~0.25 tCO₂e avoided per tonne diverted from landfill. Needs a formal GHG methodology."],
        ["C3.0 Water use in water-scarce areas",
         "Rainfall anomaly, ET, surface water",
         f"Rain {fmt_num(metrics.get('rain_anom_pct'), 1, '%')} · "
         f"ET {fmt_num(metrics.get('evapotranspiration'), 1)} · "
         f"Water {fmt_num(metrics.get('water_occ'), 1)}",
         "Water stress context. Actual process-water volumes come from plant metering."],
        ["C5.0 Ecosystem condition",
         "NDVI and trend",
         f"NDVI {fmt_num(metrics.get('ndvi_current'), 3)} · trend {fmt_num(metrics.get('ndvi_trend'), 3)}",
         "Used as proxy for ecosystem condition. Aligns with NPI IND2."],
        ["C7.0–C7.1 Physical risk / opportunity",
         "Heat, flood, fire, drought",
         f"LST {fmt_num(metrics.get('lst_mean'), 1, ' °C')} · "
         f"Flood {fmt_num(metrics.get('flood_risk'), 2, ' m')} · "
         f"PDSI {fmt_num(metrics.get('pdsi'), 1)}",
         "Physical nature-related risk signals for operations and assets."],
        ["C2.x Pollutants / waste",
         "Not yet computed",
         "—",
         "Comply-or-explain: requires BL Turner environmental monitoring (digestate liquor, CHP stack, odour)."],
    ]
    wrapped_rows = [[Paragraph(_safe_text(c), _STYLES["TableHead"] if i == 0 else _STYLES["TableCell"]) for c in r] for i, r in enumerate(rows)]
    tbl = Table(wrapped_rows, colWidths=[3.5 * cm, 3.8 * cm, 4.0 * cm, 4.8 * cm], repeatRows=1, hAlign="LEFT", splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, BRAND["border"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("LEADING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def _waste_sources_table(waste_sources: List[Dict[str, Any]]) -> Table:
    rows = [["Source", "District", "Waste stream", "t/day", "Frequency", "Seasonality", "Role"]]
    for s in waste_sources:
        rows.append([
            s.get("name", ""),
            s.get("district", ""),
            s.get("stream", ""),
            f"{float(s.get('tons_per_day_est', 0)):.1f}",
            s.get("collection_frequency", ""),
            s.get("seasonality", ""),
            s.get("role", ""),
        ])
    wrapped = [[Paragraph(_safe_text(c), _STYLES["TableHead"] if i == 0 else _STYLES["TableCell"]) for c in r] for i, r in enumerate(rows)]
    tbl = Table(wrapped, colWidths=[3.0 * cm, 2.4 * cm, 2.6 * cm, 1.1 * cm, 2.4 * cm, 3.0 * cm, 2.0 * cm], repeatRows=1, hAlign="LEFT", splitByRow=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND["primary"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, BRAND["border"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LEADING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


def _monthly_supply_chart_bytes(monthly_profile: List[Dict[str, Any]]) -> Optional[bytes]:
    if not monthly_profile:
        return None
    try:
        months = [p["month"] for p in monthly_profile]
        supply = [p["supply_tpd"] for p in monthly_profile]
        nameplate = [p["nameplate_tpd"] for p in monthly_profile]

        fig, ax = plt.subplots(figsize=(7.4, 3.6))
        ax.bar(months, supply, color="#1f8f5f", label="Indicative feedstock supply (t/day)")
        ax.plot(months, nameplate, color="#c0392b", linewidth=2, marker="o", label="Nameplate capacity (100 t/day)")
        ax.set_ylabel("Tonnes per day")
        ax.set_title("Seasonal feedstock supply vs 100 t/day nameplate capacity")
        ax.grid(True, axis="y", alpha=0.25)
        ax.set_axisbelow(True)
        ax.legend(frameon=False, loc="lower right", fontsize=8)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
        plt.close(fig)
        return buf.getvalue()
    except Exception:
        try:
            plt.close("all")
        except Exception:
            pass
        return None


def _image_block(story: List[Any], title: str, description: str, img_data: Any) -> None:
    bio = _normalize_image_input(img_data)
    if not bio:
        return
    img = _fit_image(bio, 17.5 * cm, 10.0 * cm)
    if not img:
        return
    story.append(Paragraph(title, _STYLES["SmallBrand"]))
    story.append(Paragraph(description, _STYLES["MutedBrand"]))
    story.append(img)
    story.append(Spacer(1, 0.15 * cm))


def _chart_block(story: List[Any], title: str, description: str, chart_data: Any) -> None:
    bio = _normalize_image_input(chart_data)
    if not bio:
        return
    img = _fit_image(bio, 17.5 * cm, 8.8 * cm)
    if not img:
        return
    story.append(Paragraph(title, _STYLES["SmallBrand"]))
    story.append(Paragraph(description, _STYLES["MutedBrand"]))
    story.append(img)
    story.append(Spacer(1, 0.15 * cm))


def build_pdf_report(
    preset: str,
    category: str,
    hist_start: int,
    hist_end: int,
    metrics: Dict[str, Any],
    risk: Dict[str, Any],
    image_payloads: Optional[List[Dict[str, Any]]] = None,
    chart_payloads: Optional[List[Dict[str, Any]]] = None,
    automated_flags: Optional[List[Dict[str, str]]] = None,
    waste_sources: Optional[List[Dict[str, Any]]] = None,
    monthly_supply: Optional[List[Dict[str, Any]]] = None,
    continuity_risks: Optional[List[Dict[str, str]]] = None,
    stream_mix: Optional[List[Dict[str, Any]]] = None,
    district_mix: Optional[List[Dict[str, Any]]] = None,
    supply_headroom_data: Optional[Dict[str, float]] = None,
    **kwargs,
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.5 * cm,
        title="EagleNatureInsight BL Turner Report",
        author="Space Eagle Enterprise",
    )

    story: List[Any] = []

    add_report_header(story, preset, category, hist_start, hist_end)

    story.append(Paragraph(
        "TNFD-aligned organic waste-to-fertiliser and biogas nature intelligence report for BL Turner "
        "Group's 100 t/day anaerobic digestion facility at Portion 159 of New Guelderland, KwaDukuza "
        "(iLembe District, KwaZulu-Natal). Waste is sourced from eThekwini Metropolitan Municipality "
        "(restaurants, commercial kitchens, distribution centres), the iLembe district, and "
        "uMgungundlovu abattoir cluster, with digestate fertiliser distributed to KZN farmlands.",
        _STYLES["SubBrand"],
    ))

    # --- 1. Executive summary ---
    story.append(Paragraph("1. Executive summary", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        f"This report summarises environmental and nature-related screening results for <b>{_safe_text(preset)}</b> "
        f"over the historical period <b>{hist_start}–{hist_end}</b>.",
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph(
        "The report follows the <b>TNFD LEAP approach</b> (Locate, Evaluate, Assess, Prepare) and maps to the "
        "<b>Nature Positive Initiative (NPI) State of Nature</b> indicators, presented in language suitable for "
        "operations managers, municipal partners, funders and TNFD reviewers.",
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph(
        _safe_text(metrics.get("analysis_context_method"),
                   "Site-specific indicators are measured on the exact polygon where dataset resolution allows. "
                   "Coarser climate, water, soil, flood, or landscape-support indicators may be evaluated on a "
                   "wider context window, while maps still keep the exact site boundary in red."),
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph("<b>Top takeaways</b>", _STYLES["SmallBrand"]))
    _add_bullets(story, _derive_findings(metrics))
    _add_bullets(story, [
        "Landfill diversion at 100 t/day is the largest nature-positive story for this business — indicatively "
        "around 9,125 tCO₂e/year avoided methane (screening figure).",
        "Feedstock continuity of supply is the central operational nature-related dependency and needs multi-source contracting.",
        "Indicators align with NPI IND1 (Ecosystem Extent) and IND2 (Ecosystem Condition).",
    ])
    _section_rule(story)

    # --- 2. Abbreviations ---
    story.append(Paragraph("2. Reading guide and defined abbreviations", _STYLES["SectionBrand"]))
    story.append(_metric_table(sorted(ABBREVIATIONS.items()), (3.2 * cm, 13.8 * cm)))
    _section_rule(story)

    # --- 3. Plant site overview ---
    story.append(Paragraph("3. Plant site overview metrics", _STYLES["SectionBrand"]))
    overview_rows = [
        ("Plant site", _safe_text(preset)),
        ("Business category", _safe_text(category)),
        ("Assessment area", fmt_num(metrics.get("area_ha"), 2, " ha")),
        ("Current vegetation condition (NDVI)", fmt_num(metrics.get("ndvi_current"), 3)),
        ("Vegetation trend", fmt_num(metrics.get("ndvi_trend"), 3)),
        ("Rainfall anomaly", fmt_num(metrics.get("rain_anom_pct"), 1, "%")),
        ("Recent land surface temperature", fmt_num(metrics.get("lst_mean"), 1, " °C")),
        ("Tree / semi-natural cover (context)", fmt_num(metrics.get("tree_cover_context_pct", metrics.get("tree_pct")), 1, "%")),
        ("Cropland cover", fmt_num(metrics.get("cropland_pct"), 1, "%")),
        ("Built-up cover", fmt_num(metrics.get("built_pct"), 1, "%")),
        ("Surface-water signal (context)", fmt_num(metrics.get("water_context_signal_pct", metrics.get("water_occ")), 1)),
        ("Flood hazard (1-in-100-yr depth)", fmt_num(metrics.get("flood_risk"), 2, " m")),
        ("Fire signal", fmt_num(metrics.get("fire_risk"), 1)),
        ("Travel time to eThekwini market", fmt_num(metrics.get("travel_time_to_market"), 0, " min")),
        ("Forest loss in landscape", fmt_num(metrics.get("forest_loss_pct"), 1, "%")),
    ]
    overview_rows = [(k, v) for k, v in overview_rows if v != "Not available"]
    story.append(_metric_table(overview_rows, (7.2 * cm, 9.8 * cm)))
    _section_rule(story)

    # --- 4. TNFD core metrics ---
    story.append(Paragraph("4. TNFD Core Global Disclosure Metrics", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "This table maps the current screening outputs to TNFD Annex 1 core metrics. It is a practical proxy "
        "table, not a full disclosure table, and is honest about which items are direct measurements, proxies, "
        "or 'comply or explain' placeholders that require BL Turner's own operational data.",
        _STYLES["BodyBrand"],
    ))
    story.append(_tnfd_core_metrics_table_pdf(metrics))
    _section_rule(story)

    # --- 5. Waste sourcing ---
    story.append(Paragraph("5. Organic waste sourcing portfolio", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "This section translates the plant's 100 t/day feedstock requirement into a structured view of where "
        "the waste comes from, at what frequency, in what volume, with what seasonal pattern, and with what "
        "continuity-of-supply risk. It combines KwaDukuza (iLembe), eThekwini Metropolitan Municipality, "
        "uMgungundlovu abattoir, and Western KZN agricultural sources.",
        _STYLES["BodyBrand"],
    ))

    if supply_headroom_data:
        sh = supply_headroom_data
        story.append(_metric_table([
            ("Plant nameplate capacity", f"{sh.get('nameplate_tpd', 0):.0f} tonnes per day"),
            ("Indicative feedstock supply available", f"{sh.get('estimated_supply_tpd', 0):.0f} tonnes per day"),
            ("Headroom over nameplate", f"{sh.get('headroom_tpd', 0):+.0f} tonnes per day"),
            ("Supply coverage of nameplate", f"{sh.get('coverage_pct', 0):.0f}%"),
        ], (7.2 * cm, 9.8 * cm)))
        story.append(Spacer(1, 0.2 * cm))

    if waste_sources:
        story.append(Paragraph("5a. Waste sources (frequency, tonnage, seasonality, role)", _STYLES["SmallBrand"]))
        story.append(_waste_sources_table(waste_sources))
        story.append(Spacer(1, 0.2 * cm))

    if stream_mix:
        story.append(Paragraph("5b. Waste stream mix", _STYLES["SmallBrand"]))
        sm_rows = [["Waste stream", "t/day", "Share of portfolio"]]
        for row in stream_mix:
            sm_rows.append([row["stream"], f"{row['tons_per_day']:.1f}", f"{row['share_pct']:.1f}%"])
        story.append(_matrix_table(sm_rows, (8.0 * cm, 3.0 * cm, 6.0 * cm)))
        story.append(Spacer(1, 0.2 * cm))

    if district_mix:
        story.append(Paragraph("5c. District mix", _STYLES["SmallBrand"]))
        dm_rows = [["KZN district", "t/day", "Share of portfolio"]]
        for row in district_mix:
            dm_rows.append([row["district"], f"{row['tons_per_day']:.1f}", f"{row['share_pct']:.1f}%"])
        story.append(_matrix_table(dm_rows, (8.0 * cm, 3.0 * cm, 6.0 * cm)))
        story.append(Spacer(1, 0.2 * cm))

    if monthly_supply:
        chart_bytes = _monthly_supply_chart_bytes(monthly_supply)
        if chart_bytes:
            story.append(Paragraph("5d. Seasonal supply profile", _STYLES["SmallBrand"]))
            story.append(Paragraph(
                "Indicative modelled feedstock supply by month versus the 100 t/day nameplate line. Used to "
                "plan storage, supplementary contracts and maintenance windows.",
                _STYLES["MutedBrand"],
            ))
            img = _fit_image(io.BytesIO(chart_bytes), 17.5 * cm, 9.0 * cm)
            if img:
                story.append(img)
                story.append(Spacer(1, 0.2 * cm))

    if continuity_risks:
        story.append(Paragraph("5e. Continuity of supply risks", _STYLES["SmallBrand"]))
        cr_rows = [["Risk", "Severity", "Finding", "Mitigation"]]
        for r in continuity_risks:
            cr_rows.append([r.get("risk", ""), r.get("severity", ""), r.get("finding", ""), r.get("mitigation", "")])
        story.append(_matrix_table(cr_rows, (3.8 * cm, 1.8 * cm, 5.6 * cm, 5.8 * cm)))

    _section_rule(story)

    # --- 6. LEAP summary ---
    story.append(Paragraph("6. LEAP summary (Locate, Evaluate, Assess, Prepare)", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "<b>Locate</b>: The plant site and surrounding landscape were screened, along with the waste "
        "sourcing geography across KZN.",
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph(
        "<b>Evaluate</b>: Dependencies on nature — organic waste feedstock supply, process water, flood "
        "resilience, nutrient cycling in receiving farmlands — were assessed.",
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph(
        "<b>Assess</b>: Indicators were translated into physical risks, opportunities, and a "
        "business-focused interpretation, including the avoided methane emissions from landfill diversion.",
        _STYLES["BodyBrand"],
    ))
    story.append(Paragraph(
        "<b>Prepare</b>: Practical operational and contractual actions were identified, plus monitoring "
        "and stakeholder engagement priorities.",
        _STYLES["BodyBrand"],
    ))
    _section_rule(story)

    # --- 7. TNFD dependencies ---
    story.append(Paragraph("7. TNFD-style dependencies on nature", _STYLES["SectionBrand"]))
    for dep in (risk.get("dependencies") or []):
        story.append(Paragraph(f"<b>{_safe_text(dep.get('service'))}</b>", _STYLES["SmallBrand"]))
        story.append(Paragraph(_safe_text(dep.get("why_it_matters")), _STYLES["BodyBrand"]))
    _section_rule(story)

    # --- 8. Indicator portfolio ---
    story.append(Paragraph("8. Portfolio of nature-related indicators (no single score)", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "TNFD explicitly recommends against reducing nature issues to a single number. The table below "
        "presents each indicator with its own status, plain meaning, and suggested response.",
        _STYLES["BodyBrand"],
    ))
    port_rows = [["Indicator", "Status", "What this means", "Suggested response"]]
    for row in (risk.get("portfolio") or []):
        port_rows.append([row.get("name", ""), row.get("status", ""), row.get("plain_meaning", ""), row.get("response", "")])
    story.append(_matrix_table(port_rows, (3.8 * cm, 1.8 * cm, 5.6 * cm, 5.8 * cm)))
    _section_rule(story)

    # --- 9. Monetary exposures ---
    story.append(Paragraph("9. Indicative business exposures (units of currency)", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "TNFD asks for exposures to be presented in units of nature and units of currency. The figures below "
        "are screening-level directional signals — they are not precise accounting figures, and all "
        "assumptions are stated in plain English.",
        _STYLES["BodyBrand"],
    ))
    for item in (risk.get("monetary_exposures") or []):
        story.append(Paragraph(f"<b>{_safe_text(item.get('label'))}</b>", _STYLES["SmallBrand"]))
        story.append(Paragraph(_safe_text(item.get("headline")), _STYLES["BodyBrand"]))
        story.append(Paragraph(_safe_text(item.get("assumption")), _STYLES["MutedBrand"]))
    _section_rule(story)

    # --- 10. Automated risk flags ---
    story.append(Paragraph("10. Automated risk flags", _STYLES["SectionBrand"]))
    flags = automated_flags or build_automated_risk_flags(metrics)
    rf_rows = [["Level", "Flag", "Current value", "Why it matters", "Suggested action"]]
    for row in flags:
        rf_rows.append([row.get("Level", ""), row.get("Flag", ""), row.get("Current value", ""), row.get("Why it matters", ""), row.get("Suggested action", "")])
    story.append(_matrix_table(rf_rows, (1.6 * cm, 2.8 * cm, 2.2 * cm, 5.0 * cm, 5.4 * cm)))
    _section_rule(story)

    # --- 11. Recommendations ---
    story.append(Paragraph("11. Prepare — recommended actions for BL Turner", _STYLES["SectionBrand"]))
    _add_bullets(story, risk.get("recs") or [])
    _section_rule(story)

    # --- 12. Monitoring ---
    story.append(Paragraph("12. Monitoring and review frequency", _STYLES["SectionBrand"]))
    _add_bullets(story, [
        "Review this assessment before the start of each rainy season (around Sep–Oct).",
        "Review after major weather events, especially floods.",
        "Review before commissioning, capacity upgrades, or new feedstock contracts.",
        "Review annually ahead of municipal waste contract renegotiations and funder reporting cycles.",
    ])
    _section_rule(story)

    # --- 13. Images ---
    story.append(Paragraph("13. Satellite image outputs", _STYLES["SectionBrand"]))
    story.append(Paragraph(
        "Each image is paired with a short explanation of what it shows and why it matters for the plant.",
        _STYLES["BodyBrand"],
    ))
    for payload in (image_payloads or []):
        if not payload.get("bytes"):
            continue
        _image_block(story, _safe_text(payload.get("title")), _safe_text(payload.get("description")), payload.get("bytes"))

    story.append(PageBreak())

    # --- 14. Charts ---
    story.append(Paragraph("14. Historical trend charts", _STYLES["SectionBrand"]))
    for payload in (chart_payloads or []):
        if not payload.get("bytes"):
            continue
        _chart_block(story, _safe_text(payload.get("title")), _safe_text(payload.get("description")), payload.get("bytes"))
    _section_rule(story)

    # --- 15. Detailed metrics appendix ---
    story.append(Paragraph("15. Detailed metrics appendix", _STYLES["SectionBrand"]))
    appendix_rows = sorted((str(k), _safe_text(v)) for k, v in metrics.items() if has_data(v))
    story.append(_metric_table(appendix_rows, (6.0 * cm, 11.0 * cm)))

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buffer.getvalue()

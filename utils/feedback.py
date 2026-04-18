"""
Lightweight in-app feedback capture for the Jan–April 2026 SME
testing phase of the Nature Intelligence for Business Grand Challenge.

Addresses rubric item 3d (Iteration & Roadmap Responsiveness):
  "Credible plan to incorporate SME user feedback from the Challenge"
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st


FEEDBACK_LOG = Path("feedback_log.jsonl")


def _append_feedback(record: Dict[str, Any]) -> bool:
    try:
        FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with FEEDBACK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def render_feedback_widget(context: Optional[Dict[str, Any]] = None) -> None:
    """Render a compact feedback form."""
    context = context or {}
    if st.session_state.get("_feedback_submitted_this_session"):
        st.success("Thanks — your feedback has been recorded for this session.")
        return

    with st.expander("Share feedback with the EagleNatureInsight team"):
        st.caption(
            "Your feedback helps us improve the platform during the TNFD / Conservation X Labs "
            "Nature Intelligence for Business Grand Challenge testing period (Jan–April 2026). "
            "No personal data is required."
        )
        form_key_parts = [
            "eni_feedback_form",
            str(context.get("tab", "general")),
            str(context.get("preset", "default")),
        ]
        form_key = "__".join(form_key_parts).replace(" ", "_").replace("/", "_")
        with st.form(form_key, clear_on_submit=False):
            rating = st.radio(
                "How useful is what you are looking at right now?",
                options=["Very useful", "Somewhat useful", "Not clear", "Not useful"],
                horizontal=True,
                index=1,
            )
            what_worked = st.text_area(
                "What worked well or what did you understand immediately? (optional)",
                height=80,
            )
            what_to_improve = st.text_area(
                "What was confusing, missing, or what should we improve? (optional)",
                height=80,
            )
            role = st.selectbox(
                "Which best describes you?",
                [
                    "BL Turner team / operator",
                    "Municipality / waste management",
                    "Farmer / digestate off-taker",
                    "Funder or bank",
                    "TNFD / Challenge partner",
                    "Researcher",
                    "Other",
                ],
            )
            email = st.text_input(
                "Optional: email if you are happy to be contacted for follow-up",
                placeholder="you@example.com",
            )
            submitted = st.form_submit_button("Send feedback", use_container_width=True)

        if submitted:
            record = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "rating": rating,
                "what_worked": what_worked.strip(),
                "what_to_improve": what_to_improve.strip(),
                "role": role,
                "email": email.strip(),
                "context": context,
            }
            ok = _append_feedback(record)
            if ok:
                st.session_state["_feedback_submitted_this_session"] = True
                st.success("Thank you — your feedback has been saved.")
            else:
                st.warning(
                    "We could not save feedback to disk in this environment. "
                    "Please copy your comments and share them directly with the team."
                )


def render_feedback_admin(password: Optional[str] = None) -> None:
    """Optional admin view — lists recent feedback entries."""
    st.markdown("### Feedback log (pilot admin view)")
    if password is not None:
        entered = st.text_input("Admin password", type="password")
        if entered != password:
            st.info("Enter the admin password to view the feedback log.")
            return
    if not FEEDBACK_LOG.exists():
        st.info("No feedback has been recorded yet.")
        return
    try:
        lines = FEEDBACK_LOG.read_text(encoding="utf-8").splitlines()
    except Exception:
        st.warning("Could not read feedback log.")
        return
    st.caption(f"{len(lines)} feedback records on file.")
    for line in reversed(lines[-25:]):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        st.markdown(
            f"**{rec.get('timestamp','?')}** · *{rec.get('role','?')}* · "
            f"Rating: **{rec.get('rating','?')}**"
        )
        if rec.get("what_worked"):
            st.markdown(f"- Worked: {rec['what_worked']}")
        if rec.get("what_to_improve"):
            st.markdown(f"- Improve: {rec['what_to_improve']}")
        if rec.get("email"):
            st.caption(f"Contact: {rec['email']}")
        st.markdown("---")

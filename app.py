import streamlit as st
import streamlit.components.v1 as components
import html
import re
from textwrap import dedent


MAINTENANCE_RULES = [
    {
        "keywords": ["leak", "leaking", "seepage", "drip"],
        "recommendation": "Check for active leakage, isolate if needed, inspect seals, gaskets, flanges, and nearby corrosion.",
        "severity": 8,
        "likelihood": 7,
    },
    {
        "keywords": ["corrosion", "rust", "pitting", "wall loss"],
        "recommendation": "Perform visual inspection and thickness testing, document affected areas, and evaluate repair or replacement.",
        "severity": 7,
        "likelihood": 6,
    },
    {
        "keywords": ["vibration", "shaking", "noise", "rattling"],
        "recommendation": "Inspect supports, alignment, bearings, fasteners, and operating conditions for abnormal vibration or looseness.",
        "severity": 6,
        "likelihood": 6,
    },
    {
        "keywords": ["overheating", "hot", "temperature", "high temp"],
        "recommendation": "Check temperature readings, verify cooling or heat transfer performance, and inspect insulation or fouling.",
        "severity": 7,
        "likelihood": 5,
    },
    {
        "keywords": ["pressure", "high pressure", "low pressure", "pressure drop"],
        "recommendation": "Verify pressure instruments, check valves and restrictions, and review operating limits before continued operation.",
        "severity": 8,
        "likelihood": 5,
    },
    {
        "keywords": ["crack", "cracked", "fracture"],
        "recommendation": "Remove from service if structural integrity is uncertain, perform NDE inspection, and escalate for engineering review.",
        "severity": 10,
        "likelihood": 7,
    },
    {
        "keywords": ["fouling", "plugged", "clogged", "blocked", "restriction"],
        "recommendation": "Inspect for fouling or blockage, review flow performance, and schedule cleaning or flushing if confirmed.",
        "severity": 5,
        "likelihood": 7,
    },
]

NON_ROTATING_EQUIPMENT_OPTIONS = [
    "Pressure Vessels",
    "Storage Tanks",
    "Heat Exchangers",
    "Boilers & Furnaces",
    "Columns & Reactors",
    "Piping Systems",
    "Pump",
    "Condenser",
]

NON_ROTATING_EQUIPMENT_KEYWORDS = {
    "Pressure Vessels": ["pressure vessel", "pressure vessels"],
    "Storage Tanks": ["storage tank", "storage tanks", "tank", "tanks"],
    "Heat Exchangers": ["heat exchanger", "heat exchangers", "exchanger", "exchangers"],
    "Boilers & Furnaces": ["boiler", "boilers", "furnace", "furnaces"],
    "Columns & Reactors": ["column", "columns", "reactor", "reactors"],
    "Piping Systems": ["piping system", "piping systems", "piping", "pipe", "pipes"],
    "Pump": ["pump", "pumps"],
    "Condenser": ["condenser", "condensers"],
}


def find_issue_recommendations(issue_description):
    description = issue_description.lower()
    matches = []

    for rule in MAINTENANCE_RULES:
        if any(keyword in description for keyword in rule["keywords"]):
            matches.append(rule["recommendation"])

    return matches


def calculate_issue_scores(issue_description):
    description = issue_description.lower()
    matched_rules = [
        rule
        for rule in MAINTENANCE_RULES
        if any(keyword in description for keyword in rule["keywords"])
    ]

    if not matched_rules:
        return None, None

    severity = max(rule["severity"] for rule in matched_rules)
    likelihood = max(rule["likelihood"] for rule in matched_rules)
    return severity, likelihood


def score_to_grid_position(score):
    if score <= 2:
        return 0
    if score <= 5:
        return 1
    if score <= 7:
        return 2
    return 3


def show_risk_grid(severity, likelihood):
    dot_row = None
    dot_column = None

    if severity is not None and likelihood is not None:
        dot_row = 3 - score_to_grid_position(severity)
        dot_column = score_to_grid_position(likelihood)

    rows = []
    for row in range(4):
        cells = []
        for column in range(4):
            dot_html = ""
            if row == dot_row and column == dot_column:
                dot_html = dedent(
                    """
                    <div
                        style="
                            width: 14px;
                            height: 14px;
                            background: #d92d20;
                            border: 2px solid #ffffff;
                            border-radius: 999px;
                            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
                        "
                    ></div>
                    """
                ).strip()

            cells.append(
                dedent(
                    f"""
                <div
                    style="
                        width: 56px;
                        height: 56px;
                        border: 1px solid #9ca3af;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: #f9fafb;
                    "
                >
                    {dot_html}
                </div>
                """
                ).strip()
            )
        rows.append(f"<div style='display: flex;'>{''.join(cells)}</div>")

    components.html(
        dedent(
            f"""
        <div style="margin: 8px 0 24px;">
            <div
                style="
                    width: 224px;
                    margin-left: 35px;
                    text-align: center;
                    font-weight: 600;
                    font-size: 14px;
                    color: #ffffff;
                    margin-bottom: 6px;
                "
            >
                Likelihood
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <div
                    style="
                        writing-mode: vertical-rl;
                        transform: rotate(180deg);
                        font-weight: 600;
                        font-size: 14px;
                        color: #ffffff;
                    "
                >
                    Severity
                </div>
                <div>
                    {''.join(rows)}
                </div>
            </div>
        </div>
        """
        ).strip(),
        height=270,
    )


def format_issue_description(issue_description, selected_option):
    formatted_description = html.escape(issue_description)

    for equipment, keywords in NON_ROTATING_EQUIPMENT_KEYWORDS.items():
        should_cross_out = equipment != selected_option

        for keyword in sorted(keywords, key=len, reverse=True):
            escaped_keyword = html.escape(keyword)
            pattern = re.compile(rf"\b({re.escape(escaped_keyword)})\b", re.IGNORECASE)

            if should_cross_out:
                formatted_description = pattern.sub(
                    r"<span style='text-decoration: line-through; color: #9ca3af;'>\1</span>",
                    formatted_description,
                )

    return formatted_description.replace("\n", "<br>")


def detect_equipment_from_issue(issue_description):
    earliest_match = None

    for equipment, keywords in NON_ROTATING_EQUIPMENT_KEYWORDS.items():
        for keyword in keywords:
            match = re.search(rf"\b{re.escape(keyword)}\b", issue_description, re.IGNORECASE)
            if match and (earliest_match is None or match.start() < earliest_match[0]):
                earliest_match = (match.start(), equipment)

    return earliest_match[1] if earliest_match else None


def show_issue_description_preview(issue_description):
    if not issue_description.strip():
        return

    detected_equipment = detect_equipment_from_issue(issue_description)
    formatted_description = format_issue_description(issue_description, detected_equipment)
    st.markdown("**Filtered Issue Description**")
    st.markdown(
        f"""
        <div style="
            border: 1px solid #374151;
            border-radius: 6px;
            padding: 10px 12px;
            min-height: 48px;
            background: #111827;
            color: #ffffff;
            line-height: 1.5;
        ">
            {formatted_description}
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("AI Maintenance Planner")

equipment_type = st.selectbox(
    "Equipment Type",
    [
        "Rotating Equipment",
        "Non-Rotating Equipment",
    ],
    index=1,
    key="equipment_type_category",
)

issue_description = st.text_area("Issue Description")
detected_equipment = None

if equipment_type == "Non-Rotating Equipment":
    detected_equipment = detect_equipment_from_issue(issue_description)
    st.text_input(
        "Non-Rotating Equipment",
        value=detected_equipment or "No equipment detected",
        disabled=True,
    )

selected_equipment = (
    detected_equipment
    if equipment_type == "Non-Rotating Equipment" and detected_equipment
    else equipment_type
)

if equipment_type == "Non-Rotating Equipment":
    show_issue_description_preview(issue_description)

severity, likelihood = calculate_issue_scores(issue_description)
show_risk_grid(severity, likelihood)

risk_score = round((severity + likelihood) / 20 * 100) if severity and likelihood else 0

if st.button("Generate Maintenance Recommendation"):
    issue_recommendations = find_issue_recommendations(issue_description)

    st.subheader("Result")
    st.write(f"Risk Score: {risk_score}/100")

    if risk_score >= 75:
        priority = "High"
        recommendation = "Inspect immediately and create a high-priority work order."
    elif risk_score >= 40:
        priority = "Medium"
        recommendation = "Schedule inspection during the next maintenance window."
    else:
        priority = "Low"
        recommendation = "Monitor condition and document the issue."

    st.write(f"Priority: {priority}")
    st.write(f"Recommendation: {recommendation}")

    if issue_recommendations:
        st.subheader("Issue-Based Recommendations")
        for issue_recommendation in issue_recommendations:
            st.write(f"- {issue_recommendation}")
    else:
        st.info("No issue-specific keywords detected. Use the base risk recommendation.")

    st.subheader("Suggested Work Order")
    issue_actions = " ".join(issue_recommendations) if issue_recommendations else recommendation
    st.write(
        f"Investigate issue on {selected_equipment}. "
        f"Reported condition: {issue_description}. "
        f"Priority level: {priority}. Recommended action: {issue_actions}"
    )

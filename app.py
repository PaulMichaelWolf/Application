import streamlit as st
import streamlit.components.v1 as components
import html
import re
from textwrap import dedent


TENSE_LIKELIHOOD = {
    "present": 10,
    "future": 7,
    "past": 4,
    "negative": 0,
}

MAINTENANCE_RULES = [
    {
        "recommendation": "Isolate if needed.",
        "keywords": {
            "present": ["leak", "leaking", "seepage", "drip", "dripping"],
            "past": ["leaked", "was leaking", "seeped", "dripped"],
            "future": ["will leak", "may leak", "could leak", "expected to leak"],
            "negative": ["not leaking", "no leak", "no leakage", "not dripping"],
        },
        "severity": 10,
        
    },
    {
        "recommendation": "Perform thickness testing.",
        "keywords": {
            "present": ["corrosion", "rust", "pitting", "wall loss", "corroding"],
            "past": ["corroded", "rusted", "pitted", "lost wall thickness"],
            "future": ["will corrode", "may corrode", "could corrode", "expected to corrode"],
            "negative": ["not corroding", "no corrosion", "no rust", "no pitting"],
        },
        "severity": 4,
        
    },
    {
        "recommendation": "Inspect supports, alignment, bearings, fasteners, and operating conditions for abnormal vibration or looseness.",
        "keywords": {
            "present": ["vibration", "vibrating", "shaking", "noise", "rattling"],
            "past": ["vibrated", "was vibrating", "shook", "rattled", "made noise"],
            "future": ["will vibrate", "may vibrate", "could vibrate", "expected to vibrate"],
            "negative": ["not vibrating", "no vibration", "not shaking", "no noise", "not rattling"],
        },
        "severity": 7,
        
    },
    {
        "recommendation": "Check temperature readings, verify cooling or heat transfer performance, and inspect insulation or fouling.",
        "keywords": {
            "present": ["overheating", "hot", "temperature", "high temp", "high temperature"],
            "past": ["overheated", "was hot", "ran hot", "had high temperature"],
            "future": ["will overheat", "may overheat", "could overheat", "expected to overheat"],
            "negative": ["not overheating", "not hot", "no high temperature", "normal temperature"],
        },
        "severity": 7,
        
    },
    {
        "recommendation": "Verify pressure instruments, check valves and restrictions, and review operating limits before continued operation.",
        "keywords": {
            "present": ["pressure", "high pressure", "low pressure", "pressure drop"],
            "past": ["pressurized", "lost pressure", "dropped pressure", "had pressure drop"],
            "future": ["will pressurize", "may lose pressure", "could lose pressure", "expected pressure drop"],
            "negative": ["no pressure issue", "no pressure drop", "not pressurized", "pressure normal"],
        },
        "severity": 8,
        
    },
    {
        "recommendation": "Remove from service if structural integrity is uncertain, perform NDE inspection, and escalate for engineering review.",
        "keywords": {
            "present": ["crack", "cracking", "fracture", "fracturing"],
            "past": ["cracked", "fractured", "was cracked", "had fractured"],
            "future": ["will crack", "may crack", "could crack", "expected to crack"],
            "negative": ["not cracked", "no crack", "no cracking", "no fracture"],
        },
        "severity": 10,
        
    },
    {
        "recommendation": "Inspect for fouling or blockage, review flow performance, and schedule cleaning or flushing if confirmed.",
        "keywords": {
            "present": ["fouling", "plugging", "clogging", "blocked", "restriction"],
            "past": ["fouled", "plugged", "clogged", "was blocked", "restricted"],
            "future": ["will foul", "may plug", "could clog", "expected to block"],
            "negative": ["not fouled", "not plugged", "not clogged", "not blocked", "no restriction"],
        },
        "severity": 4,
        
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
    matches = detect_all_maintenance_keywords_from_issue(issue_description)
    recommendations = []

    for _, recommendation, *_ in matches:
        if recommendation not in recommendations:
            recommendations.append(recommendation)

    return recommendations


def get_rule_keywords(rule):
    return [keyword for _, keyword, _ in get_rule_keyword_entries(rule)]


def get_rule_keyword_entries(rule):
    return [
        (tense, keyword, TENSE_LIKELIHOOD[tense])
        for tense, tense_keywords in rule["keywords"].items()
        for keyword in tense_keywords
    ]


def calculate_issue_scores(issue_description):
    matches = detect_all_maintenance_keywords_from_issue(issue_description)

    if not matches:
        return None, None

    severity = max(match[4] for match in matches)
    likelihood = max(match[5] for match in matches)
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
        dot_column = 3 - score_to_grid_position(likelihood)

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


def detect_equipment_match_from_issue(issue_description):
    earliest_match = None

    for equipment, keywords in NON_ROTATING_EQUIPMENT_KEYWORDS.items():
        for keyword in keywords:
            match = re.search(rf"\b{re.escape(keyword)}\b", issue_description, re.IGNORECASE)
            if match and (earliest_match is None or match.start() < earliest_match[0]):
                earliest_match = (match.start(), equipment, match.group(0))

    if earliest_match is None:
        return None, None

    return earliest_match[1], earliest_match[2]


def detect_equipment_from_issue(issue_description):
    detected_equipment, _ = detect_equipment_match_from_issue(issue_description)
    return detected_equipment


def detect_all_equipment_from_issue(issue_description):
    matches = []

    for equipment, keywords in NON_ROTATING_EQUIPMENT_KEYWORDS.items():
        for keyword in keywords:
            match = re.search(rf"\b{re.escape(keyword)}\b", issue_description, re.IGNORECASE)
            if match:
                matches.append((match.start(), equipment, match.group(0)))
                break

    return sorted(matches)


def remove_equipment_phrases(issue_description):
    cleaned_description = issue_description

    equipment_keywords = [
        keyword
        for keywords in NON_ROTATING_EQUIPMENT_KEYWORDS.values()
        for keyword in keywords
    ]

    for keyword in sorted(equipment_keywords, key=len, reverse=True):
        cleaned_description = re.sub(
            rf"\b{re.escape(keyword)}\b",
            " ",
            cleaned_description,
            flags=re.IGNORECASE,
        )

    return cleaned_description


def detect_maintenance_keyword_from_issue(issue_description):
    matches = detect_all_maintenance_keywords_from_issue(issue_description)
    return matches[0][2] if matches else None


def find_keyword_matches(description, keyword_entries):
    matches = []
    occupied_spans = []

    for tense, keyword, likelihood in sorted(
        keyword_entries,
        key=lambda keyword_entry: len(keyword_entry[1]),
        reverse=True,
    ):
        for match in re.finditer(rf"\b{re.escape(keyword)}\b", description, re.IGNORECASE):
            span = match.span()
            overlaps_existing_match = any(
                span[0] < existing_span[1] and existing_span[0] < span[1]
                for existing_span in occupied_spans
            )

            if overlaps_existing_match:
                continue

            matches.append((match.start(), match.group(0), tense, likelihood))
            occupied_spans.append(span)

    return matches


def detect_all_maintenance_keywords_from_issue(issue_description):
    cleaned_description = remove_equipment_phrases(issue_description)
    matches = []

    for rule in MAINTENANCE_RULES:
        for match_start, matched_keyword, tense, likelihood in find_keyword_matches(
            cleaned_description,
            get_rule_keyword_entries(rule),
        ):
            matches.append(
                (
                    match_start,
                    rule["recommendation"],
                    matched_keyword,
                    tense,
                    rule["severity"],
                    likelihood,
                )
            )

    return sorted(matches)


def show_issue_description_preview(issue_description):
    if not issue_description.strip():
        return

    detected_equipment = detect_equipment_from_issue(issue_description)
    matched_keyword = detect_maintenance_keyword_from_issue(issue_description)
    st.markdown("**Filtered Issue Description**")

    if detected_equipment is None and matched_keyword is None:
        st.info("No non-rotating equipment or maintenance keyword detected.")
        return

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
            <div><strong>Non-Rotating Equipment:</strong> {html.escape(detected_equipment or "Not detected")}</div>
            <div><strong>Keyword Pulled:</strong> {html.escape(matched_keyword or "Not detected")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_ticket_split_suggestions(issue_description):
    if not issue_description.strip():
        return

    equipment_matches = detect_all_equipment_from_issue(issue_description)
    maintenance_matches = detect_all_maintenance_keywords_from_issue(issue_description)

    if len(equipment_matches) > 1:
        equipment_names = ", ".join(
            html.escape(equipment) for _, equipment, _ in equipment_matches
        )
        st.warning(
            "Consider creating separate tickets because multiple equipment items "
            f"were detected: {equipment_names}."
        )

    if len(maintenance_matches) > 1:
        keywords = ", ".join(
            html.escape(keyword) for _, _, keyword, *_ in maintenance_matches
        )
        st.warning(
            "Consider creating separate tickets because multiple maintenance "
            f"keywords were detected: {keywords}."
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

selected_equipment = (
    detected_equipment
    if equipment_type == "Non-Rotating Equipment" and detected_equipment
    else equipment_type
)

if equipment_type == "Non-Rotating Equipment":
    show_ticket_split_suggestions(issue_description)
    show_issue_description_preview(issue_description)

severity, likelihood = calculate_issue_scores(issue_description)
show_risk_grid(severity, likelihood)

risk_score = (
    round((severity + likelihood) / 20 * 100)
    if severity is not None and likelihood is not None
    else 0
)

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

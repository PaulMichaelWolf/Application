import streamlit as st
import streamlit.components.v1 as components
import html
import re
from textwrap import dedent


TENSE_LIKELIHOOD = {
    "present": 10,
    "future": 7,
    "conditional": 7,
    "past": 4,
    "negative": 0,
}

MAINTENANCE_RULES = [
    {
        "recommendation": "Isolate if needed.",
        "keywords": {
            "present": ["leak", "leaking", "seepage", "drip", "dripping"],
            "past": ["leaked", "was leaking", "seeped", "dripped"],
            "future": ["will leak", "may leak", "expected to leak"],
            "conditional": ["could leak", "could be leaking", "may be leaking"],
            "negative": [
                "not leaking",
                "no leak",
                "no leakage",
                "not dripping",
                "does not have leak",
                "does not have a leak",
                "does not have leakage",
                "doesn't have leak",
                "doesn't have a leak",
                "doesn't have leakage",
            ],
        },
        "severity": 10,
        
    },
    {
        "recommendation": "Perform thickness testing.",
        "keywords": {
            "present": ["corrosion", "rust", "pitting", "wall loss", "corroding"],
            "past": ["corroded", "rusted", "pitted", "lost wall thickness"],
            "future": ["will corrode", "may corrode", "expected to corrode"],
            "conditional": ["could corrode", "could be corroding", "may be corroding"],
            "negative": [
                "not corroding",
                "no corrosion",
                "no rust",
                "no pitting",
                "does not have corrosion",
                "does not have rust",
                "does not have pitting",
                "doesn't have corrosion",
                "doesn't have rust",
                "doesn't have pitting",
            ],
        },
        "severity": 4,
        
    },
    {
        "recommendation": "Inspect supports, alignment, bearings, fasteners, and operating conditions for abnormal vibration or looseness.",
        "keywords": {
            "present": ["vibration", "vibrating", "shaking", "noise", "rattling"],
            "past": ["vibrated", "was vibrating", "shook", "rattled", "made noise"],
            "future": ["will vibrate", "may vibrate", "expected to vibrate"],
            "conditional": ["could vibrate", "could be vibrating", "may be vibrating"],
            "negative": [
                "not vibrating",
                "no vibration",
                "not shaking",
                "no noise",
                "not rattling",
                "does not have vibration",
                "does not have noise",
                "does not have rattling",
                "doesn't have vibration",
                "doesn't have noise",
                "doesn't have rattling",
            ],
        },
        "severity": 7,
        
    },
    {
        "recommendation": "Check temperature readings, verify cooling or heat transfer performance, and inspect insulation or fouling.",
        "keywords": {
            "present": ["overheating", "hot", "temperature", "high temp", "high temperature"],
            "past": ["overheated", "was hot", "ran hot", "had high temperature"],
            "future": ["will overheat", "may overheat", "expected to overheat"],
            "conditional": ["could overheat", "could be overheating", "may be overheating"],
            "negative": [
                "not overheating",
                "not hot",
                "no high temperature",
                "normal temperature",
                "does not have high temperature",
                "does not have overheating",
                "doesn't have high temperature",
                "doesn't have overheating",
            ],
        },
        "severity": 7,
        
    },
    {
        "recommendation": "Verify pressure instruments, check valves and restrictions, and review operating limits before continued operation.",
        "keywords": {
            "present": ["pressure", "high pressure", "low pressure", "pressure drop"],
            "past": ["pressurized", "lost pressure", "dropped pressure", "had pressure drop"],
            "future": ["will pressurize", "may lose pressure", "expected pressure drop"],
            "conditional": ["could lose pressure", "could have pressure drop", "may be losing pressure"],
            "negative": [
                "no pressure issue",
                "no pressure drop",
                "not pressurized",
                "pressure normal",
                "does not have pressure issue",
                "does not have pressure drop",
                "doesn't have pressure issue",
                "doesn't have pressure drop",
            ],
        },
        "severity": 8,
        
    },
    {
        "recommendation": "Remove from service if structural integrity is uncertain, perform NDE inspection, and escalate for engineering review.",
        "keywords": {
            "present": ["crack", "cracking", "fracture", "fracturing"],
            "past": ["cracked", "fractured", "was cracked", "had fractured"],
            "future": ["will crack", "may crack", "expected to crack"],
            "conditional": ["could crack", "could be cracking", "may be cracking"],
            "negative": [
                "not cracked",
                "no crack",
                "no cracking",
                "no fracture",
                "does not have crack",
                "does not have a crack",
                "does not have cracking",
                "does not have fracture",
                "doesn't have crack",
                "doesn't have a crack",
                "doesn't have cracking",
                "doesn't have fracture",
            ],
        },
        "severity": 10,
        
    },
    {
        "recommendation": "Inspect for fouling or blockage, review flow performance, and schedule cleaning or flushing if confirmed.",
        "keywords": {
            "present": ["fouling", "plugging", "clogging", "blocked", "restriction"],
            "past": ["fouled", "plugged", "clogged", "was blocked", "restricted"],
            "future": ["will foul", "may plug", "expected to block"],
            "conditional": ["could clog", "could be clogged", "could block", "may be clogging"],
            "negative": [
                "not fouled",
                "not plugged",
                "not clogged",
                "not blocked",
                "no restriction",
                "does not have fouling",
                "does not have plugging",
                "does not have clogging",
                "does not have blockage",
                "does not have restriction",
                "doesn't have fouling",
                "doesn't have plugging",
                "doesn't have clogging",
                "doesn't have blockage",
                "doesn't have restriction",
            ],
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

    pulled_keyword_match = matches[0]
    if pulled_keyword_match[3] == "negative":
        return 0, pulled_keyword_match[5]

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
    risk_colors = [
        ["#ef3b2d", "#ef3b2d", "#ff8a00", "#f4e04d"],
        ["#ef3b2d", "#ff8a00", "#f4e04d", "#8bd646"],
        ["#ff8a00", "#f4e04d", "#8bd646", "#42b549"],
        ["#f4e04d", "#8bd646", "#42b549", "#42b549"],
    ]

    if severity is not None and likelihood is not None:
        dot_row = 3 - score_to_grid_position(severity)
        dot_column = 3 - score_to_grid_position(likelihood)

    rows = []
    for row in range(4):
        cells = []
        for column in range(4):
            dot_html = ""
            cell_color = risk_colors[row][column]
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
                        background: {cell_color};
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
        <div style="margin: 8px 0 4px;">
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


def display_keyword(keyword):
    return keyword[:1].upper() + keyword[1:] if keyword else keyword


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
            <div><strong>Keyword Pulled:</strong> {html.escape(display_keyword(matched_keyword) or "Not detected")}</div>
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
            html.escape(display_keyword(keyword))
            for _, _, keyword, *_ in maintenance_matches
        )
        st.warning(
            "Consider creating separate tickets because multiple maintenance "
            f"keywords were detected: {keywords}."
        )


def sync_likelihood_override(suggested_likelihood):
    default_likelihood = suggested_likelihood if suggested_likelihood is not None else 0

    if st.session_state.get("likelihood_suggestion") != default_likelihood:
        st.session_state["likelihood_suggestion"] = default_likelihood
        st.session_state["likelihood_override"] = default_likelihood


def sync_severity_override(suggested_severity):
    default_severity = suggested_severity if suggested_severity is not None else 0

    if st.session_state.get("severity_suggestion") != default_severity:
        st.session_state["severity_suggestion"] = default_severity
        st.session_state["severity_override"] = default_severity


def get_query_int(name):
    value = st.query_params.get(name)

    if isinstance(value, list):
        value = value[0] if value else None

    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None

    return max(0, min(10, parsed_value))


def show_likelihood_override_slider(suggested_likelihood):
    sync_likelihood_override(suggested_likelihood)
    current_likelihood = st.session_state.get("likelihood_override", 0)
    red_fill_start = (10 - current_likelihood) * 10
    st.markdown(
        f"""
        <style>
        .likelihood-value-label {{
            width: 224px;
            margin-left: 35px;
            position: relative;
            top: 15px;
            z-index: 5;
            pointer-events: none;
            text-align: center;
            color: #ffffff;
            font-size: 22px;
            font-weight: 700;
            line-height: 24px;
            margin-bottom: -24px;
            text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[data-testid="stSlider"] {{
                width: 235px;
                margin-left: 35px;
                margin-top: -50px;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[data-baseweb="slider"] > div {{
                height: 10px !important;
                min-height: 10px !important;
                max-height: 10px !important;
                background: linear-gradient(
                    to right,
                    #4b5563 0%,
                    #4b5563 {red_fill_start}%,
                    #ff4b4b {red_fill_start}%,
                    #ff4b4b 100%
                ) !important;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[data-baseweb="slider"] > div > div {{
                height: 10px !important;
                min-height: 10px !important;
                max-height: 10px !important;
                background: transparent !important;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"] {{
                width: 14px !important;
                min-width: 14px !important;
                max-width: 14px !important;
                height: 14px !important;
                min-height: 14px !important;
                max-height: 14px !important;
                background: transparent !important;
                border: 0 !important;
                box-shadow: none !important;
                outline: none !important;
                color: transparent !important;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"]:hover,
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"]:focus,
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"]:active {{
                width: 14px !important;
                min-width: 14px !important;
                max-width: 14px !important;
                height: 14px !important;
                min-height: 14px !important;
                max-height: 14px !important;
                transform: translate(-50%, -50%) !important;
                background: transparent !important;
                border: 0 !important;
                box-shadow: none !important;
                outline: none !important;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"]::before,
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[role="slider"]::after {{
                display: none !important;
        }}
        div[data-testid="stElementContainer"]:has(.likelihood-slider-marker)
            + div[data-testid="stElementContainer"] div[data-baseweb="slider"] div {{
                color: transparent !important;
        }}
        </style>
        <div class="likelihood-value-label">{current_likelihood}</div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<span class='likelihood-slider-marker'></span>", unsafe_allow_html=True)
    return st.select_slider(
        "User Override Likelihood Value (0-10)",
        options=list(range(10, -1, -1)),
        key="likelihood_override",
    )


def show_severity_override_slider(suggested_severity):
    sync_severity_override(suggested_severity)
    query_severity = get_query_int("severity_override")

    if query_severity is not None:
        st.session_state["severity_override"] = query_severity

    current_severity = st.session_state.get("severity_override", 0)
    red_fill_start = (10 - current_severity) * 10

    components.html(
        dedent(
            f"""
            <div class="severity-control">
                <div class="severity-label">User Override Severity Value (0-10)</div>
                <div
                    id="severity-track"
                    class="severity-track"
                    role="slider"
                    aria-label="User Override Severity Value"
                    aria-valuemin="0"
                    aria-valuemax="10"
                    aria-valuenow="{current_severity}"
                    tabindex="0"
                >
                    <div id="severity-fill" class="severity-fill"></div>
                    <div id="severity-value" class="severity-value">{current_severity}</div>
                </div>
            </div>

            <style>
            body {{
                margin: 0;
                background: transparent;
                color: #ffffff;
                font-family: sans-serif;
            }}
            .severity-control {{
                height: 400px;
                width: 190px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
            }}
            .severity-label {{
                width: 150px;
                transform: rotate(-90deg);
                transform-origin: center;
                white-space: nowrap;
                font-size: 14px;
                font-weight: 600;
                text-align: center;
            }}
            .severity-track {{
                position: relative;
                width: 36px;
                height: 235px;
                background: #4b5563;
                cursor: ns-resize;
                user-select: none;
                touch-action: none;
                overflow: hidden;
                outline: none;
            }}
            .severity-fill {{
                position: absolute;
                left: 0;
                right: 0;
                top: {red_fill_start}%;
                bottom: 0;
                background: #ff4b4b;
            }}
            .severity-value {{
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
                line-height: 1;
                text-shadow: 0 1px 3px rgba(0, 0, 0, 0.75);
                pointer-events: none;
                z-index: 2;
            }}
            </style>

            <script>
            const initialValue = {current_severity};
            let currentValue = initialValue;
            const track = document.getElementById("severity-track");
            const fill = document.getElementById("severity-fill");
            const valueLabel = document.getElementById("severity-value");

            function clamp(value, min, max) {{
                return Math.min(max, Math.max(min, value));
            }}

            function render(value) {{
                const fillStart = (10 - value) * 10;
                fill.style.top = `${{fillStart}}%`;
                valueLabel.textContent = value;
                track.setAttribute("aria-valuenow", value);
            }}

            function valueFromPointer(event) {{
                const rect = track.getBoundingClientRect();
                const position = clamp(event.clientY - rect.top, 0, rect.height);
                return Math.round(10 - (position / rect.height) * 10);
            }}

            function updateFromPointer(event) {{
                currentValue = valueFromPointer(event);
                render(currentValue);
            }}

            function commitValue() {{
                if (currentValue === initialValue) {{
                    return;
                }}

                const parentLocation = window.parent.location;
                const params = new URLSearchParams(parentLocation.search);
                params.set("severity_override", String(currentValue));
                parentLocation.href = `${{parentLocation.pathname}}?${{params.toString()}}${{parentLocation.hash}}`;
            }}

            track.addEventListener("pointerdown", (event) => {{
                track.setPointerCapture(event.pointerId);
                updateFromPointer(event);
            }});

            track.addEventListener("pointermove", (event) => {{
                if (event.buttons === 1) {{
                    updateFromPointer(event);
                }}
            }});

            track.addEventListener("pointerup", () => {{
                commitValue();
            }});

            track.addEventListener("keydown", (event) => {{
                if (event.key === "ArrowUp" || event.key === "ArrowRight") {{
                    currentValue = clamp(currentValue + 1, 0, 10);
                    render(currentValue);
                    commitValue();
                    event.preventDefault();
                }}

                if (event.key === "ArrowDown" || event.key === "ArrowLeft") {{
                    currentValue = clamp(currentValue - 1, 0, 10);
                    render(currentValue);
                    commitValue();
                    event.preventDefault();
                }}
            }});
            </script>
            """
        ),
        height=310,
    )
    return current_severity


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

issue_description = ""
detected_equipment = None
severity = None
likelihood = None

if equipment_type == "Non-Rotating Equipment":
    st.markdown(
        """
        <style>
        div[data-testid="stElementContainer"]:has(.issue-description-marker)
            + div[data-testid="stElementContainer"] textarea {
                height: 80px !important;
                min-height: 80px !important;
                max-height: 80px !important;
                resize: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<span class='issue-description-marker'></span>", unsafe_allow_html=True)
    issue_description = st.text_area("Issue Description", height=80)
    detected_equipment = detect_equipment_from_issue(issue_description)

selected_equipment = (
    detected_equipment
    if equipment_type == "Non-Rotating Equipment" and detected_equipment
    else equipment_type
)

if equipment_type == "Non-Rotating Equipment":
    show_ticket_split_suggestions(issue_description)
    show_issue_description_preview(issue_description)
    suggested_severity, suggested_likelihood = calculate_issue_scores(issue_description)
    matrix_column, severity_column = st.columns([3, 2])

    with matrix_column:
        risk_grid = st.empty()
        likelihood = show_likelihood_override_slider(suggested_likelihood)

    with severity_column:
        severity = show_severity_override_slider(suggested_severity)

    if suggested_severity is not None or suggested_likelihood is not None:
        with risk_grid:
            show_risk_grid(severity, likelihood)
    else:
        with risk_grid:
            show_risk_grid(None, None)

risk_score = (
    round((severity + likelihood) / 20 * 100)
    if severity is not None and likelihood is not None
    else 0
)

if equipment_type == "Non-Rotating Equipment" and st.button("Generate Maintenance Recommendation"):
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

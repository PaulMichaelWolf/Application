import streamlit as st

st.title("AI Maintenance Planner")

equipment_type = st.selectbox(
    "Equipment Type",
    [
        "Rotating Equipment",
        "Non-Rotating Equipment",
    ],
)
issue_description = st.text_area("Issue Description")

severity = st.slider("Severity", 1, 10, 5)
likelihood = st.slider("Likelihood", 1, 10, 5)
business_impact = st.slider("Business Impact", 1, 10, 5)

risk_score = round((severity + likelihood + business_impact) / 30 * 100)

if st.button("Generate Maintenance Recommendation"):
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

    st.subheader("Suggested Work Order")
    st.write(
        f"Investigate issue on {equipment_type}. "
        f"Reported condition: {issue_description}. "
        f"Priority level: {priority}. Recommended action: {recommendation}"
    )

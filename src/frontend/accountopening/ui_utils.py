import streamlit as st
import datetime



def subway_sidebar(active_phase_index: int, PHASES):
    """
    Displays each phase in a vertical list, 
    making the (circle + label) effectively clickable via a button.
    """
    # CSS to style the circle and color states
    st.markdown(
        """
        <style>
        .circle-row {
            display: flex; 
            align-items: center; 
            margin-bottom: 0.5rem;
        }
        .step-circle {
            width: 36px; 
            height: 36px; 
            border-radius: 50%;
            background-color: #555; /* default upcoming color */
            border: 3px solid #999;
            color: #fff;
            font-weight: bold;
            display: flex; 
            justify-content: center; 
            align-items: center;
            margin-right: 8px;
        }
        /* COMPLETED */
        .completed {
            background-color: #4CAF50 !important;
            border-color: #4CAF50 !important;
        }
        /* ACTIVE */
        .active {
            background-color: #007BFF !important;
            border-color: #007BFF !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Build a row for each phase
    for i, phase_name in enumerate(PHASES):
        if i < active_phase_index:
            circle_class = "step-circle completed"
        elif i == active_phase_index:
            circle_class = "step-circle active"
        else:
            circle_class = "step-circle"

        col_circle, col_label = st.columns([1, 5], gap="small")
        with col_circle:
            # The circle alone, with appropriate coloring
            st.markdown(
                f"<div class='circle-row'><div class='{circle_class}'>{i+1}</div></div>",
                unsafe_allow_html=True
            )
        with col_label:
            # The clickable button
            if st.button(phase_name, key=f"phase_button_{i}"):
                st.session_state.active_step = i
                st.rerun()



def show_banner(prospect: dict):
    """
    Renders a banner on top of the detail view with:
      1) A risk-level 
      2) A compliance status section using a standard resizable text area.
    """
    col_risk, col_logs = st.columns([1, 6], gap="small")
    with col_risk:
        st.write("")
        # 1) Determine the icon color for risk_level
        risk_level = prospect.get("risk_level", "").lower()
        st.metric("Risk", risk_level, delta=risk_level, delta_color="normal", help=None, label_visibility="visible")
       
    with col_logs:
        # 2) Retrieve the onboarding array
        onboarding_entries = prospect.get("onboarding", [])
        onboarding_text = "\n".join([
            f"{entry.get('timestamp', 'N/A')} – {entry.get('step', '')} – {entry.get('action', '')}"
            for entry in onboarding_entries
        ]) if onboarding_entries else "No onboarding history available."

    
        st.markdown("#### Compliance Status")
        onboarding_text = st.text_area("Onboarding History", onboarding_text, height=100)


   

    

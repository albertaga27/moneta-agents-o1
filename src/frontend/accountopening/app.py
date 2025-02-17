import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

API_URL = "http://localhost:8000/prospects"
UPDATE_PROSPECT_URL = "http://localhost:8000/update_prospect" 

PHASES = [
    "KYC Information",
    "Source of Wealth",
    "Documents AI Extraction",
    "Name Screening",
    "Risk Profile",
    "Compliance & Risk Assessment",
    "First Line of Defence",
    "Check Documents",
    "Compliance Report",
    "Second line of defence",
    "Account opening"
]

def fetch_prospects():
    payload = {"user_id": "default_user"}  
    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, str):
            data = json.loads(data)
        return data if data else []
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching prospects: {e}")
        return []


def map_status_to_phase(status: str) -> int:
    """
    Returns a 0-based index for the active phase based on 'status'.
    Modify logic as needed.
    """
    status_map = {
        "KYC Information": 0,
        "Source of Wealth": 1,
        "Documents AI Extraction": 2,
        "Name Screening": 3,
        "Risk Profile": 4,
        "Compliance & Risk Assessment": 5,
        "First Line of Defence": 6,
        "Check Documents": 7,
        "Compliance Report": 8,
        "Second line of defence": 9,
        "Account opening": 10
    }
    # Example partial logic
    if "first line of defence" in status.lower():
        return 6
    for phrase, idx in status_map.items():
        if phrase.lower() in status.lower():
            return idx
    return 0

def subway_sidebar(active_phase_index: int):
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
                st.experimental_rerun()

def show_form_for_step(step_index: int, prospect):
    """
    Displays a different form depending on the current step (active_step).
    For brevity, we only define the "prospect details" in step 0;
    subsequent steps are placeholders.
    """
    if step_index == 0:
        st.subheader("Step 1: KYC Information")
        with st.form("prospect_form"):
            first_name = st.text_input("First Name", prospect.get("firstName", ""))
            last_name = st.text_input("Last Name", prospect.get("lastName", ""))

            try:
                dob = pd.to_datetime(prospect.get("dateOfBirth", "2000-01-01"))
            except:
                dob = datetime(2000, 1, 1)
            date_of_birth = st.date_input("Date of Birth", value=dob)

            nationality = st.text_input("Nationality", prospect.get("nationality", ""))
            status_val = st.text_input("Status", prospect.get("status", ""))

            contact_details = prospect.get("contactDetails", {})
            email = st.text_input("Email", contact_details.get("email", ""))
            phone = st.text_input("Phone", contact_details.get("phone", ""))

            pep_status = st.checkbox("PEP Status", value=prospect.get("pep_status", False))
            risk_level = st.text_input("Risk Level", prospect.get("risk_level", "Low"))
            risk_score = st.number_input("Risk Score", value=prospect.get("risk_score", 1))

            if st.form_submit_button("Save Changes"):
                # Update in session or call an API
                updated_p = dict(prospect)
                updated_p["firstName"] = first_name
                updated_p["lastName"] = last_name
                updated_p["dateOfBirth"] = str(date_of_birth)
                updated_p["nationality"] = nationality
                updated_p["status"] = status_val
                updated_p["pep_status"] = pep_status
                updated_p["risk_level"] = risk_level
                updated_p["risk_score"] = risk_score
                updated_p["contactDetails"] = {"email": email, "phone": phone}
                # 1) Update in Streamlit session state
                st.session_state.selected_prospect = updated_p

                # 2) Real API call to persist changes
                api_response = update_prospect_in_backend(updated_p)
                if api_response:
                    # 3) Store the updated doc from the server back into local state
                    st.session_state.selected_prospect = api_response
                    st.success("Prospect updated in backend successfully!")
                else:
                    st.error("Backend update failed. See logs for details.")

    elif step_index == 1:
        st.subheader("Step 2: Source of Wealth")
        
        # The possible SoW options
        sow_options = ["Employment", "Business income", "Inheritance", "Donations"]

        with st.form("documents_ai_form"):
            st.write("**Select Declared Source of Wealth**")
            selected_sow = st.multiselect(
                "Choose all that apply:",
                options=sow_options,
                default=prospect.get("declared_source_of_wealth", "")
                
            )

            submitted_sow = st.form_submit_button("Save Changes")
            if submitted_sow:
                updated_p = dict(prospect)
                updated_p["declared_source_of_wealth"] = selected_sow

                st.session_state.selected_prospect = updated_p
                api_response = update_prospect_in_backend(updated_p)
                if api_response:
                    st.success("Source of Wealth updated in backend!")
                    st.session_state.selected_prospect = api_response
                else:
                    st.error("Backend SoW update failed.")

    elif step_index == 2:
        st.subheader("Step 3: Documents AI Extraction")
        
        # Retrieve any existing declared_source_of_wealth
        existing_sow = prospect.get("declared_source_of_wealth", [])
        if not isinstance(existing_sow, list):
            existing_sow = []

        documents_provided = prospect.get("documents_provided", [])
        existing_passport = documents_provided[0] if len(documents_provided) > 0 else ""
        existing_por = documents_provided[1] if len(documents_provided) > 1 else ""

        # Create a form with columns
        with st.form("documents_ai_form"):

            col_left, col_right = st.columns(2, gap="large")

            with col_left:
                # 1) SOW multi-select
                st.write("**Declared Source of Wealth**")
                selected_sow = st.text(existing_sow)
                st.divider()

                # 2) Passport input (text input, e.g. passport number or description)
                st.write("**Passport**")
                passport_value = st.text(existing_passport)
                st.divider()

                # 3) Proof of Residency input
                st.write("**Proof of Address**")
                por_value = st.text_input(existing_por)
                st.divider()

            with col_right:
                st.write("**Upload Documents**")

                # For each left-field, we have a corresponding file uploader on the right
                sow_file = st.file_uploader("Source of Wealth Document", type=["pdf", "jpg", "png"])
                passport_file = st.file_uploader("Passport Document", type=["pdf", "jpg", "png"])
                por_file = st.file_uploader("Proof of Residency Document", type=["pdf", "jpg", "png"])

            # Submit button
            submitted = st.form_submit_button("Save Changes")
            if submitted:
                # 1) Copy the old prospect data
                updated_p = dict(prospect)

                # 2) Update fields from the form
                updated_p["passport"] = passport_value
                updated_p["proof_of_residency"] = por_value

                # TODO need to store these file(s) or upload them somewhere
                # e.g. updated_p["passport_file"] = passport_file.getvalue()  # as raw bytes
                #      updated_p["por_file"] = por_file.getvalue()
                # Or you might do a separate API call for each file

                # 3) Update local session state
                st.session_state.selected_prospect = updated_p

                # 4) API call to update in the backend (example)
                api_response = update_prospect_in_backend(updated_p)
                if api_response:
                    # If your endpoint returns the updated doc, store it
                    st.session_state.selected_prospect = api_response
                    st.success("Documents updated in backend!")
                else:
                    st.error("Backend update failed.")

    else:
        st.subheader(f"Step {step_index+1}: {PHASES[step_index]}")
        st.info("Placeholder for that step's form here.")

    if st.button("Back to List"):
        st.session_state.view = "list"
        st.experimental_rerun()

def show_prospect_list():
    prospects = st.session_state.prospects
    st.markdown("<h2>Prospects Table</h2>", unsafe_allow_html=True)
    if not prospects:
        st.info("No prospects found from the API.")
        return

    # ... dark themed table code from before ...
    hdr_cols = st.columns([2, 3, 2, 2, 2])
    hdr_cols[0].markdown("**Client ID**")
    hdr_cols[1].markdown("**Full Name**")
    hdr_cols[2].markdown("**DOB**")
    hdr_cols[3].markdown("**Status**")
    hdr_cols[4].markdown("**Action**")

    for i, p in enumerate(prospects):
        row_cols = st.columns([2, 3, 2, 2, 2])
        row_cols[0].write(p.get('clientID', ''))
        row_cols[1].write(p.get('fullName', ''))
        row_cols[2].write(p.get('dateOfBirth', ''))
        row_cols[3].write(p.get('status', ''))

        if row_cols[4].button("Show Details", key=f"show_{i}"):
            st.session_state.selected_prospect = p
            st.session_state.view = "detail"
            st.experimental_rerun()

def show_prospect_details():
    """
    Left column: subway steps (clickable).
    Right column: the form for the active step.
    """
    p = st.session_state.selected_prospect
    if not p:
        st.warning("No prospect selected.")
        return

    # Set the active step if it doesn't exist
    if "active_step" not in st.session_state:
        st.session_state.active_step = map_status_to_phase(p.get("status", ""))

    # Two columns
    col_left, col_right = st.columns([2, 5], gap="large")

    # Left: clickable steps
    with col_left:
        st.write("### Process Steps")
        subway_sidebar(st.session_state.active_step)

    # Right: the relevant form
    with col_right:
        show_form_for_step(st.session_state.active_step, p)


def update_prospect_in_backend(prospect_data: dict, user_id: str = "default_user"):
    """
    Calls the FastAPI endpoint /update_prospect to update the prospect data in Cosmos DB.
    Returns the response data 
    """
    payload = {
        "user_id": user_id,
        # The backend expects prospect_data as a JSON string
        "prospect_data": json.dumps(prospect_data)
    }
    try:
        resp = requests.post(UPDATE_PROSPECT_URL, json=payload)
        resp.raise_for_status()
        # The endpoint returns a JSON string or None
        data = resp.json()
        # If data is a JSON string, parse it
        if isinstance(data, str):
            data = json.loads(data)
        return data  
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to update prospect in backend: {e}")
        return None


def main():
    st.set_page_config(page_title="Prospects Dashboard", layout="wide")
    st.title("Prospects Dashboard")

    if "view" not in st.session_state:
        st.session_state.view = "list"

    if "prospects" not in st.session_state:
        st.session_state.prospects = fetch_prospects()

    if "selected_prospect" not in st.session_state:
        st.session_state.selected_prospect = None

    # Routing
    if st.session_state.view == "list":
        show_prospect_list()
    else:
        show_prospect_details()

if __name__ == "__main__":
    main()

import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

from ui_utils import *

API_URL = "http://localhost:8000/prospects"
UPDATE_PROSPECT_URL = "http://localhost:8000/update_prospect" 
RUN_AGENTS_URL = "http://localhost:8000/run_ao_agents" 

PHASES = [
    "KYC Information",
    "Source of Wealth",
    "Documents AI Extraction",
    "Name Screening",
    "Risk Profile",
    "Compliance & Risk Assessment",
    "First Line of Defence",
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
        "Compliance Report": 7,
        "Second line of defence": 8,
        "Account opening": 9
    }
    # Example partial logic
    if "first line of defence" in status.lower():
        return 6
    for phrase, idx in status_map.items():
        if phrase.lower() in status.lower():
            return idx
    return 0



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
        sow_options = ["Employment", "Business income", "Inheritance", "Donations", ""]

        with st.form("sow_form"):
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

                # 2) Update fields from the form (mocked)
                updated_p["documents_provided"] = ['passport','proof_of_address']

                # TODO need to store these file(s) or upload them somewhere and process the extraction
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

    elif step_index == 3:
        st.subheader("Step 3: Name Screening")
    
        st.text(f"Client Names: {prospect.get("firstName")} {prospect.get("lastName")}")

        st.title("Screening result:")
        if prospect["name_screening_result"] == "None":
            st.warning('Name checks not performed yet!', icon="⚠️")
        else:
            st.success(prospect['name_screening_result'], icon="✅")
            
    elif step_index == 4:
        st.subheader("Step 4: Risk Profile")
    
        st.title("Evaluation:")
        if prospect["risk_level"] == "":
            st.warning('Risk profile not evaluated yet!', icon="⚠️")
        else:
            st.metric("Risk Level", prospect['risk_level'], delta=prospect['risk_level'], delta_color="normal", help=None, label_visibility="visible",  border=True)
            st.metric("Risk Score", prospect['risk_score'], delta=prospect['risk_score'], delta_color="normal", help=None, label_visibility="visible",  border=True)
    
    elif step_index == 5:
        st.subheader("Step 5: Compliance & Risk Assessment")
    
        st.title("First evaluation:")
        st.text(f"Status: {prospect['status']}")
        st.text(f"Flagged issues: {prospect['compliance_flags']}")

    elif step_index == 6:
        st.subheader("Step 6: First line of defence (Back-office)")
    
        st.title("Back-office review:")
        st.text_area("Reviewer comments:")
        approved = st.button("Approve", type="primary", icon="👍",use_container_width=False)
        rejected = st.button("Reject", type="tertiary", icon="👎",use_container_width=False)
        if approved:
            updated_p = dict(prospect)
            updated_p["status"] = "First line of defence: approved"

            st.session_state.selected_prospect = updated_p
            api_response = update_prospect_in_backend(updated_p)
            if api_response:
                st.success("Back-office approval updated in backend!")
                st.session_state.selected_prospect = api_response
            else:
                st.error("Back-office approval update failed.")

        #TODO rejection updates in backend


    else:
        st.subheader(f"Step {step_index+1}: {PHASES[step_index]}")
        st.info("Placeholder for that step's form here.")
       
       #TODO
        # "Compliance Report": 7,
        # "Second line of defence": 8,
        # "Account opening": 9

    # Two columns for buttons actions
    col_left, col_right = st.columns([4, 2], gap="large")

    with col_left:
        # Run agents button
        if st.button("Run Agents", type="secondary", icon=":material/restart_alt:",use_container_width=False):
        
            updated_p = st.session_state.selected_prospect

            with st.spinner("Running agentic workflow in the backend...", show_time=False):
                # API call to run agentic process in the backend
                api_response = run_agents_in_backend(updated_p)
                if api_response:
                    # If your endpoint returns the updated doc, store it
                    st.session_state.selected_prospect = api_response
                    st.success("Agentic workflow ran succesfully!")
                    st.rerun()
                else:
                    st.error("Agentic workflow failed.")

    with col_right:
        if st.button("Back to List", type="tertiary", icon=":material/list:",use_container_width=False):
            st.session_state.view = "list"
            st.rerun()

def show_prospect_list():
    prospects = st.session_state.prospects
    st.markdown("<h2>Prospects</h2>", unsafe_allow_html=True)
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
            st.rerun()
    # New button at the bottom for creating a new prospect
    if st.button("Create prospect", key="create_prospect"):
        st.session_state.view = "create"
        st.rerun()

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
        subway_sidebar(st.session_state.active_step, PHASES)

    # Right: the relevant form
    with col_right:
        show_banner(p)
        show_form_for_step(st.session_state.active_step, p)

def show_create_prospect_form():
    st.subheader("New Prospect")
    # Switch between manual entry and document upload
    creation_mode = st.radio("Select Creation Mode:", options=["Enter manually", "Upload documents"])
    if creation_mode == "Enter manually":
        st.markdown("### Enter Basic KYC Information")
        with st.form("new_prospect_manual_form"):
            first_name = st.text_input("First Name")
            last_name = st.text_input("Last Name")
            date_of_birth = st.date_input("Date of Birth")
            nationality = st.text_input("Nationality")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            if st.form_submit_button("Create Prospect"):
                new_prospect = {
                    "clientID": f"PRONEW{int(datetime.utcnow().timestamp())}",
                    "firstName": first_name,
                    "lastName": last_name,
                    "dateOfBirth": str(date_of_birth),
                    "nationality": nationality,
                    "contactDetails": {"email": email, "phone": phone},
                    "status": "New prospect - KYC pending",
                    "fullName": f"{first_name} {last_name}"
                }
                # Optionally, call an API to persist this new prospect
                st.session_state.prospects.append(new_prospect)
                st.success("New prospect created successfully!")
                st.session_state.view = "list"
                st.rerun()
    elif creation_mode == "Upload documents":
        st.markdown("### Upload Documents for New Prospect")
        with st.form("new_prospect_upload_form"):
            st.info("This feature is under construction. Please upload the necessary documents.")
            upload_files = st.file_uploader("Upload Documents", type=["pdf", "jpg", "png"], accept_multiple_files=True)
            if st.form_submit_button("Submit Documents"):
                # Process the uploaded files and create a new prospect record accordingly
                st.success("Documents submitted successfully. (Feature under construction)")
                st.session_state.view = "list"
                st.rerun()
    if st.button("Back to List", type="tertiary", icon=":material/list:",use_container_width=False):
            st.session_state.view = "list"
            st.rerun()


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


def run_agents_in_backend(prospect_data: dict, user_id: str = "default_user"):
    """
    Calls the FastAPI endpoint /run_ao_agents to update the status of the prospect.
    Returns the response data 
    """
    payload = {
        "user_id": user_id,
        # The backend expects prospect_data as a JSON string
        "prospect_data": json.dumps(prospect_data)
    }
    try:
        resp = requests.post(RUN_AGENTS_URL, json=payload)
        resp.raise_for_status()
        # The endpoint returns a JSON string or None
        data = resp.json()
        # If data is a JSON string, parse it
        if isinstance(data, str):
            data = json.loads(data)
        return data  
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to run ao agentic process in backend: {e}")
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
    elif st.session_state.view == "detail":
        show_prospect_details()
    elif st.session_state.view == "create":
        show_create_prospect_form()

if __name__ == "__main__":
    main()

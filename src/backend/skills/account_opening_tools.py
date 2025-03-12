import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import random

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from crm_store import CRMStore


def create_prospect(first_name: str, last_name: str, dob: str, nationality: str, referral_source: str) -> Dict[str, Any]:
    """
    Create a prospect in the CRM with initial mimimal information
    
    """
    new_id = f"PROSP{10 + random.randint(1000, 9999)}"

    new_prospect = {
        "clientID": new_id,
        "firstName": first_name,
        "lastName": last_name,
        "referral_source": referral_source,
        "id": new_id,  
        "fullName": first_name+" "+last_name,  
        "dateOfBirth": dob,  
        "nationality": nationality,  
        "contactDetails": {  
            "email": "",  
            "phone": ""  
        },  
        "status": "new",
        "onboarding" : [],
        "kyc_reviews" : [],
        "pep_status": False,
        "risk_level" : "",
        "risk_score" : 0,
        "documents_provided": [],
        "name_screening_result": "None",
        "investmentProfile": {  
            "riskProfile": "",  
            "investmentObjectives": "",  
            "investmentHorizon": ""  
        },
        "declared_source_of_wealth" : ""
    }
    
    try:
        # Example of how to pull from environment variables:
        cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT") or ""
        crm_database_name = os.getenv("COSMOSDB_DATABASE_NAME") or ""
        crm_container_name = os.getenv("COSMOSDB_CONTAINER_CLIENT_NAME") or ""
        key=DefaultAzureCredential()
        
        crm_db = CRMStore(
             url=cosmosdb_endpoint,
             key=key,
             database_name=crm_database_name,
             container_name=crm_container_name
        )

        response = crm_db.create_customer_profile(new_prospect)
        return json.dumps(response) if response else None
    
    except Exception as e:
        logging.error(f"Error in create_prospect: {str(e)}")
        return json.dumps({"error": f"create_prospect failed with error: {str(e)}"})
   


def fetch_prospect_details(full_name: str) -> str:
    """
    Load prospect data from the CRM using the given full name.
    
    """
    try:
        # Example of how to pull from environment variables:
        cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT") or ""
        crm_database_name = os.getenv("COSMOSDB_DATABASE_NAME") or ""
        crm_container_name = os.getenv("COSMOSDB_CONTAINER_CLIENT_NAME") or ""
        key=DefaultAzureCredential()
        
        crm_db = CRMStore(
             url=cosmosdb_endpoint,
             key=key,
             database_name=crm_database_name,
             container_name=crm_container_name
        )

        response = crm_db.get_customer_profile_by_full_name(full_name)
        return json.dumps(response) if response else None

    except Exception as e:
        logging.error(f"Error in load_from_crm_by_client_fullname: {str(e)}")
        return json.dumps({"error": f"load_from_crm_by_client_fullname failed with error: {str(e)}"})

  
def fetch_prospect_details_by_id(clientID: str) -> str:
    """
    Load prospect data from the CRM using the clientID.
    
    """
    try:
        # Example of how to pull from environment variables:
        cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT") or ""
        crm_database_name = os.getenv("COSMOSDB_DATABASE_NAME") or ""
        crm_container_name = os.getenv("COSMOSDB_CONTAINER_CLIENT_NAME") or ""
        key=DefaultAzureCredential()
        
        crm_db = CRMStore(
             url=cosmosdb_endpoint,
             key=key,
             database_name=crm_database_name,
             container_name=crm_container_name
        )

        response = crm_db.get_customer_profile_by_client_id(clientID)
        return json.dumps(response) if response else None

    except Exception as e:
        logging.error(f"Error in load_from_crm_by_client_fullname: {str(e)}")
        return json.dumps({"error": f"load_from_crm_by_client_fullname failed with error: {str(e)}"})
  
  

def update_prospect_details(client_id: str, prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update prospect data in the CRM.
    
    """
    try:
        # Example of how to pull from environment variables:
        cosmosdb_endpoint = os.getenv("COSMOSDB_ENDPOINT") or ""
        crm_database_name = os.getenv("COSMOSDB_DATABASE_NAME") or ""
        crm_container_name = os.getenv("COSMOSDB_CONTAINER_CLIENT_NAME") or ""
        key=DefaultAzureCredential()
        
        crm_db = CRMStore(
             url=cosmosdb_endpoint,
             key=key,
             database_name=crm_database_name,
             container_name=crm_container_name
        )

        updated_prospect = crm_db.update_customer_profile(client_id, prospect_data)
        return updated_prospect if updated_prospect else None

    except Exception as e:
        logging.error(f"Error in update_prospect_details: {str(e)}")
        return json.dumps({"error": f"update_prospect_details failed with error: {str(e)}"})
    

def collect_kyc_info(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    KYC Information Collection
    - Checks if mandatory fields are present.
    """
    mandatory_fields = ["firstName", "lastName", "dateOfBirth", "nationality"]
    missing_fields = [field for field in mandatory_fields if field not in prospect_data]
    
    if missing_fields:
        kyc_status = f"KYC incomplete. Missing fields: {missing_fields}"
        action_description = f"Client KYC data is incomplete. Missing: {', '.join(missing_fields)}."
    else:
        kyc_status = "KYC data collected successfully"
        action_description = "Client KYC data successfully verified and collected."

    try:
      # Update client data status
      prospect_data['status'] = kyc_status

      # Add onboarding log entry
      
      onboarding_entry = {
          "timestamp": datetime.now().isoformat(),
          "step": kyc_status,
          "action": action_description
      }
      
      if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
      prospect_data["onboarding"].append(onboarding_entry)

      # Persist updated prospect data
      update_prospect_details(prospect_data['clientID'], prospect_data)

    except Exception as e:
      logging.error('error', f"Error in collect_kyc_info: {e}")

    return {
        "status": kyc_status,
        "onboarding": prospect_data["onboarding"]
    }


def collect_sow_info(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Source of Wealth (SOW) Information Collection
    - Accepts a declared source of wealth.
    """
    #mocked fixed response
    sow = prospect_data.get("declared_source_of_wealth", "Employment")

    try:
      #update client data status
      prospect_data['status'] = "SOW information captured"

      # Add onboarding log entry
      onboarding_entry = {
          "timestamp": datetime.now().isoformat(),
          "step": prospect_data['status'],
          "action": f"SOW information captured: {prospect_data.get("declared_source_of_wealth", "")}"
      }
      
      if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
      prospect_data["onboarding"].append(onboarding_entry)

      update_prospect_details(prospect_data['clientID'], prospect_data)

    except Exception as e:
      logging.error('error', f"Error in collect_sow_info: {e}")

    return {
        "onboarding": prospect_data["onboarding"],
        "status": "SOW information captured"
    }

def perform_data_management_ai_extraction(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data Management & AI Extraction
    - Mock logic that pretends to parse attached documents (PDFs, images, etc.) to enrich the KYC.
    """
    # Simulate a minimal list of required documents.
    required_docs = ["passport", "proof_of_address"]
    provided_docs = prospect_data.get("documents_provided", [])
    
    # Identify which required documents are missing
    missing_docs = [doc for doc in required_docs if doc not in provided_docs]
    
    # Mock extracting data from each document (in practice, this could leverage an OCR/AI pipeline).
    extracted_data_points = {}
    for doc in provided_docs:
        if doc == "passport":
            extracted_data_points["passport_number"] = f"P-{random.randint(100000, 999999)}"
            extracted_data_points["passport_issue_date"] = "2020-01-01"
            extracted_data_points["passport_expiry_date"] = "2030-01-01"
        elif doc == "proof_of_address":
            extracted_data_points["address_verified"] = True
        elif doc == "corporate_doc":
            extracted_data_points["corporation_name"] = prospect_data.get("corporation_name", "N/A")
            extracted_data_points["incorporation_year"] = prospect_data.get("incorporation_year", "N/A")
    
    #update client data status
    prospect_data['status'] = "Documents AI extraction completed"

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": "Documents AI extraction completed"
    }
    
    if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "extracted_fields": extracted_data_points,
        "status": "Documents AI extraction completed"
    }

def perform_name_screening(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Name Screening & Exception Handling
    - Simulates if the prospect name appears on a watchlist or sanctions list.
    """
    possible_outcomes = ["No match", "Potential match", "Sanctions list match"]
    screening_outcome = random.choices(
        possible_outcomes,
        weights=[0.8, 0.15, 0.05],  # Weighted to produce 'No match' more often
        k=1
    )[0]
    
    if screening_outcome == "No match":
        screening_status = "Name screening: Cleared"
    elif screening_outcome == "Potential match":
        screening_status = "Name screening: Further review required"
    else:
        screening_status = "Name appears on sanctions list! High alert."

    #update client data status
    prospect_data['status'] = screening_status
    prospect_data['name_screening_result'] = screening_outcome

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": prospect_data['status']+f": Screening outcome: {screening_outcome}"
    }
    
    if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)
    
    return {
        "name_screening_result": screening_outcome,
        "status": screening_status
    }

def create_client_profile(prospect_data: Dict[str, Any], name_screening_result: str) -> Dict[str, Any]:
    """
    Client Profile Risk Evaluation
    - Calculate a simple risk score/level based on name screening and nationality.
    """
    screening_outcome = name_screening_result
    risk_score = 0
    
    # Simple weighting: if screening found a potential or sanctions match
    if screening_outcome == "Potential match":
        risk_score += 3
    elif screening_outcome == "Sanctions list match":
        risk_score += 10
    
    # Example: certain high-risk nationalities or jurisdictions
    high_risk_nationalities = ["IR", "RU", "KP", "SY"]
    if prospect_data.get("nationality") in high_risk_nationalities:
        risk_score += 5
    
    # Random minor variation
    risk_score += random.randint(0, 3)
    
    if risk_score <= 3:
        risk_level = "Low"
    elif risk_score <= 7:
        risk_level = "Medium"
    else:
        risk_level = "High"
    
    #update client data status
    prospect_data['risk_level'] = risk_level
    prospect_data['risk_score'] = risk_score
    prospect_data['status'] = "Client risk profile assessed"

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": prospect_data['status']+f": Risk level is {risk_level}"
    }
    
    if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "status": "Client risk profile assessed"
    }

def perform_compliance_risk_assessment(prospect_data: Dict[str, Any] ) -> Dict[str, Any]:
    """
    Compliance & Risk Assessment
    - If risk is 'High' or there's a sanctions list match, flag EDD.
    """

    flagged_issues = []
    
    try:
      risk_level = prospect_data['risk_level']
      screening_outcome =  prospect_data['name_screening_result']
      
      if risk_level == "High" or screening_outcome == "Sanctions list match":
          compliance_status = "High-risk client. Further Enhanced Due Diligence required."
          flagged_issues.append(compliance_status)
      else:
          compliance_status = "First KYC checks passed."
      
      
      #update client data status
      prospect_data['status'] = compliance_status
      prospect_data['compliance_flags'] = flagged_issues

      # Add onboarding log entry
      onboarding_entry = {
          "timestamp": datetime.now().isoformat(),
          "step": prospect_data['status'],
          "action": prospect_data['status']+f": Compliance status is {compliance_status}"
      }
      
      if "onboarding" not in prospect_data:
        prospect_data["onboarding"] = []
      prospect_data["onboarding"].append(onboarding_entry)
      update_prospect_details(prospect_data['clientID'], prospect_data)

    except Exception as e:
      logging.error('error', f"Error in perform_compliance_risk_assessment: {e}")

    return {
        "overall_status": compliance_status,
        "flagged_issues": flagged_issues
    }

#3.1 Human interface case assigned for go/no-go (first line of defence)
def assign_first_line_of_defence(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assign the case with data and status so far to a Human interface for go/no-go (first line of defence).

    """
    #TODO external process logic (human case review etc.)
    
    try:
      prospect_loaded = fetch_prospect_details_by_id(prospect_data["clientID"])  
      prospect = json.loads(prospect_loaded)

      #update client data status
      prospect['status'] = "Assigned to human review (first line of defence)"
      
      # Add onboarding log entry
      onboarding_entry = {
          "timestamp": datetime.now().isoformat(),
          "step": prospect['status'],
          "action": prospect['status']+f": Waiting for first compliance approval"
      }
      
      if "onboarding" not in prospect:
        prospect["onboarding"] = []
      prospect["onboarding"].append(onboarding_entry)
      update_prospect_details(prospect['clientID'], prospect)
    
    except Exception as e:
        logging.error('error', f"Error in assign_first_line_of_defence: {e}")

    return {
        "status": "Assigned to human review (first line of defence)"
    }


#TODO: 5. Onboarding forms: filling, dispatching to client
#TODO: 6. Signed forms recevied & review (second line of defence)
#TODO: 7. Name screening (again? or move from 2.x here?)
#TODO: 8. EDD Integration (high risk case escalations only?)
#TODO: 9. Account opening at Core banking system + welcome letter with accounts instructions

def instructions_complete():
    return


FUNCTION_MAPPING = {
    'fetch_prospect_details': fetch_prospect_details,
    'collect_kyc_info': collect_kyc_info,
    'collect_sow_info': collect_sow_info,
    'perform_data_management_ai_extraction': perform_data_management_ai_extraction,
    'perform_name_screening': perform_name_screening,
    'create_client_profile': create_client_profile,
    'perform_compliance_risk_assessment': perform_compliance_risk_assessment,
    'assign_first_line_of_defence' : assign_first_line_of_defence,
    'instructions_complete': instructions_complete
    
}

TOOLS = [
    {
      "type": "function",
      "function": {
        "name": "fetch_prospect_details",
        "description": "Load prospect data from the CRM using the given full name.",
        "parameters": {
          "type": "object",
          "properties": {
            "full_name": {
              "type": "string",
              "description": "The full name of the prospect (e.g., 'John Doe')."
            }
          },
          "required": ["full_name"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "collect_kyc_info",
        "description": "KYC Information Collection: checks if mandatory fields are present.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
              "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "firstName": {
                  "type": "string"
                },
                "lastName": {
                  "type": "string"
                },
                "dateOfBirth": {
                  "type": "string"
                },
                "nationality": {
                  "type": "string"
                }
              },
              "required": [
                "clientID",
                "firstName",
                "lastName",
                "dateOfBirth",
                "nationality"
              ],
              "description": "A dictionary of prospect data from the CRM.",
            }
          },
          "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "collect_sow_info",
        "description": "Collect declared source of wealth (SOW) from prospect data.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
              "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "firstName": {
                  "type": "string"
                },
                "lastName": {
                  "type": "string"
                },
                "dateOfBirth": {
                  "type": "string"
                },
                "nationality": {
                  "type": "string"
                }
              },
              "required": [
                "clientID",
                "firstName",
                "lastName",
                "dateOfBirth",
                "nationality"
              ],
              "description": "A dictionary of prospect data from the CRM."
            }
          },
          "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "perform_data_management_ai_extraction",
        "description": "Parse attached docs (PDFs, images, etc.) with AI to extract relevant data.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
              "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "documents_provided": {
                  "type": "array",
                  "description": "A list of documents name provided by the prospect.",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "required": [
                "clientID",
                "documents_provided"
              ],
              "description": "A dictionary of prospect data that may include 'documents_provided'."
            }
          },
          "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "perform_name_screening",
        "description": "Randomly decides if the name appears on watchlists or sanctions lists.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
              "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "firstName": {
                  "type": "string"
                },
                "lastName": {
                  "type": "string"
                },
                "dateOfBirth": {
                  "type": "string"
                },
                "nationality": {
                  "type": "string"
                }
              },
              "required": [
                "clientID",
                "firstName",
                "lastName",
                "dateOfBirth",
                "nationality"
              ],
              "description": "A dictionary of prospect data containing name fields."
            }
          },
          "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "create_client_profile",
        "description": "Create a risk profile for the client based on name screening and nationality.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
             "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "risk_level": {
                  "type": "string"
                },
                "risk_score": {
                  "type": "integer"
                },
                "nationality": {
                  "type": "string"
                }
              },
              "required": [
                "clientID",
                "risk_level",
                "risk_score",
                "nationality"
              ],
              "description": "Prospect data containing nationality, etc."
            },
            "name_screening_result": {
              "type": "string",
              "description": "The result of perform_name_screening function."
            }
          },
          "required": ["prospect_data", "name_screening_result"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "perform_compliance_risk_assessment",
        "description": "Compliance check to determine if Enhanced Due Diligence is needed.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
             "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "name_screening_result": {
                  "type": "string"
                },
                "risk_level": {
                  "type": "string"
                }
              },
              "required": [
                "clientID",
                "name_screening_result",
                "risk_level"
              ],
              "description": "Prospect data containing risk_level, status, etc."
            }
          },
          "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "assign_first_line_of_defence",
        "description": "Assign the case to a human interface for go/no-go (first line of defence).",
        "parameters": {
          "type": "object",
          "properties": {
              "prospect_data": {
                "type": "object",
                "properties": {
                    "clientID": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "clientID"
                  ],
                  "description": "A dictionary containing up-to-date prospect info and status."
              }
            },
            "required": ["prospect_data"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "instructions_complete",
        "description": "signal that the execution should end.",
      }
    }
]

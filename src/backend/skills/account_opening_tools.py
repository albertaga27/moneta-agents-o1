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
    Step 1: Create a prospect in the CRM with initial mimimal information
    
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
        "status": "KYC data collected successfully.",
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
    Step 2.1: KYC Information Collection
    - Checks if mandatory fields are present.
    - Updates status and logs onboarding step.
    """
    mandatory_fields = ["firstName", "lastName", "dateOfBirth", "nationality"]
    missing_fields = [field for field in mandatory_fields if field not in prospect_data]
    
    if missing_fields:
        kyc_status = f"KYC incomplete. Missing fields: {missing_fields}"
        action_description = f"Client KYC data is incomplete. Missing: {', '.join(missing_fields)}."
    else:
        kyc_status = "KYC data collected successfully"
        action_description = "Client KYC data successfully verified and collected."

    # Update client data status
    prospect_data['status'] = kyc_status

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": kyc_status,
        "action": action_description
    }
    
    prospect_data["onboarding"].append(onboarding_entry)

    # Persist updated prospect data
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "status": kyc_status,
        "onboarding": prospect_data["onboarding"]
    }


def collect_sow_info(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2.2: Source of Wealth (SOW) Information Collection
    - Accepts a declared source of wealth.
    """
    #mocked fixed response
    sow = prospect_data.get("declared_source_of_wealth", "Employment")

    #update client data status
    prospect_data['status'] = "SOW information captured"

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": f"SOW information captured: {prospect_data.get("declared_source_of_wealth", "")}"
    }
    
    prospect_data["onboarding"].append(onboarding_entry)

    update_prospect_details(prospect_data['clientID'], prospect_data)
    return {
        "onboarding": prospect_data["onboarding"],
        "status": "SOW information captured"
    }

def perform_data_management_ai_extraction(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2.3: Data Management & AI Extraction
    - Mock logic that pretends to parse attached documents (PDFs, images, etc.).
    """
    ai_extracted_fields = {
        "passport_number": "MockPassport1234" if "passport" in prospect_data.get("documents_provided", []) else None,
        "proof_of_address_verified": "proof_of_address" in prospect_data.get("documents_provided", []),
    }
    
    #update client data status
    prospect_data['status'] = "Documents AI extraction completed"

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": "Documents AI extraction completed"
    }
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "extracted_fields": ai_extracted_fields,
        "status": "Documents AI extraction completed"
    }

def perform_name_screening(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2.4: Name Screening & Exception Handling
    - Randomly decides if the name appears on a watchlist or sanctions list.
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
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)
    
    return {
        "name_screening_result": screening_outcome,
        "status": screening_status
    }

def create_client_profile(prospect_data: Dict[str, Any], name_screening_result: str) -> Dict[str, Any]:
    """
    Step 2.5: Client Profile Risk Evaluation
    - Assigns a simple risk score/level based on name screening and nationality.
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
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "status": "Client profile generated."
    }

def perform_compliance_risk_assessment(prospect_data: Dict[str, Any] ) -> Dict[str, Any]:
    """
    Step 2.6: Compliance & Risk Assessment
    - If risk is 'High' or there's a sanctions list match, flag EDD.
    """
    risk_level = prospect_data['risk_level']
    screening_outcome =  prospect_data['name_screening_result']
    
    if risk_level == "High" or screening_outcome == "Sanctions list match":
        compliance_status = "High-risk client. Further Enhanced Due Diligence required."
    else:
        compliance_status = "Standard compliance checks passed."
    
    flagged_issues = []
    if "Missing fields" in prospect_data["status"]:
        flagged_issues.append("Incomplete KYC data or suspicious info received.")
    
    #update client data status
    prospect_data['status'] = "First KYC checks passed"

    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": prospect_data['status']+f": Compliance status is {compliance_status}"
    }
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "overall_status": compliance_status,
        "flagged_issues": flagged_issues
    }

#3.1 Human interface case assigned for go/no-go (first line of defence)
def assign_first_line_of_defence(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3.1: Assign the case with data and status so far to a Human interface for go/no-go (first line of defence).

    Update a record in DB or call an API to thid party system (case management etc.)
    """
    #external process logic (human case review etc.)

    #update client data status
    prospect_data['status'] = "Assigned to human review (first line of defence)"
    
    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": prospect_data['status']+f": Waiting for first compliance approval"
    }
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "status": "Assigned to human review (first line of defence)"
    }

#3.2 Human interface case outcome (first line of defence)
def receive_first_line_of_defence(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3.2: Outcome of the Human decision for go/no-go (first line of defence).

    This would most likely be a polling query to check status of an API
    """

    compliance_review = ""
    #external process logic (human case review etc.)
    if not "First line of defence: approved" == prospect_data['status']:
        compliance_review = "In compliance review"
    else:
        compliance_review = "First line of defence: approved"

    prospect_data['status'] = compliance_review
    # Add onboarding log entry
    onboarding_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": prospect_data['status'],
        "action": prospect_data['status']+f": {compliance_review}"
    }
    
    prospect_data["onboarding"].append(onboarding_entry)
    update_prospect_details(prospect_data['clientID'], prospect_data)

    return {
        "status": prospect_data['status']
    }


def check_required_documents(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4.1: Gather official documents such as passports, proof of address,
              and any other client-provided documentation.

    Simulates collecting these from the prospect and parsing essential data.
    """
    # In a real system, this step might involve uploading or scanning documents
    # and verifying the file formats.
    
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
    
    document_info = {
        "required_docs": required_docs,
        "provided_docs": provided_docs,
        "missing_docs": missing_docs,
        "extracted_data_points": extracted_data_points,
        "status": "Documents captured successfully" if not missing_docs else "Documents missing"
    }
    
    return document_info


def generate_compliance_verification_report(prospect_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 4.2: Generate a report on findings—e.g., verifying identity, 
              beneficial ownership, cross-border compliance, etc.
              
    :param prospect_data: The dictionary with the prospect information
    :return: A structured compliance report.
    """
    compliant = random.randint(0,1)
    
    if 0 == compliant:
        report_status = "Non-compliant / Additional checks required"
    else:
        report_status = "Fully compliant"
    
    return {
        "report_status": report_status,
        "summary": "Compliance verification completed with results above."
    }

#TODO: 5. Onboarding forms: filling, dispatching to client
#TODO: 6. Signed forms recevied & review (second line of defence)
#TODO: 7. Name screening (again? or move from 2.x here?)
#TODO: 8. EDD Integration (high risk case escalations only?)
#TODO: 9. Account opening at Core banking system + welcome letter with accounts instructions


FUNCTION_MAPPING = {
    'create_prospect': create_prospect,
    'fetch_prospect_details': fetch_prospect_details,
    'collect_kyc_info': collect_kyc_info,
    'collect_sow_info': collect_sow_info,
    'perform_data_management_ai_extraction': perform_data_management_ai_extraction,
    'perform_name_screening': perform_name_screening,
    'create_client_profile': create_client_profile,
    'perform_compliance_risk_assessment': perform_compliance_risk_assessment,
    'assign_first_line_of_defence' : assign_first_line_of_defence,
    'receive_first_line_of_defence' : receive_first_line_of_defence,
    'check_required_documents': check_required_documents,
    'generate_compliance_verification_report' : generate_compliance_verification_report
    
}

TOOLS = [
    {
      "type": "function",
      "function": {
        "name": "create_prospect",
        "description": "Step 1.1: Create a new prospect in the CRM with minimal information.",
        "parameters": {
          "type": "object",
          "properties": {
            "first_name": {
              "type": "string",
              "description": "The prospect's first name."
            },
            "last_name": {
              "type": "string",
              "description": "The prospect's last name."
            },
            "dob": {
              "type": "string",
              "description": "The date of birth in YYYY-MM-DD format."
            },
            "nationality": {
              "type": "string",
              "description": "The prospect's nationality."
            },
            "referral_source": {
              "type": "string",
              "description": "The referral source (e.g., 'Internal', 'External', etc.)."
            }
          },
          "required": ["first_name", "last_name", "dob", "nationality", "referral_source"]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "fetch_prospect_details",
        "description": "Step 1.2: Load prospect data from the CRM using the given full name.",
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
        "description": "Step 2.1 - KYC Information Collection: checks if mandatory fields are present.",
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
        "description": "Step 2.2 - Collect declared source of wealth (SOW) from prospect data.",
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
        "description": "Step 2.3 - Parse attached docs (PDFs, images, etc.) with AI to extract relevant data.",
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
        "description": "Step 2.4 - Randomly decides if the name appears on watchlists or sanctions lists.",
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
        "description": "Step 2.5 - Create a risk profile for the client based on name screening and nationality.",
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
        "description": "Step 2.6 - Final compliance check to determine if Enhanced Due Diligence is needed.",
        "parameters": {
          "type": "object",
          "properties": {
            "prospect_data": {
             "type": "object",
              "properties": {
                "clientID": {
                  "type": "string"
                },
                "status": {
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
                "status",
                "name_screening_result",
                "risk_level"
              ],
              "description": "Prospect data containing risk_level, status, etc."
            }
          }
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "assign_first_line_of_defence",
        "description": "Step 3.1 - Assign the case to a human interface for go/no-go (first line of defence).",
        "parameters": {
          "type": "object",
          "properties": {
              "prospect_data": {
                "type": "object",
                "properties": {
                    "clientID": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "clientID",
                    "status"
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
        "name": "receive_first_line_of_defence",
        "description": "Step 3.2 - Receive outcome from the human interface (first line of defence).",
        "parameters": {
          "type": "object",
          "properties": {
              "prospect_data": {
                "type": "object",
                "properties": {
                    "clientID": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "clientID",
                    "status"
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
        "name": "check_required_documents",
        "description": "Step 4.1 - Verify that the required documents have been provided and extract data.",
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
        "name": "generate_compliance_verification_report",
        "description": "Step 4.2 - Produce a structured compliance report.",
        "parameters": {
          "type": "object",
          "properties": {
              "prospect_data": {
                "type": "object",
                "properties": {
                    "clientID": {
                      "type": "string"
                    },
                    "status": {
                      "type": "string"
                    }
                  },
                  "required": [
                    "clientID",
                    "status"
                  ],
                  "description": "A dictionary containing up-to-date prospect info and status."
              }
            },
            "required": ["prospect_data"]
        }
      }
    }
]

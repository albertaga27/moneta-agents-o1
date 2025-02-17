from fastapi import FastAPI, HTTPException, Body  
from fastapi.responses import JSONResponse 
import os
import json
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential  
from pydantic import BaseModel
from typing import Optional, List
import logging

from crm_store import CRMStore  

load_dotenv()
app = FastAPI()

@app.post("/prospects")
def get_all_prospects(request: dict = Body(...)):
    """
    Return all records from Cosmos DB whose clientID starts with 'PRO'.
    The request body must include a user_id for demonstration/authorization purposes.
    """
     
    logging.info('Moneta o1 agents - <POST get_all_prospects> triggered...')

    # Extract parameters from the request body  
    user_id = request.get('user_id')
    # Validate required parameters
    if not user_id:
        raise HTTPException(status_code=400, detail="<user_id> is required!")
   
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

        prospects = crm_db.load_all_prospects()
        return json.dumps(prospects) if prospects else None

    except Exception as e:
        logging.error(f"Error in load_all_prospects: {str(e)}")
        return json.dumps({"error": f"load_all_prospects failed with error: {str(e)}"})


@app.post("/update_prospect")
def update_prospect(request: dict = Body(...)):
    """
    Update prospect_data into the CRM_Store
    The request body must include a user_id for demonstration/authorization purposes.
    """
     
    logging.info('Moneta o1 agents - <POST update_prospect> triggered...')

    # Extract parameters from the request body  
    user_id = request.get('user_id')
    # Validate required parameters
    if not user_id:
        raise HTTPException(status_code=400, detail="<user_id> is required!")
   
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

        prospect_data = json.loads(request.get('prospect_data'))
        prospects = crm_db.update_customer_profile(prospect_data["clientID"], prospect_data)
        return json.dumps(prospects) if prospects else None

    except Exception as e:
        logging.error(f"Error in load_all_prospects: {str(e)}")
        return json.dumps({"error": f"load_all_prospects failed with error: {str(e)}"})

@app.post("/run_ao_agents")
def run_ao_agents(request: dict = Body(...)):
    """
    Run the agentic account opening process to re-evaulate the prospect status 
    The request body must include a user_id for demonstration/authorization purposes.
    """
     
    logging.info('Moneta o1 agents - <POST run_ao_agents> triggered...')

from fastapi import FastAPI, HTTPException, Body  
from fastapi.responses import JSONResponse 
import os
import json
import datetime
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential  
from pydantic import BaseModel
from typing import Optional, List
import logging

from openai import AzureOpenAI
from crm_store import CRMStore  
from accountopening.planner_executor import *

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
    
    # Extract parameters from the request body  
    user_id = request.get('user_id')
    # Validate required parameters
    if not user_id:
        raise HTTPException(status_code=400, detail="<user_id> is required!")
   
    try:
        prospect_data = json.loads(request.get('prospect_data'))

        o1_client = get_openai_client("O1_OPENAI_API_KEY", "O1_OPENAI_ENDPOINT", "O1_MINI_OPENAI_DEPLOYMENT_NAME")
        #o1 planner agent part
        o1_response = call_o1(o1_client, prospect_data)

        #4o executor agent part
        client = get_openai_client("AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_DEPLOYMENT_NAME")
        ex_response = call_gpt4o(client, o1_response)

        # Filter assistant messages that have actual content
        assistants_4o_contents = [
            msg['content'] for msg in ex_response 
            if msg.get('role') == 'assistant' and msg.get('content') is not None
        ]

        #TODO think about filtering or what to do to return to the frontend all this chain of messages...
        
         # reload prospect after agentic workflow run...
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

        upd_prospect = crm_db.get_customer_profile_by_client_id(prospect_data['clientID'])
        return json.dumps(upd_prospect) if upd_prospect else None

    except Exception as e:
        logging.error(f"Error in run_ao_agents: {str(e)}")
        return json.dumps({"error": f"run_ao_agents failed with error: {str(e)}"})
    


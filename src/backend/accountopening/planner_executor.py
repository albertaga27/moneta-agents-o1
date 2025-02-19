import json
import os
import logging
from typing import Dict, Any, List
from datetime import datetime
import random

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from skills.account_opening_tools import *

from openai import AzureOpenAI

# Initialize OpenAI clients
def get_openai_client(key, endpoint, deployment):
    return AzureOpenAI(
        api_key=os.getenv(key),
        api_version="2024-02-15-preview",
        azure_endpoint=os.getenv(endpoint),
        azure_deployment=os.getenv(deployment)
    )


def call_o1(client, scenario):
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'business_logic.txt')
        business_logic = ""
        with open(file_path, 'r') as file:
            business_logic = file.read()
    
        # Prompt templates
        O1_PROMPT = """
You are a an account opening assistant focusing on orchestrating a full end to end workflow of private banking investement account opening
that involve several steps.
You are a planner. The input you will receive (the scenario) include the current status of the workflow in the field "status".
Your task is to review the status and understand which are the next steps to execute next (following the example plan in prder below) by creating a plan from the next bullet point on.

You will have access to an LLM agent that is responsible for executing the plan that you create and will return results.

The LLM agent has access to the following functions:
{tools}

When creating a plan for the LLM to execute, break your instructions into a logical, step-by-step order, using the specified format:
    - **Main actions are marked with letters** (e.g., A, B, C..).
    - **Sub-actions are under their relevant main actions** (e.g., A.1, B.2).
        - **Sub-actions should start on new lines**
    - **Specify conditions using clear 'if...then...else' statements** (e.g., 'If the status was approved, then...').
    - **For actions that require using one of the above functions defined**, write a step to call a function using backticks for the function name (e.g., `call the load_from_crm_by_client_fullname function`).
        - Ensure that the proper input arguments are given to the model for instruction. There should not be any ambiguity in the inputs.
    - **The last step** in the instructions should always be calling the `instructions_complete` function. This is necessary so we know the LLM has completed all of the instructions you have given it.
    - **Make the plan simple** Do not add steps on the plan when they are not needed.
    - **Generate summary** Before the `instructions_complete` ask the LLM to make a summary of the actions.
Use markdown format when generating the plan with each step and sub-step.

Please find the scenario below.
{scenario}

---

### Guidance Plan

Below is the ruleset of how you need to structure your final plan, including condition checks, steps/sub-steps, and function calls:

{business_logic}

**End of Plan**

"""       
        
        prompt= O1_PROMPT.replace("{tools}",str(TOOLS)).replace("{scenario}",str(scenario))
     
        response = client.chat.completions.create(
            model=os.getenv("O1_MINI_OPENAI_DEPLOYMENT_NAME"),
            messages=[{'role': 'user', 'content': prompt}]
        )
        
        plan = response.choices[0].message.content
        print(f"📟 Response from o1 plan: {plan}")
        return plan


def call_gpt4o(client, plan):
        GPT4O_SYSTEM_PROMPT = """
You are a helpful assistant responsible for executing a plan about account opening.
Your task is to:
1. Follow the plan exactly as written
2. Use the available tools to execute each step
3. Provide clear explanations of what you're doing
4. Always respond with some content explaining your actions
5. Call the instructions_complete function only when all steps are done
6. Never write or execute code
7. In your response, do not add things like "I have succesfully do this and that..." or "This should provide you with the content you asked for..."

PLAN TO EXECUTE:
{plan}

Remember to explain each action you take and provide status updates.
"""
        
        gpt4o_policy_prompt = GPT4O_SYSTEM_PROMPT.replace("{plan}", plan)
        messages = [{'role': 'system', 'content': gpt4o_policy_prompt}]

        while True:
            response = client.chat.completions.create(
                model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                messages=messages,
                tools=TOOLS,
                parallel_tool_calls=False
            )
            #self.logger.info(f" Response from 4o agent:\n {response}")
            
            assistant_message = response.choices[0].message.model_dump()
            messages.append(assistant_message)
   
            if not response.choices[0].message.tool_calls:
                continue

            for tool in response.choices[0].message.tool_calls:
                if tool.function.name == 'instructions_complete':
                    return messages

                function_name = tool.function.name 
              
                print(f"📟 Executing function: {function_name}")
                try:
                    arguments = json.loads(tool.function.arguments)
                    print(f"📟 ...with arguments: {arguments}")
                    function_response = FUNCTION_MAPPING[function_name](**arguments)
                  
                    print( f"{function_name}: {json.dumps(function_response)}")
                    print("Function executed successfully!")
                    #print(function_response)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": json.dumps(function_response)
                    })
                    
                except Exception as e:
                    print('error', f"Error in {function_name}: {str(e)}")
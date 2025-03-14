# Moneta-agents with Planner - Executor pattern

Demonstrates how to use a Planner - Executor pattern leveraging openAI reasoning models in combination of chat completions models to achieve AI workflow planning and execution only by looking at the data passed as input and without the usage of any agentic orchestration framework (Semantic kernel, langchain, crewAI etc.).

The business context is Account Opening and KYC Review for Private Banking / Wealth Management.

Note: this is an experiment!

## Prerequisites

* Docker
* [uv](https://docs.astral.sh/uv/getting-started/installation/)
* python 3.12
* pip

## Implementation Details
- Python 3.12 or higher
- OpenAI reasoning models 01/o3-mini + 4o / 4-mini
- Streamlit (frontend app)
- CosmosDB to simulate client CRM and store logs

## Use Cases

### Account Opening 

- `CRM`: simulate fetching clients information from a CRM (DB, third-party API etc)
- `Business Logic`: provided in natural language
- `Reasoning model as planner`: reads the business logic + the prospect data from CRM and come up with a Plan to resume or validate the account opening process based on the specific data
- `Completion model as executor`: reads the Plan made by the planner and execute the function calls to following the plan

### Periodic KYC review 

- 'TODO' as next

## Project structure

- src
  - backend
    - accountopening
      - business_logic.txt
      - planner_executor.py  
    - kycreview
      - 
    - skills
    - app.py # exposes API
    - crm_storep.py # handle db operations
    - env.sample

  - frontend
    - accountopening
        - app.py # streamlit app

## Setup

### Frontend
The project is managed by pyproject.toml.

* To init the .venv  install [uv package manager](https://docs.astral.sh/uv/getting-started/installation/) package manager"
* Run `uv sync`

1. Prepare requirements.txt
* To create requirements.txt out of pyproject.toml:
    ```shell
    uv pip compile pyproject.toml --no-deps |\
        grep -v '# via' |\
        grep -v ipykernel > requirements.txt 
    ```

2. Run locally

* Activate .venv as per above

```shell
cd src/frontend/accountopening
streamlit run app.py
```

The frontend does not use any variables, only calls the API of the backend assuming a default URL localhost:8000

### Backend
The project is managed by pyproject.toml.

* To init the .venv  install [uv package manager](https://docs.astral.sh/uv/getting-started/installation/) package manager"
* Run `uv sync`

1. Prepare requirements.txt
* To create requirements.txt out of pyproject.toml:
    ```shell
    uv pip compile pyproject.toml --no-deps |\
        grep -v '# via' |\
        grep -v ipykernel > requirements.txt 
    ```

2. Run locally

* Activate .venv as per above
* Configure .env as per sample.env

```shell
cd src/backend
uv sync
. ./.venv/bin/actvate
uvicorn app:app
```

Note: Be sure that the user is authorized in CosmosDB with appropriate roles to perform data operations.
*Run the cosmosdb_cli_addrole.sh to set roles*

### Use the Testing-o1.ipynb to create and manage prospects in the db and for fast testing.
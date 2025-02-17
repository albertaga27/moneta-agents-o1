from azure.cosmos import CosmosClient, PartitionKey, exceptions
import os
import json
import datetime
import random

class CRMStore:
    def __init__(self, url, key, database_name, container_name):
        self.client = CosmosClient(url, credential=key)
        self.database_name = database_name
        self.container_name = container_name
        self.db = None
        self.container = None
        self.initialize_database()
        self.initialize_container()

    def initialize_database(self):
        try:
            self.db = self.client.create_database_if_not_exists(id=self.database_name)
        except exceptions.CosmosResourceExistsError:
            self.db = self.client.get_database_client(database=self.database_name)

    def initialize_container(self):
        try:
            self.container = self.db.create_container_if_not_exists(
                id=self.container_name,
                partition_key=PartitionKey(path="/client_id"),
                offer_throughput=400
            )
        except exceptions.CosmosResourceExistsError:
            self.container = self.db.get_container_client(container=self.container_name)
            
        
    def create_customer_profile(self, customer_profile):
        """
        Saves the customer profile to Cosmos DB.
        
        Args:
        - customer_profile (dict): The customer profile to save.
        """
        
        try:
            # Create a new document in the container
            created_user = self.container.create_item(body=customer_profile)
            return created_user
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    def get_customer_profile_by_full_name(self, full_name):
        """
        Retrieves a customer profile from Cosmos DB based on a partial match of the customer's full name.
        
        Args:
        - full_name (str): The partial or full name of the customer to search for.
        
        Returns:
        - dict: The customer profile, if found.
        """
        query = "SELECT * FROM c WHERE c.fullName LIKE @full_name"
        parameters = [
            {"name": "@full_name", "value": f"%{full_name}%"}
        ]
        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items[0] if items else None
    

    def get_customer_profile_by_client_id(self, client_id):
        """
        Retrieves a customer profile from Cosmos DB based on a client_id.
        
        Args:
        - client_id (str): The client id of the customer to search for.
        
        Returns:
        - dict: The customer profile, if found.
        """
        query = "SELECT * FROM c WHERE c.clientID = @client_id"
        parameters = [
            {"name": "@client_id", "value": client_id}
        ]
        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        ))
        return items[0] if items else None
    

    def update_customer_profile(self, client_id: str, updated_data: dict):
        """
        Updates a customer profile in Cosmos DB with new data.

        Args:
            client_id (str): The client ID of the profile to be updated.
            updated_data (dict): A dictionary containing the fields and values to be updated.

        Returns:
            dict or None: The updated profile if successful, or None if the profile was not found.
        """
        # 1. Fetch the existing profile by client ID
        existing_profile = self.get_customer_profile_by_client_id(client_id)
        if not existing_profile:
            print(f"No profile found for clientID: {client_id}")
            return None

        # 2. Merge/overwrite fields from updated_data
        for key, value in updated_data.items():
            existing_profile[key] = value

        # 3. Replace the item in Cosmos DB using replace_item (or upsert_item)
        try:
            updated_profile = self.container.replace_item(
                item=existing_profile,
                body=existing_profile
            )
            return updated_profile
        except Exception as e:
            print(f"An error occurred while updating: {e}")
            return None


    def delete_customer_profile(self, client_id: str) -> bool:
        """
        Deletes a customer profile from Cosmos DB by clientID.
        
        Args:
            client_id (str): The clientID of the profile to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        # 1. Attempt to find the existing profile
        existing_profile = self.get_customer_profile_by_client_id(client_id)
        if not existing_profile:
            print(f"No profile found for clientID: {client_id}")
            return False

        try:
            # 2. Delete the found item from Cosmos
            self.container.delete_item(
                item=existing_profile["id"],
                partition_key=existing_profile["clientID"]
            )
            return True
        except Exception as e:
            print(f"An error occurred while deleting: {e}")
            return False

    
    def load_all_prospects(self):
        """
        Retrieves all customer profiles from Cosmos DB where clientID starts with 'PRO'.
        
        Returns:
        - list: A list of all matching customer profiles.
        """
        query = "SELECT * FROM c WHERE STARTSWITH(c.clientID, 'PRO')"
        try:
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
        except Exception as e:
            print(f"An error occurred while loading all prospects: {e}")
            return False  
        return items



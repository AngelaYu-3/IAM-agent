from langflow.field_typing import Data
from langflow.custom import Component
from langflow.io import MessageTextInput, DataInput, Output
from langflow.schema import Data
import pandas as pd

class UserLookupTool(Component):
    display_name = "User Lookup Tool"
    description = "Look up user information from IAM CSV data"
    documentation: str = "https://docs.langflow.org/components-custom-components"
    icon = "search"
    name = "UserLookupTool"
    
    inputs = [
        MessageTextInput(
            name="username",
            display_name="Username",
            info="Username to lookup in IAM system",
            value="",
            tool_mode=True,
        ),
        DataInput(
            name="csv_data",
            display_name="User Data",
            info="IAM user data from CSV file",
            input_types=["DataFrame", "Data"],
        ),
    ]
    
    outputs = [
        Output(display_name="User Data", name="user_data", method="lookup_user"),
    ]
    
    def lookup_user(self) -> DataFrame:
        """
        Look up user in CSV data and return their information
        """
        try:
            username = self.username.strip()
            csv_data = self.csv_data
            
            # Handle different data formats
            if isinstance(csv_data, pd.DataFrame):
                # Convert DataFrame to list of dictionaries
                data_records = csv_data.to_dict('records')
                data_type = "DataFrame"
            elif isinstance(csv_data, list):
                # Already a list of dictionaries
                data_records = csv_data
                data_type = "List"
            else:
                # Try to convert whatever we got
                try:
                    data_records = list(csv_data)
                    data_type = "Converted"
                except:
                    data_records = []
                    data_type = "Unknown"
            
            # DEBUG: Let's see what we're getting
            debug_info = f"DEBUG - Username: '{username}', Original Type: {type(csv_data)}, Converted Type: {data_type}, Records: {len(data_records) if data_records else 'None'}"
            
            if not username:
                return Data(value={
                    "found": False,
                    "error": "Please provide a username to lookup",
                    "debug": debug_info
                })
            
            if not data_records:
                return Data(value={
                    "found": False,
                    "error": "No CSV data provided - check File component connection",
                    "debug": debug_info
                })
            
            # DEBUG: Show first few usernames we can see
            available_users = []
            if data_records and len(data_records) > 0:
                for i, record in enumerate(data_records[:5]):  # First 5 records
                    if isinstance(record, dict):
                        available_users.append(record.get('username', f'Record_{i}_no_username'))
                    else:
                        available_users.append(f'Record_{i}_not_dict')
            
            # Search for user in CSV data
            user_found = None
            
            for user_record in data_records:
                if isinstance(user_record, dict):
                    record_username = user_record.get('username', '')
                    if str(record_username).lower() == username.lower():
                        user_found = user_record
                        break
            
            if not user_found:
                result = {
                    "found": False,
                    "message": f"User '{username}' not found in IAM system",
                    "debug": debug_info,
                    "available_users": available_users,
                    "total_records": len(data_records) if data_records else 0
                }
                
                self.status = f"User {username} not found"
                return Data(value=result)
            
            # User found - extract and return their data
            permissions_str = user_found.get('permissions', '')
            permissions_list = str(permissions_str).split(',') if permissions_str else []
            risk_reasoning = str(user_found.get('risk_reasoning', '')).strip()
            
            result = {
                "found": True,
                "username": user_found.get('username'),
                "department": user_found.get('department'),
                "role": user_found.get('role'),
                "permissions": permissions_list,
                "permission_count": len(permissions_list),
                "employment_status": user_found.get('employment_status'),
                "hire_date": user_found.get('hire_date'),
                "risk_reasoning": risk_reasoning,
                "has_risk_flags": bool(risk_reasoning and risk_reasoning != 'nan'),
                "risky_permissions": risk_reasoning.split(', ') if risk_reasoning and risk_reasoning != 'nan' else []
            }
            
            # Set status message
            risk_level = "HIGH RISK" if risk_reasoning and risk_reasoning != 'nan' else "Standard"
            self.status = f"Found {username} - {risk_level}"
            
            return Data(value=result)
            
        except Exception as e:
            error_result = {
                "found": False,
                "error": f"Lookup failed: {str(e)}",
                "debug": f"Exception occurred: {e}"
            }
            self.status = f"Error: {str(e)}"
            return Data(value=error_result)
"""
Airtable Service - REST API integration to store lead data
This is how no-code agent builders work - they collect data and store it via API
"""
from __future__ import annotations

import os
import requests
from typing import Dict, Any, Optional
from datetime import datetime


class AirtableService:
    """
    Airtable REST API Service
    
    No-code platforms like this use simple REST API calls to store data.
    User never sees the complexity - they just see the conversation.
    """
    
    def __init__(self):
        self.api_key = os.getenv("AIRTABLE_API_KEY")
        self.base_id = os.getenv("AIRTABLE_BASE_ID")
        self.table_name = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
        self.api_base_url = os.getenv("AIRTABLE_API_BASE_URL", "https://api.airtable.com/v0")
        
        self.base_url = f"{self.api_base_url}/{self.base_id}/{self.table_name}"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Airtable is properly configured"""
        return bool(self.api_key and self.base_id)
    
    def create_lead(self, profile: Dict[str, str], summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new lead record in Airtable
        
        Args:
            profile: Dict with user data (name, email, mobile, etc.)
            summary: Optional generated summary text
            
        Returns:
            Dict with success status and record ID or error message
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Airtable not configured. Set AIRTABLE_API_KEY and AIRTABLE_BASE_ID environment variables."
            }
        
        try:
            # Load field mapping from config
            try:
                from config import AIRTABLE_FIELD_MAPPING
            except ImportError:
                AIRTABLE_FIELD_MAPPING = {
                    "name": "Name", "email": "Email", "mobile": "Mobile",
                    "age": "Age", "city": "City", "summary": "Summary"
                }
            
            # Map profile fields to Airtable columns using config
            fields = {}
            for local_field, airtable_column in AIRTABLE_FIELD_MAPPING.items():
                if local_field == "summary":
                    if summary:
                        fields[airtable_column] = summary
                elif local_field in profile and profile[local_field]:
                    fields[airtable_column] = profile[local_field]
            
            # Remove empty fields
            fields = {k: v for k, v in fields.items() if v}
            
            payload = {
                "records": [
                    {
                        "fields": fields
                    }
                ]
            }
            
            print(f"📤 AIRTABLE - Sending data to Airtable...")
            print(f"📤 AIRTABLE - Base ID: {self.base_id}")
            print(f"📤 AIRTABLE - Table: {self.table_name}")
            print(f"📤 AIRTABLE - URL: {self.base_url}")
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            print(f"📤 AIRTABLE - Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                record_id = data["records"][0]["id"]
                print(f"📤 AIRTABLE - ✓ Lead saved successfully! Record ID: {record_id}")
                return {
                    "success": True,
                    "record_id": record_id,
                    "message": "Lead saved to Airtable successfully"
                }
            else:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", response.text)
                error_type = error_data.get("error", {}).get("type", "Unknown")
                print(f"📤 AIRTABLE - ✗ Error Type: {error_type}")
                print(f"📤 AIRTABLE - ✗ Error: {error_msg}")
                return {
                    "success": False,
                    "error": f"Airtable API error: {error_msg}",
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            print("📤 AIRTABLE - ✗ Request timeout")
            return {
                "success": False,
                "error": "Airtable request timed out"
            }
        except requests.exceptions.RequestException as e:
            print(f"📤 AIRTABLE - ✗ Request error: {e}")
            return {
                "success": False,
                "error": f"Network error: {str(e)}"
            }
        except Exception as e:
            print(f"📤 AIRTABLE - ✗ Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def get_leads(self, max_records: int = 100) -> Dict[str, Any]:
        """
        Get leads from Airtable (for admin/dashboard use)
        
        Args:
            max_records: Maximum number of records to fetch
            
        Returns:
            Dict with success status and records or error
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Airtable not configured"
            }
        
        try:
            params = {
                "maxRecords": max_records,
                "sort[0][field]": "Created At",
                "sort[0][direction]": "desc"
            }
            
            response = requests.get(
                self.base_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "records": data.get("records", []),
                    "count": len(data.get("records", []))
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", response.text)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
_airtable_service: Optional[AirtableService] = None


def get_airtable_service() -> AirtableService:
    """Get singleton Airtable service instance"""
    global _airtable_service
    if _airtable_service is None:
        _airtable_service = AirtableService()
    return _airtable_service


def save_lead_to_airtable(profile: Dict[str, str], summary: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to save lead to Airtable
    
    This is called by Summary Agent after generating summary.
    User never sees this - it happens in the backend.
    """
    service = get_airtable_service()
    return service.create_lead(profile, summary)

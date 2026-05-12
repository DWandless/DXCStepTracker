"""
OneDrive storage helper for Step Tracker evidence uploads.
Handles file uploads to OneDrive using Microsoft Graph API.
"""

import streamlit as st
import requests
from io import BytesIO
import logging

# Microsoft Graph API endpoints
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
ONEDRIVE_FOLDER = "StepTrackerEvidence"  # Folder name in OneDrive root


def get_access_token():
    """
    Get Microsoft Graph access token from session state.
    Uses the token obtained during login.
    """
    token = st.session_state.get("token")
    if token and "access_token" in token:
        # Debug: Check what scopes are in the token
        try:
            import jwt
            decoded = jwt.decode(token["access_token"], options={"verify_signature": False})
            scopes = decoded.get("scp", "").split() if "scp" in decoded else []
            logging.info(f"Token scopes: {scopes}")
        except Exception as e:
            logging.error(f"Could not decode token: {e}")
        
        return token["access_token"]
    return None


def create_onedrive_folder_if_not_exists(access_token):
    """
    Create the StepTrackerEvidence folder in OneDrive root if it doesn't exist.
    
    Args:
        access_token: Microsoft Graph access token
        
    Returns:
        tuple: (folder_id, error_message) - folder_id if successful, None otherwise
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Check if folder exists
    try:
        search_url = f"{GRAPH_API_ENDPOINT}/me/drive/root/children"
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 401:
            return None, "Authentication failed - token may not have Files.ReadWrite permission"
        elif response.status_code == 403:
            return None, "Access denied - check Azure app permissions"
        elif response.status_code == 200:
            items = response.json().get("value", [])
            for item in items:
                if item.get("name") == ONEDRIVE_FOLDER and "folder" in item:
                    return item["id"], None
        else:
            logging.error(f"Failed to list OneDrive: {response.status_code} - {response.text}")
            return None, f"OneDrive access failed: {response.status_code}"
        
        # Folder doesn't exist, create it
        create_url = f"{GRAPH_API_ENDPOINT}/me/drive/root/children"
        folder_data = {
            "name": ONEDRIVE_FOLDER,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename"
        }
        
        create_response = requests.post(create_url, headers=headers, json=folder_data)
        
        if create_response.status_code in [200, 201]:
            return create_response.json()["id"], None
        else:
            error_msg = f"Failed to create folder: {create_response.status_code}"
            logging.error(f"{error_msg} - {create_response.text}")
            return None, error_msg
            
    except Exception as e:
        error_msg = f"Error accessing OneDrive: {str(e)}"
        logging.error(error_msg)
        return None, error_msg


def upload_to_onedrive(file_bytes, filename, access_token):
    """
    Upload a file to OneDrive StepTrackerEvidence folder.
    
    Args:
        file_bytes: File content as bytes
        filename: Name for the file
        access_token: Microsoft Graph access token
        
    Returns:
        dict with 'success' (bool), 'url' (str), 'error' (str)
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        # Ensure folder exists
        folder_id, error_msg = create_onedrive_folder_if_not_exists(access_token)
        
        if not folder_id:
            return {
                "success": False,
                "error": error_msg or "Could not create or access OneDrive folder"
            }
        
        # Upload file to folder
        upload_url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{folder_id}:/{filename}:/content"
        
        response = requests.put(upload_url, headers=headers, data=file_bytes)
        
        if response.status_code in [200, 201]:
            file_data = response.json()
            
            # Create a sharing link for the file
            share_url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{file_data['id']}/createLink"
            share_data = {
                "type": "view",  # Read-only link
                "scope": "organization"  # Only people in your org
            }
            
            share_headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            share_response = requests.post(share_url, headers=share_headers, json=share_data)
            
            if share_response.status_code in [200, 201]:
                web_url = share_response.json()["link"]["webUrl"]
            else:
                # Fallback to direct web URL
                web_url = file_data.get("webUrl", "")
            
            return {
                "success": True,
                "url": web_url,
                "file_id": file_data["id"]
            }
        else:
            logging.error(f"Upload failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Upload failed: {response.status_code}"
            }
            
    except Exception as e:
        logging.error(f"Error uploading to OneDrive: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_from_onedrive(file_id, access_token):
    """
    Delete a file from OneDrive.
    
    Args:
        file_id: OneDrive file ID
        access_token: Microsoft Graph access token
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        delete_url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{file_id}"
        response = requests.delete(delete_url, headers=headers)
        
        return response.status_code == 204
        
    except Exception as e:
        logging.error(f"Error deleting from OneDrive: {e}")
        return False


def get_file_id_from_sharing_url(sharing_url, access_token):
    """
    Resolve a sharing URL to get the OneDrive file_id.
    
    Args:
        sharing_url: SharePoint/OneDrive sharing URL
        access_token: Microsoft Graph access token
        
    Returns:
        str: file_id or None
    """
    try:
        import base64
        
        # Encode the sharing URL as base64 (URL-safe, without padding)
        encoded_url = base64.urlsafe_b64encode(sharing_url.encode('utf-8')).decode('utf-8').rstrip('=')
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # Try the /shares endpoint first
        url = f"{GRAPH_API_ENDPOINT}/shares/{encoded_url}/driveItem"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            file_id = response.json().get("id")
            logging.info(f"Successfully resolved sharing URL to file_id: {file_id}")
            return file_id
        
        # Fallback to /me/drive/shared endpoint
        url = f"{GRAPH_API_ENDPOINT}/me/drive/shared/{encoded_url}/driveitem"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            file_id = response.json().get("id")
            logging.info(f"Successfully resolved sharing URL to file_id (fallback): {file_id}")
            return file_id
        
        logging.error(f"Failed to resolve sharing URL: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        logging.error(f"Error resolving sharing URL: {e}")
        return None


def get_file_download_url(file_id, access_token):
    """
    Get a temporary download URL for a file.
    
    Args:
        file_id: OneDrive file ID
        access_token: Microsoft Graph access token
        
    Returns:
        str: Download URL or None
    """
    try:
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        url = f"{GRAPH_API_ENDPOINT}/me/drive/items/{file_id}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get("@microsoft.graph.downloadUrl")
        
        return None
        
    except Exception as e:
        logging.error(f"Error getting download URL: {e}")
        return None

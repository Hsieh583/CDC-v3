import os
from pathlib import Path
from typing import Optional, Tuple
from werkzeug.utils import secure_filename

# Try to import SharePoint libraries (optional dependency)
try:
    from office365.runtime.auth.authentication_context import AuthenticationContext
    from office365.sharepoint.client_context import ClientContext
    SHAREPOINT_AVAILABLE = True
except ImportError:
    SHAREPOINT_AVAILABLE = False


class SharePointService:
    """
    SharePoint integration service
    Falls back to local storage if SharePoint is not configured
    """
    
    def __init__(self, config):
        self.config = config
        self.site_url = config.get('SHAREPOINT_SITE_URL', '')
        self.username = config.get('SHAREPOINT_USERNAME', '')
        self.password = config.get('SHAREPOINT_PASSWORD', '')
        self.root_folder = config.get('SHAREPOINT_ROOT_FOLDER', 'CDC-PR-Cases')
        self.local_storage_path = Path(config.get('LOCAL_STORAGE_PATH', './instance/storage'))
        
        # Determine if SharePoint is configured
        self.sharepoint_enabled = bool(self.site_url and self.username and self.password)
        
        # Ensure local storage exists
        self.local_storage_path.mkdir(parents=True, exist_ok=True)
    
    def create_case_folder(self, case_number: str) -> Tuple[bool, str]:
        """
        Create a folder for the case
        Returns: (success, folder_path)
        """
        if self.sharepoint_enabled:
            return self._create_sharepoint_folder(case_number)
        else:
            return self._create_local_folder(case_number)
    
    def upload_file(self, case_number: str, file, filename: str) -> Tuple[bool, str, Optional[str]]:
        """
        Upload a file to the case folder
        Returns: (success, file_path, error_message)
        """
        safe_filename = secure_filename(filename)
        
        if self.sharepoint_enabled:
            return self._upload_to_sharepoint(case_number, file, safe_filename)
        else:
            return self._upload_to_local(case_number, file, safe_filename)
    
    def get_file_url(self, case_number: str, filename: str) -> Optional[str]:
        """Get the URL/path to access a file"""
        if self.sharepoint_enabled:
            return f"{self.site_url}/{self.root_folder}/{case_number}/{filename}"
        else:
            return f"/storage/{case_number}/{filename}"
    
    def _create_sharepoint_folder(self, case_number: str) -> Tuple[bool, str]:
        """Create folder in SharePoint"""
        if not SHAREPOINT_AVAILABLE:
            return self._create_local_folder(case_number)
        
        try:
            ctx_auth = AuthenticationContext(self.site_url)
            if ctx_auth.acquire_token_for_user(self.username, self.password):
                ctx = ClientContext(self.site_url, ctx_auth)
                
                # Get or create root folder
                web = ctx.web
                folder_url = f"Shared Documents/{self.root_folder}/{case_number}"
                
                # Create folder
                target_folder = web.folders.add(folder_url)
                ctx.execute_query()
                
                return True, folder_url
            else:
                return False, "SharePoint authentication failed"
        except Exception as e:
            # Fall back to local storage on error
            print(f"SharePoint error: {e}, falling back to local storage")
            return self._create_local_folder(case_number)
    
    def _create_local_folder(self, case_number: str) -> Tuple[bool, str]:
        """Create folder in local storage"""
        try:
            case_folder = self.local_storage_path / case_number
            case_folder.mkdir(parents=True, exist_ok=True)
            return True, str(case_folder)
        except Exception as e:
            return False, str(e)
    
    def _upload_to_sharepoint(self, case_number: str, file, filename: str) -> Tuple[bool, str, Optional[str]]:
        """Upload file to SharePoint"""
        if not SHAREPOINT_AVAILABLE:
            return self._upload_to_local(case_number, file, filename)
        
        try:
            ctx_auth = AuthenticationContext(self.site_url)
            if ctx_auth.acquire_token_for_user(self.username, self.password):
                ctx = ClientContext(self.site_url, ctx_auth)
                
                folder_url = f"Shared Documents/{self.root_folder}/{case_number}"
                target_folder = ctx.web.get_folder_by_server_relative_url(folder_url)
                
                # Read file content
                file_content = file.read()
                
                # Upload file
                target_file = target_folder.upload_file(filename, file_content)
                ctx.execute_query()
                
                file_path = f"{folder_url}/{filename}"
                return True, file_path, None
            else:
                return False, "", "SharePoint authentication failed"
        except Exception as e:
            # Fall back to local storage on error
            print(f"SharePoint upload error: {e}, falling back to local storage")
            file.seek(0)  # Reset file pointer
            return self._upload_to_local(case_number, file, filename)
    
    def _upload_to_local(self, case_number: str, file, filename: str) -> Tuple[bool, str, Optional[str]]:
        """Upload file to local storage"""
        try:
            case_folder = self.local_storage_path / case_number
            case_folder.mkdir(parents=True, exist_ok=True)
            
            file_path = case_folder / filename
            file.save(str(file_path))
            
            return True, str(file_path), None
        except Exception as e:
            return False, "", str(e)

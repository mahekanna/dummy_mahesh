# utils/csv_field_mapper.py
import re
from datetime import datetime
from typing import Dict, List, Optional, Set
from utils.logger import Logger

class CSVFieldMapper:
    """
    Robust CSV field mapping system that handles various CSV formats
    and maps them to standardized internal field names
    """
    
    def __init__(self):
        self.logger = Logger('csv_field_mapper')
        
        # Define field mapping patterns - map various CSV field names to our standard names
        self.field_mappings = {
            # Server identification
            'server_name': [
                'Server Name', 'ServerName', 'Hostname', 'Host Name', 'server_name', 
                'hostname', 'Server', 'Host', 'FQDN', 'server_fqdn', 'machine_name'
            ],
            
            # Timezone
            'server_timezone': [
                'Server Timezone', 'Timezone', 'Time Zone', 'server_timezone', 
                'timezone', 'tz', 'ServerTZ', 'ServerTimeZone'
            ],
            
            # Operating System
            'operating_system': [
                'Operating System', 'OS', 'operating_system', 'os_type', 'OSType',
                'Platform', 'OS Version', 'Operating_System', 'OperatingSystem'
            ],
            
            # Environment
            'environment': [
                'Environment', 'Env', 'environment', 'env_type', 'Environment Type',
                'Stage', 'Tier', 'ServerEnvironment'
            ],
            
            # Ownership - Primary Owner
            'primary_owner': [
                'primary_owner', 'Primary Owner', 'PrimaryOwner', 'Owner', 'owner',
                'Server Owner', 'ServerOwner', 'Primary Contact', 'PrimaryContact',
                'primary_contact', 'main_owner', 'MainOwner', 'responsible_person',
                'admin_contact', 'AdminContact', 'primary_admin', 'PrimaryAdmin'
            ],
            
            # Ownership - Secondary Owner
            'secondary_owner': [
                'secondary_owner', 'Secondary Owner', 'SecondaryOwner', 'Backup Owner',
                'BackupOwner', 'backup_owner', 'Secondary Contact', 'SecondaryContact',
                'secondary_contact', 'backup_contact', 'BackupContact', 'alternate_owner',
                'AlternateOwner', 'secondary_admin', 'SecondaryAdmin'
            ],
            
            # Linux Users (converted from emails)
            'primary_linux_user': [
                'primary_linux_user', 'Primary Linux User', 'PrimaryLinuxUser',
                'primary_user', 'PrimaryUser', 'main_user', 'MainUser'
            ],
            
            'secondary_linux_user': [
                'secondary_linux_user', 'Secondary Linux User', 'SecondaryLinuxUser',
                'secondary_user', 'SecondaryUser', 'backup_user', 'BackupUser'
            ],
            
            # Host Group / Server Group
            'host_group': [
                'host_group', 'Host Group', 'HostGroup', 'Server Group', 'ServerGroup',
                'server_group', 'Group', 'group', 'application_group', 'ApplicationGroup',
                'service_group', 'ServiceGroup', 'cluster', 'Cluster'
            ],
            
            # Engineering Domain / Business Unit
            'engr_domain': [
                'engr_domain', 'Engineering Domain', 'EngineeringDomain', 'Domain',
                'Business Unit', 'BusinessUnit', 'business_unit', 'Department',
                'department', 'Team', 'team', 'Organization', 'organization'
            ],
            
            # Location
            'location': [
                'location', 'Location', 'Site', 'site', 'Data Center', 'DataCenter',
                'data_center', 'DC', 'dc', 'Region', 'region', 'Facility', 'facility'
            ],
            
            # Serial Number
            'serial_number': [
                'serial_number', 'Serial Number', 'SerialNumber', 'Serial', 'serial',
                'Asset Tag', 'AssetTag', 'asset_tag', 'Hardware Serial', 'HW Serial',
                'Service Tag', 'ServiceTag', 'service_tag'
            ],
            
            # Patching-specific fields
            'incident_ticket': [
                'incident_ticket', 'Incident Ticket', 'IncidentTicket', 'Ticket',
                'ticket', 'Change Request', 'ChangeRequest', 'change_request',
                'CR', 'cr', 'Work Order', 'WorkOrder', 'work_order'
            ],
            
            'patcher_email': [
                'patcher_email', 'Patcher Email', 'PatcherEmail', 'Patcher',
                'patcher', 'Patch Engineer', 'PatchEngineer', 'patch_engineer',
                'patching_contact', 'PatchingContact'
            ],
            
            # Quarterly patch scheduling
            'q1_patch_date': [
                'Q1 Patch Date', 'Q1PatchDate', 'q1_patch_date', 'Q1_Patch_Date',
                'Quarter 1 Patch Date', 'Q1 Date', 'Q1Date'
            ],
            'q1_patch_time': [
                'Q1 Patch Time', 'Q1PatchTime', 'q1_patch_time', 'Q1_Patch_Time',
                'Quarter 1 Patch Time', 'Q1 Time', 'Q1Time'
            ],
            'q1_approval_status': [
                'Q1 Approval Status', 'Q1ApprovalStatus', 'q1_approval_status',
                'Q1_Approval_Status', 'Quarter 1 Approval', 'Q1 Status', 'Q1Status'
            ],
            
            # Similar patterns for Q2, Q3, Q4
            'q2_patch_date': [
                'Q2 Patch Date', 'Q2PatchDate', 'q2_patch_date', 'Q2_Patch_Date',
                'Quarter 2 Patch Date', 'Q2 Date', 'Q2Date'
            ],
            'q2_patch_time': [
                'Q2 Patch Time', 'Q2PatchTime', 'q2_patch_time', 'Q2_Patch_Time',
                'Quarter 2 Patch Time', 'Q2 Time', 'Q2Time'
            ],
            'q2_approval_status': [
                'Q2 Approval Status', 'Q2ApprovalStatus', 'q2_approval_status',
                'Q2_Approval_Status', 'Quarter 2 Approval', 'Q2 Status', 'Q2Status'
            ],
            
            'q3_patch_date': [
                'Q3 Patch Date', 'Q3PatchDate', 'q3_patch_date', 'Q3_Patch_Date',
                'Quarter 3 Patch Date', 'Q3 Date', 'Q3Date'
            ],
            'q3_patch_time': [
                'Q3 Patch Time', 'Q3PatchTime', 'q3_patch_time', 'Q3_Patch_Time',
                'Quarter 3 Patch Time', 'Q3 Time', 'Q3Time'
            ],
            'q3_approval_status': [
                'Q3 Approval Status', 'Q3ApprovalStatus', 'q3_approval_status',
                'Q3_Approval_Status', 'Quarter 3 Approval', 'Q3 Status', 'Q3Status'
            ],
            
            'q4_patch_date': [
                'Q4 Patch Date', 'Q4PatchDate', 'q4_patch_date', 'Q4_Patch_Date',
                'Quarter 4 Patch Date', 'Q4 Date', 'Q4Date'
            ],
            'q4_patch_time': [
                'Q4 Patch Time', 'Q4PatchTime', 'q4_patch_time', 'Q4_Patch_Time',
                'Quarter 4 Patch Time', 'Q4 Time', 'Q4Time'
            ],
            'q4_approval_status': [
                'Q4 Approval Status', 'Q4ApprovalStatus', 'q4_approval_status',
                'Q4_Approval_Status', 'Quarter 4 Approval', 'Q4 Status', 'Q4Status'
            ],
            
            # Current status
            'current_quarter_status': [
                'Current Quarter Patching Status', 'Current Status', 'CurrentStatus',
                'current_quarter_status', 'Patching Status', 'PatchingStatus',
                'patching_status', 'Status', 'status'
            ],
            
            # Sync metadata
            'last_sync_date': [
                'last_sync_date', 'Last Sync Date', 'LastSyncDate', 'Last Sync',
                'LastSync', 'Sync Date', 'SyncDate', 'Updated Date', 'UpdatedDate'
            ],
            'sync_status': [
                'sync_status', 'Sync Status', 'SyncStatus', 'Sync State', 'SyncState'
            ]
        }
        
        # Define which fields come from external CSV vs internal system
        self.external_fields = {
            'server_name', 'primary_owner', 'secondary_owner', 
            'host_group', 'engr_domain', 'location', 'serial_number'
        }
        
        self.internal_fields = {
            'q1_patch_date', 'q1_patch_time', 'q1_approval_status',
            'q2_patch_date', 'q2_patch_time', 'q2_approval_status', 
            'q3_patch_date', 'q3_patch_time', 'q3_approval_status',
            'q4_patch_date', 'q4_patch_time', 'q4_approval_status',
            'current_quarter_status', 'server_timezone', 'incident_ticket',
            'patcher_email', 'primary_linux_user', 'secondary_linux_user',
            'last_sync_date', 'sync_status', 'operating_system', 'environment'
        }
        
        # Build reverse mapping for quick lookup
        self._build_reverse_mapping()
    
    def _build_reverse_mapping(self):
        """Build reverse mapping from CSV field names to standard field names"""
        self.reverse_mapping = {}
        
        for standard_field, csv_variants in self.field_mappings.items():
            for variant in csv_variants:
                # Case-insensitive mapping
                self.reverse_mapping[variant.lower()] = standard_field
    
    def map_csv_fields(self, csv_headers: List[str]) -> Dict[str, str]:
        """
        Map CSV headers to standardized field names
        
        Args:
            csv_headers: List of CSV column headers
            
        Returns:
            Dictionary mapping CSV headers to standard field names
        """
        field_mapping = {}
        unmapped_fields = []
        
        for header in csv_headers:
            header_clean = header.strip()
            header_lower = header_clean.lower()
            
            if header_lower in self.reverse_mapping:
                standard_field = self.reverse_mapping[header_lower]
                field_mapping[header_clean] = standard_field
                self.logger.debug(f"Mapped '{header_clean}' -> '{standard_field}'")
            else:
                unmapped_fields.append(header_clean)
                # Keep unmapped fields as-is for additional data
                field_mapping[header_clean] = header_clean.lower().replace(' ', '_')
        
        if unmapped_fields:
            self.logger.info(f"Unmapped fields (will be preserved): {unmapped_fields}")
        
        # Check for required fields
        required_fields = ['server_name', 'primary_owner']
        mapped_standard_fields = set(field_mapping.values())
        missing_required = [field for field in required_fields if field not in mapped_standard_fields]
        
        if missing_required:
            self.logger.warning(f"Missing required fields: {missing_required}")
        
        return field_mapping
    
    def normalize_csv_row(self, row: Dict[str, str], field_mapping: Dict[str, str]) -> Dict[str, str]:
        """
        Normalize a CSV row using the field mapping
        
        Args:
            row: Raw CSV row dictionary
            field_mapping: Mapping from CSV headers to standard field names
            
        Returns:
            Normalized row with standard field names
        """
        normalized_row = {}
        
        for csv_field, value in row.items():
            if csv_field in field_mapping:
                standard_field = field_mapping[csv_field]
                normalized_row[standard_field] = value.strip() if value else ''
            else:
                # Keep unmapped fields
                clean_field = csv_field.lower().replace(' ', '_')
                normalized_row[clean_field] = value.strip() if value else ''
        
        return normalized_row
    
    def suggest_field_mappings(self, csv_headers: List[str]) -> Dict[str, List[str]]:
        """
        Suggest possible field mappings for ambiguous headers
        
        Args:
            csv_headers: List of CSV column headers
            
        Returns:
            Dictionary of suggestions for unmapped fields
        """
        suggestions = {}
        
        for header in csv_headers:
            header_clean = header.strip()
            header_lower = header_clean.lower()
            
            if header_lower not in self.reverse_mapping:
                # Find similar field names using fuzzy matching
                possible_matches = []
                
                for standard_field, variants in self.field_mappings.items():
                    for variant in variants:
                        if self._is_similar(header_lower, variant.lower()):
                            possible_matches.append((standard_field, variant))
                
                if possible_matches:
                    suggestions[header_clean] = possible_matches
        
        return suggestions
    
    def _is_similar(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """
        Check if two strings are similar (simple similarity check)
        """
        # Simple similarity based on common words and character overlap
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        
        if words1 and words2:
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            similarity = intersection / union if union > 0 else 0
            return similarity >= threshold
        
        return False
    
    def validate_required_fields(self, normalized_row: Dict[str, str]) -> List[str]:
        """
        Validate that required fields are present and have values
        
        Args:
            normalized_row: Normalized CSV row
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = {
            'server_name': 'Server Name is required',
            'primary_owner': 'Primary Owner is required'
        }
        
        for field, error_msg in required_fields.items():
            if field not in normalized_row or not normalized_row[field].strip():
                errors.append(error_msg)
        
        # Validate email formats for owner fields
        email_fields = ['primary_owner', 'secondary_owner']
        for field in email_fields:
            if field in normalized_row and normalized_row[field]:
                email = normalized_row[field].strip()
                if email and '@' not in email:
                    errors.append(f"{field} should be a valid email address: {email}")
        
        return errors
    
    def get_supported_fields(self) -> Dict[str, List[str]]:
        """
        Get list of all supported field mappings
        
        Returns:
            Dictionary of standard fields and their supported CSV variants
        """
        return self.field_mappings.copy()
    
    def add_custom_mapping(self, standard_field: str, csv_variants: List[str]):
        """
        Add custom field mapping
        
        Args:
            standard_field: Standard internal field name
            csv_variants: List of CSV field variants that map to this standard field
        """
        if standard_field not in self.field_mappings:
            self.field_mappings[standard_field] = []
        
        self.field_mappings[standard_field].extend(csv_variants)
        
        # Update reverse mapping
        for variant in csv_variants:
            self.reverse_mapping[variant.lower()] = standard_field
        
        self.logger.info(f"Added custom mapping for '{standard_field}': {csv_variants}")
    
    def extract_external_fields_only(self, csv_headers: List[str]) -> Dict[str, str]:
        """
        Map only external fields that should come from source CSV
        
        Args:
            csv_headers: List of CSV column headers
            
        Returns:
            Dictionary mapping CSV headers to external field names only
        """
        all_mappings = self.map_csv_fields(csv_headers)
        
        # Filter to only external fields
        external_mappings = {}
        for csv_field, standard_field in all_mappings.items():
            if standard_field in self.external_fields:
                external_mappings[csv_field] = standard_field
            # Keep unmapped fields that might be relevant
            elif standard_field not in self.external_fields and standard_field not in self.internal_fields:
                external_mappings[csv_field] = standard_field
        
        return external_mappings
    
    def get_external_fields(self) -> Set[str]:
        """Get set of fields that should come from external CSV"""
        return self.external_fields.copy()
    
    def get_internal_fields(self) -> Set[str]:
        """Get set of fields managed internally by the system"""
        return self.internal_fields.copy()
    
    def create_internal_field_defaults(self) -> Dict[str, str]:
        """
        Create default values for internal fields
        
        Returns:
            Dictionary with default values for all internal fields
        """
        defaults = {}
        
        # Quarter-specific defaults
        for q in ['1', '2', '3', '4']:
            defaults[f'q{q}_patch_date'] = ''
            defaults[f'q{q}_patch_time'] = ''
            defaults[f'q{q}_approval_status'] = 'Pending'
        
        # General defaults
        defaults.update({
            'current_quarter_status': 'Pending',
            'server_timezone': 'America/New_York',  # Default timezone
            'incident_ticket': '',
            'patcher_email': '',
            'primary_linux_user': '',
            'secondary_linux_user': '',
            'last_sync_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'sync_status': 'imported',
            'operating_system': '',
            'environment': 'Production'  # Default environment
        })
        
        return defaults
    
    def merge_external_with_existing(self, external_data: Dict[str, str], existing_data: Dict[str, str] = None) -> Dict[str, str]:
        """
        Merge external CSV data with existing internal data
        
        Args:
            external_data: Data from external CSV (mapped to standard fields)
            existing_data: Existing internal data (optional)
            
        Returns:
            Complete server record with external + internal fields
        """
        # Start with defaults
        merged_data = self.create_internal_field_defaults()
        
        # Add existing internal data if provided
        if existing_data:
            for field, value in existing_data.items():
                if field in self.internal_fields and value:
                    merged_data[field] = value
        
        # Add external data (this overwrites any defaults)
        merged_data.update(external_data)
        
        # Update sync timestamp
        merged_data['last_sync_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        merged_data['sync_status'] = 'synced'
        
        return merged_data
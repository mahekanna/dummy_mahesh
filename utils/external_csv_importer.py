# utils/external_csv_importer.py
import os
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from utils.logger import Logger
from utils.csv_field_mapper import CSVFieldMapper
from utils.csv_handler import CSVHandler
from config.settings import Config

class ExternalCSVImporter:
    """
    Import external CSV files containing only source data fields
    Merges with existing internal patching data
    """
    
    def __init__(self):
        self.logger = Logger('external_csv_importer')
        self.field_mapper = CSVFieldMapper()
        self.csv_handler = CSVHandler()
        
    def import_external_csv(self, external_csv_path: str, preserve_internal_data: bool = True) -> Tuple[bool, str]:
        """
        Import external CSV with only source data fields
        
        Args:
            external_csv_path: Path to external CSV file
            preserve_internal_data: Whether to preserve existing internal data
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not os.path.exists(external_csv_path):
                return False, f"External CSV file not found: {external_csv_path}"
            
            # Read existing data if preserving internal data
            existing_servers = {}
            if preserve_internal_data and os.path.exists(Config.CSV_FILE_PATH):
                try:
                    current_servers = self.csv_handler.read_servers(normalize_fields=True)
                    existing_servers = {s.get('server_name', ''): s for s in current_servers}
                    self.logger.info(f"Loaded {len(existing_servers)} existing servers for merge")
                except Exception as e:
                    self.logger.warning(f"Could not load existing data: {e}")
            
            # Analyze external CSV structure
            self.logger.info("Analyzing external CSV structure...")
            analysis = self._analyze_external_csv(external_csv_path)
            
            if 'error' in analysis:
                return False, f"Error analyzing external CSV: {analysis['error']}"
            
            # Validate required external fields
            missing_required = []
            external_fields = self.field_mapper.get_external_fields()
            required_external = {'server_name', 'primary_owner'}  # Minimum required
            
            mapped_fields = set(analysis['external_field_mapping'].values())
            for required_field in required_external:
                if required_field not in mapped_fields:
                    missing_required.append(required_field)
            
            if missing_required:
                return False, f"Missing required fields in external CSV: {missing_required}"
            
            # Import external data
            external_servers = self._read_external_csv(external_csv_path, analysis['external_field_mapping'])
            
            if not external_servers:
                return False, "No valid servers found in external CSV"
            
            # Merge with existing data
            merged_servers = self._merge_external_with_existing(external_servers, existing_servers)
            
            # Write merged data
            success = self.csv_handler.write_servers(merged_servers)
            
            if success:
                message = f"Successfully imported {len(external_servers)} servers from external CSV"
                if preserve_internal_data:
                    message += f" (preserved existing internal data for {len(existing_servers)} servers)"
                return True, message
            else:
                return False, "Failed to write merged server data"
                
        except Exception as e:
            self.logger.error(f"Error importing external CSV: {e}")
            return False, f"Import error: {str(e)}"
    
    def _analyze_external_csv(self, csv_path: str) -> Dict:
        """Analyze external CSV structure and field mappings"""
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames or []
                
                # Get sample data
                sample_rows = []
                for i, row in enumerate(reader):
                    if i >= 3:
                        break
                    sample_rows.append(row)
            
            # Map only external fields
            external_field_mapping = self.field_mapper.extract_external_fields_only(headers)
            
            # Analyze coverage
            external_fields = self.field_mapper.get_external_fields()
            mapped_external_fields = set(external_field_mapping.values()).intersection(external_fields)
            missing_external_fields = external_fields - mapped_external_fields
            
            return {
                'total_headers': len(headers),
                'headers': headers,
                'sample_data': sample_rows,
                'external_field_mapping': external_field_mapping,
                'mapped_external_fields': len(mapped_external_fields),
                'missing_external_fields': list(missing_external_fields),
                'unmapped_headers': [h for h in headers if h not in external_field_mapping]
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _read_external_csv(self, csv_path: str, field_mapping: Dict[str, str]) -> List[Dict]:
        """Read external CSV and extract only mapped external fields"""
        servers = []
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Extract only external fields
                        external_data = {}
                        
                        for csv_field, standard_field in field_mapping.items():
                            value = row.get(csv_field, '').strip()
                            external_data[standard_field] = value
                        
                        # Validate required fields
                        server_name = external_data.get('server_name', '').strip()
                        primary_owner = external_data.get('primary_owner', '').strip()
                        
                        if not server_name:
                            self.logger.warning(f"Row {row_num}: Missing server name, skipping")
                            continue
                        
                        if not primary_owner:
                            self.logger.warning(f"Row {row_num}: Missing primary owner for {server_name}")
                        
                        servers.append(external_data)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing row {row_num}: {e}")
                        continue
            
            self.logger.info(f"Successfully read {len(servers)} servers from external CSV")
            return servers
            
        except Exception as e:
            self.logger.error(f"Error reading external CSV: {e}")
            return []
    
    def _merge_external_with_existing(self, external_servers: List[Dict], existing_servers: Dict[str, Dict]) -> List[Dict]:
        """Merge external data with existing internal data"""
        merged_servers = []
        
        for external_data in external_servers:
            server_name = external_data.get('server_name', '')
            
            # Get existing data for this server
            existing_data = existing_servers.get(server_name, {})
            
            # Merge external with existing internal data
            merged_server = self.field_mapper.merge_external_with_existing(external_data, existing_data)
            
            merged_servers.append(merged_server)
            
            if server_name in existing_servers:
                self.logger.debug(f"Merged external data with existing internal data for {server_name}")
            else:
                self.logger.debug(f"Created new server record with defaults for {server_name}")
        
        # Add any existing servers not in external CSV (if preserving)
        external_server_names = {s.get('server_name', '') for s in external_servers}
        for server_name, existing_server in existing_servers.items():
            if server_name not in external_server_names:
                merged_servers.append(existing_server)
                self.logger.debug(f"Preserved existing server not in external CSV: {server_name}")
        
        self.logger.info(f"Merged data for {len(merged_servers)} total servers")
        return merged_servers
    
    def get_import_report(self, external_csv_path: str) -> str:
        """Generate detailed import analysis report"""
        if not os.path.exists(external_csv_path):
            return f"Error: External CSV file not found: {external_csv_path}"
        
        analysis = self._analyze_external_csv(external_csv_path)
        
        if 'error' in analysis:
            return f"Error analyzing CSV: {analysis['error']}"
        
        external_fields = self.field_mapper.get_external_fields()
        internal_fields = self.field_mapper.get_internal_fields()
        
        report_lines = [
            "External CSV Import Analysis",
            "=" * 50,
            f"File: {external_csv_path}",
            f"Total columns: {analysis['total_headers']}",
            f"External fields mapped: {analysis['mapped_external_fields']}/{len(external_fields)}",
            "",
            "External Field Mappings (Source Data):",
            "-" * 40
        ]
        
        for csv_field, standard_field in analysis['external_field_mapping'].items():
            if standard_field in external_fields:
                status = "✓ EXTERNAL"
            else:
                status = "• EXTRA"
            report_lines.append(f"{status} '{csv_field}' -> '{standard_field}'")
        
        if analysis['missing_external_fields']:
            report_lines.extend([
                "",
                "Missing External Fields:",
                "-" * 25
            ])
            for field in analysis['missing_external_fields']:
                report_lines.append(f"✗ '{field}' not found in external CSV")
        
        if analysis['unmapped_headers']:
            report_lines.extend([
                "",
                "Unmapped Headers (will be ignored):",
                "-" * 35
            ])
            for header in analysis['unmapped_headers']:
                report_lines.append(f"? '{header}' (not a known external field)")
        
        report_lines.extend([
            "",
            "Internal Fields (Auto-Generated):",
            "-" * 35,
            "These fields will be initialized with defaults or preserved from existing data:"
        ])
        
        for field in sorted(internal_fields):
            report_lines.append(f"• {field}")
        
        # Sample data preview
        if analysis['sample_data']:
            report_lines.extend([
                "",
                "Sample External Data:",
                "-" * 22
            ])
            for i, row in enumerate(analysis['sample_data'][:2], 1):
                mapped_row = {}
                for csv_field, standard_field in analysis['external_field_mapping'].items():
                    if standard_field in external_fields:
                        mapped_row[standard_field] = row.get(csv_field, '')
                
                report_lines.append(f"Row {i}: {mapped_row}")
        
        return "\n".join(report_lines)
    
    def validate_external_csv(self, external_csv_path: str) -> Tuple[bool, List[str]]:
        """Validate external CSV for import readiness"""
        issues = []
        
        if not os.path.exists(external_csv_path):
            return False, [f"File not found: {external_csv_path}"]
        
        try:
            analysis = self._analyze_external_csv(external_csv_path)
            
            if 'error' in analysis:
                return False, [f"Analysis error: {analysis['error']}"]
            
            # Check required external fields
            required_fields = {'server_name', 'primary_owner'}
            mapped_fields = set(analysis['external_field_mapping'].values())
            
            missing_required = required_fields - mapped_fields
            if missing_required:
                issues.append(f"Missing required fields: {', '.join(missing_required)}")
            
            # Check for empty server names
            external_servers = self._read_external_csv(external_csv_path, analysis['external_field_mapping'])
            empty_names = [i+1 for i, s in enumerate(external_servers) if not s.get('server_name', '').strip()]
            
            if empty_names:
                issues.append(f"Rows with empty server names: {', '.join(map(str, empty_names[:5]))}")
            
            # Check for duplicate server names
            server_names = [s.get('server_name', '') for s in external_servers]
            duplicates = list(set([name for name in server_names if server_names.count(name) > 1 and name]))
            
            if duplicates:
                issues.append(f"Duplicate server names: {', '.join(duplicates[:5])}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            return False, [f"Validation error: {str(e)}"]
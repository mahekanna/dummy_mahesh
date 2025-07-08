# utils/csv_handler.py
import csv
import os
from typing import List, Dict, Optional
from config.settings import Config
from utils.csv_field_mapper import CSVFieldMapper
from utils.logger import Logger

class CSVHandler:
    def __init__(self, csv_file_path=None):
        self.csv_file_path = csv_file_path or Config.CSV_FILE_PATH
        self.field_mapper = CSVFieldMapper()
        self.logger = Logger('csv_handler')
        self._field_mapping = None
    
    def read_servers(self, normalize_fields=True) -> List[Dict]:
        """
        Read servers from CSV file with intelligent field mapping
        
        Args:
            normalize_fields: Whether to normalize field names to standard format
            
        Returns:
            List of server dictionaries with normalized field names
        """
        servers = []
        
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {self.csv_file_path}")
        
        with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # Get field mapping on first read
            if self._field_mapping is None and normalize_fields:
                headers = reader.fieldnames
                self._field_mapping = self.field_mapper.map_csv_fields(headers)
                self.logger.info(f"Mapped {len(self._field_mapping)} CSV fields")
                
                # Log field mapping for debugging
                for csv_field, standard_field in self._field_mapping.items():
                    if csv_field.lower().replace(' ', '_') != standard_field:
                        self.logger.debug(f"Field mapping: '{csv_field}' -> '{standard_field}'")
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Strip whitespace from all values
                    cleaned_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                    
                    if normalize_fields and self._field_mapping:
                        # Normalize field names
                        normalized_row = self.field_mapper.normalize_csv_row(cleaned_row, self._field_mapping)
                        
                        # Validate required fields
                        validation_errors = self.field_mapper.validate_required_fields(normalized_row)
                        if validation_errors:
                            for error in validation_errors:
                                self.logger.warning(f"Row {row_num}: {error}")
                        
                        servers.append(normalized_row)
                    else:
                        servers.append(cleaned_row)
                        
                except Exception as e:
                    self.logger.error(f"Error processing row {row_num}: {e}")
                    continue
        
        self.logger.info(f"Successfully read {len(servers)} servers from CSV")
        return servers
    
    def write_servers(self, servers: List[Dict], output_path: Optional[str] = None) -> bool:
        """
        Write servers to CSV file
        
        Args:
            servers: List of server dictionaries
            output_path: Optional output file path (defaults to configured path)
            
        Returns:
            True if successful, False otherwise
        """
        if not servers:
            self.logger.warning("No servers to write")
            return False
        
        output_file = output_path or self.csv_file_path
        
        try:
            # Determine fieldnames - preserve order from first server
            fieldnames = list(servers[0].keys())
            
            # Ensure required fields are first
            required_fields = ['server_name', 'primary_owner', 'secondary_owner']
            ordered_fieldnames = []
            
            # Add required fields first (if they exist)
            for field in required_fields:
                if field in fieldnames:
                    ordered_fieldnames.append(field)
                    fieldnames.remove(field)
            
            # Add remaining fields
            ordered_fieldnames.extend(fieldnames)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=ordered_fieldnames)
                writer.writeheader()
                writer.writerows(servers)
            
            self.logger.info(f"Successfully wrote {len(servers)} servers to {output_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing servers to CSV: {e}")
            return False
    
    def update_server_status(self, server_name: str, quarter: str, status: str) -> bool:
        """Update server patching status"""
        servers = self.read_servers()
        updated = False
        
        for server in servers:
            if server['Server Name'] == server_name:
                server['Current Quarter Patching Status'] = status
                updated = True
                break
        
        if updated:
            self.write_servers(servers)
            return True
        
        return False
    
    def get_servers_by_owner(self, owner_email: str) -> List[Dict]:
        """Get all servers for a specific owner"""
        servers = self.read_servers()
        owner_servers = []
        
        for server in servers:
            if (server.get('primary_owner') == owner_email or 
                server.get('secondary_owner') == owner_email):
                owner_servers.append(server)
        
        return owner_servers
    
    def analyze_csv_structure(self) -> Dict:
        """
        Analyze CSV structure and provide field mapping information
        
        Returns:
            Dictionary with CSV analysis results
        """
        if not os.path.exists(self.csv_file_path):
            return {'error': f"CSV file not found: {self.csv_file_path}"}
        
        try:
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                headers = reader.fieldnames or []
                
                # Get first few rows for sample data
                sample_rows = []
                for i, row in enumerate(reader):
                    if i >= 3:  # Get first 3 rows
                        break
                    sample_rows.append(row)
            
            # Map fields
            field_mapping = self.field_mapper.map_csv_fields(headers)
            suggestions = self.field_mapper.suggest_field_mappings(headers)
            
            # Analyze field coverage
            mapped_standard_fields = set(field_mapping.values())
            supported_fields = set(self.field_mapper.get_supported_fields().keys())
            missing_fields = supported_fields - mapped_standard_fields
            
            analysis = {
                'file_path': self.csv_file_path,
                'total_headers': len(headers),
                'headers': headers,
                'sample_data': sample_rows,
                'field_mapping': field_mapping,
                'mapped_fields': len([f for f in field_mapping.values() if f in supported_fields]),
                'unmapped_headers': [h for h in headers if field_mapping.get(h, '').replace('_', ' ').lower() not in [f.replace('_', ' ').lower() for f in supported_fields]],
                'missing_standard_fields': list(missing_fields),
                'suggestions': suggestions,
                'required_fields_present': {
                    'server_name': 'server_name' in mapped_standard_fields,
                    'primary_owner': 'primary_owner' in mapped_standard_fields
                }
            }
            
            return analysis
            
        except Exception as e:
            return {'error': f"Error analyzing CSV: {str(e)}"}
    
    def get_field_mapping_report(self) -> str:
        """
        Generate a human-readable field mapping report
        
        Returns:
            Formatted report string
        """
        analysis = self.analyze_csv_structure()
        
        if 'error' in analysis:
            return f"Error: {analysis['error']}"
        
        report_lines = [
            "CSV Field Mapping Report",
            "=" * 50,
            f"File: {analysis['file_path']}",
            f"Total Headers: {analysis['total_headers']}",
            f"Mapped Fields: {analysis['mapped_fields']}",
            "",
            "Field Mappings:",
            "-" * 20
        ]
        
        for csv_field, standard_field in analysis['field_mapping'].items():
            if standard_field in self.field_mapper.get_supported_fields():
                status = "✓ MAPPED"
            else:
                status = "• PRESERVED"
            report_lines.append(f"{status} '{csv_field}' -> '{standard_field}'")
        
        if analysis['unmapped_headers']:
            report_lines.extend([
                "",
                "Unmapped Headers:",
                "-" * 20
            ])
            for header in analysis['unmapped_headers']:
                report_lines.append(f"? '{header}' (preserved as-is)")
        
        if analysis['missing_standard_fields']:
            report_lines.extend([
                "",
                "Missing Standard Fields:",
                "-" * 25
            ])
            for field in analysis['missing_standard_fields']:
                report_lines.append(f"✗ '{field}' not found in CSV")
        
        if analysis['suggestions']:
            report_lines.extend([
                "",
                "Suggestions for Unmapped Fields:",
                "-" * 35
            ])
            for csv_field, suggestions in analysis['suggestions'].items():
                report_lines.append(f"'{csv_field}' might map to:")
                for standard_field, variant in suggestions[:3]:  # Show top 3 suggestions
                    report_lines.append(f"  - {standard_field} (similar to '{variant}')")
        
        # Required fields check
        report_lines.extend([
            "",
            "Required Fields Check:",
            "-" * 22
        ])
        
        for field, present in analysis['required_fields_present'].items():
            status = "✓ FOUND" if present else "✗ MISSING"
            report_lines.append(f"{status} {field}")
        
        return "\n".join(report_lines)
    
    def add_custom_field_mapping(self, standard_field: str, csv_variants: List[str]):
        """
        Add custom field mapping for specific CSV format
        
        Args:
            standard_field: Standard internal field name
            csv_variants: List of CSV field names that should map to this field
        """
        self.field_mapper.add_custom_mapping(standard_field, csv_variants)
        # Reset field mapping to force remapping on next read
        self._field_mapping = None
        self.logger.info(f"Added custom mapping for '{standard_field}': {csv_variants}")
    
    def get_supported_fields(self) -> Dict[str, List[str]]:
        """
        Get all supported field mappings
        
        Returns:
            Dictionary of standard fields and their supported CSV variants
        """
        return self.field_mapper.get_supported_fields()

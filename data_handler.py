"""
CSV Data Handler for Web Form Automation System
"""

import pandas as pd
import logging
from typing import List, Optional
from pathlib import Path
from config import Config

logger = logging.getLogger(__name__)

class DataHandler:
    """Handles CSV data loading, validation, and batch processing"""
    
    def __init__(self, csv_path: str):
        self.csv_path = Path(csv_path)
        self.data = []
        self.total_sets = 0
        
    def load_csv_data(self) -> bool:
        """
        Load and validate CSV data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.csv_path.exists():
                logger.error(f"CSV file not found: {self.csv_path}")
                return False
            
            # Load CSV with pandas
            df = pd.read_csv(
                self.csv_path, 
                encoding=Config.CSV_ENCODING,
                header=None
            )
            
            # Validate data structure
            if not self._validate_dataframe(df):
                return False
            
            # Convert to list of lists
            self.data = df.values.tolist()
            self.total_sets = len(self.data)
            
            logger.info(f"Successfully loaded {self.total_sets} sets from {self.csv_path}")
            return True
            
        except pd.errors.EmptyDataError:
            logger.error("CSV file is empty")
            return False
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading CSV: {e}")
            return False
    
    def _validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        Validate the loaded dataframe
        
        Args:
            df: Pandas DataFrame to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check if dataframe is empty
        if df.empty:
            logger.error("CSV data is empty")
            return False
        
        # Check number of columns
        if df.shape[1] != Config.EXPECTED_COLUMNS:
            logger.error(f"Expected {Config.EXPECTED_COLUMNS} columns, got {df.shape[1]}")
            return False
        
        # Check for valid values
        for index, row in df.iterrows():
            for col_index, value in enumerate(row):
                if pd.isna(value):
                    logger.error(f"Found NaN value at row {index + 1}, column {col_index + 1}")
                    return False
                
                if value not in Config.VALID_VALUES:
                    logger.error(f"Invalid value '{value}' at row {index + 1}, column {col_index + 1}. Expected: {Config.VALID_VALUES}")
                    return False
        
        logger.info(f"Data validation passed: {df.shape[0]} rows, {df.shape[1]} columns")
        return True
    
    def split_data_into_batches(self, batch_size: Optional[int] = None) -> List[List[List[int]]]:
        """
        Split data into batches for processing
        
        Args:
            batch_size: Maximum number of sets per batch (default: Config.MAX_SETS_PER_BATCH)
            
        Returns:
            List of batches, where each batch is a list of sets
        """
        if batch_size is None:
            batch_size = Config.MAX_SETS_PER_BATCH
        
        if not self.data:
            logger.warning("No data to split into batches")
            return []
        
        batches = []
        for i in range(0, len(self.data), batch_size):
            batch = self.data[i:i + batch_size]
            batches.append(batch)
            logger.debug(f"Created batch {len(batches)} with {len(batch)} sets")
        
        logger.info(f"Split {self.total_sets} sets into {len(batches)} batches")
        return batches
    
    def get_data_info(self) -> dict:
        """
        Get information about the loaded data
        
        Returns:
            dict: Data information
        """
        if not self.data:
            return {"error": "No data loaded"}
        
        return {
            "total_sets": self.total_sets,
            "games_per_set": Config.EXPECTED_COLUMNS,
            "file_path": str(self.csv_path),
            "estimated_batches": (self.total_sets + Config.MAX_SETS_PER_BATCH - 1) // Config.MAX_SETS_PER_BATCH
        }
    
    def validate_single_set(self, set_data: List[int]) -> bool:
        """
        Validate a single set of data
        
        Args:
            set_data: List of values for one set
            
        Returns:
            bool: True if valid, False otherwise
        """
        if len(set_data) != Config.EXPECTED_COLUMNS:
            logger.error(f"Set has {len(set_data)} values, expected {Config.EXPECTED_COLUMNS}")
            return False
        
        for index, value in enumerate(set_data):
            if value not in Config.VALID_VALUES:
                logger.error(f"Invalid value '{value}' at position {index + 1}. Expected: {Config.VALID_VALUES}")
                return False
        
        return True
    
    def preview_data(self, num_rows: int = 5) -> List[List[int]]:
        """
        Get a preview of the data
        
        Args:
            num_rows: Number of rows to preview
            
        Returns:
            List of first few data rows
        """
        if not self.data:
            return []
        
        return self.data[:min(num_rows, len(self.data))]
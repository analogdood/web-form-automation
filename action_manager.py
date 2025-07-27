"""
Action Recording and Playback System for Web Form Automation
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Supported action types for recording and playback"""
    CLICK = "click"
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_URL_CHANGE = "wait_for_url_change"
    WAIT_FOR_ALERT = "wait_for_alert"
    INPUT_TEXT = "input_text"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    SLEEP = "sleep"
    CONFIRM_CHECKBOX = "confirm_checkbox"
    SUBMIT_FORM = "submit_form"

@dataclass
class ActionStep:
    """Single action step in a sequence"""
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    description: Optional[str] = None
    wait_before: float = 0.0
    wait_after: float = 1.0
    timeout: float = 10.0
    optional: bool = False
    retry_count: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action step to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionStep':
        """Create action step from dictionary"""
        return cls(**data)

@dataclass
class ActionSequence:
    """Complete sequence of actions for batch processing"""
    metadata: Dict[str, Any]
    batch_actions: List[ActionStep]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert action sequence to dictionary"""
        return {
            "metadata": self.metadata,
            "batch_actions": [action.to_dict() for action in self.batch_actions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionSequence':
        """Create action sequence from dictionary"""
        return cls(
            metadata=data.get("metadata", {}),
            batch_actions=[ActionStep.from_dict(action) for action in data.get("batch_actions", [])]
        )

class ActionFileManager:
    """Manages loading and saving of action files"""
    
    def __init__(self, actions_dir: str = "actions"):
        self.actions_dir = Path(actions_dir)
        self.actions_dir.mkdir(exist_ok=True)
    
    def save_actions(self, actions: ActionSequence, filename: str) -> bool:
        """
        Save action sequence to JSON file
        
        Args:
            actions: ActionSequence to save
            filename: Output filename
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            filepath = self.actions_dir / filename
            
            # Add metadata
            actions.metadata.update({
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "total_actions": len(actions.batch_actions)
            })
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(actions.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Actions saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save actions: {e}")
            return False
    
    def load_actions(self, filename: str) -> Optional[ActionSequence]:
        """
        Load action sequence from JSON file
        
        Args:
            filename: Input filename
            
        Returns:
            ActionSequence if successful, None otherwise
        """
        try:
            filepath = self.actions_dir / filename
            
            if not filepath.exists():
                logger.error(f"Action file not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            actions = ActionSequence.from_dict(data)
            logger.info(f"Actions loaded from {filepath}")
            return actions
            
        except Exception as e:
            logger.error(f"Failed to load actions: {e}")
            return None
    
    def list_action_files(self) -> List[str]:
        """List all available action files"""
        try:
            return [f.name for f in self.actions_dir.glob("*.json")]
        except Exception as e:
            logger.error(f"Failed to list action files: {e}")
            return []
    
    def create_sample_actions(self) -> ActionSequence:
        """Create sample action sequence for testing"""
        metadata = {
            "name": "Sample Web Form Actions",
            "description": "Sample action sequence for web form processing",
            "site_url": "https://example.com/form"
        }
        
        batch_actions = [
            ActionStep(
                action=ActionType.CLICK.value,
                selector="button.submit-form",
                description="Click form submit button",
                wait_after=3.0
            ),
            ActionStep(
                action=ActionType.WAIT_FOR_URL_CHANGE.value,
                value="confirmation",
                description="Wait for confirmation page",
                timeout=15.0
            ),
            ActionStep(
                action=ActionType.CONFIRM_CHECKBOX.value,
                selector="input[name='confirm']",
                description="Check confirmation checkbox",
                optional=True
            ),
            ActionStep(
                action=ActionType.CLICK.value,
                selector="button.add-next",
                description="Click add next voting button",
                wait_after=2.0
            ),
            ActionStep(
                action=ActionType.WAIT_FOR_ELEMENT.value,
                selector="form.voting-form",
                description="Wait for next voting form to appear",
                timeout=10.0
            )
        ]
        
        return ActionSequence(metadata=metadata, batch_actions=batch_actions)

class ActionValidator:
    """Validates action sequences for correctness"""
    
    @staticmethod
    def validate_action_step(step: ActionStep) -> List[str]:
        """
        Validate single action step
        
        Args:
            step: ActionStep to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check required fields
        if not step.action:
            errors.append("Action type is required")
        
        # Validate action-specific requirements
        if step.action in [ActionType.CLICK.value, ActionType.WAIT_FOR_ELEMENT.value, 
                          ActionType.CONFIRM_CHECKBOX.value]:
            if not step.selector:
                errors.append(f"Selector is required for {step.action} action")
        
        if step.action == ActionType.INPUT_TEXT.value:
            if not step.selector or not step.value:
                errors.append("Both selector and value are required for input_text action")
        
        # Validate numeric fields
        if step.wait_before < 0:
            errors.append("wait_before must be non-negative")
        
        if step.wait_after < 0:
            errors.append("wait_after must be non-negative")
        
        if step.timeout <= 0:
            errors.append("timeout must be positive")
        
        if step.retry_count < 1:
            errors.append("retry_count must be at least 1")
        
        return errors
    
    @staticmethod
    def validate_action_sequence(sequence: ActionSequence) -> List[str]:
        """
        Validate complete action sequence
        
        Args:
            sequence: ActionSequence to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check metadata
        if not sequence.metadata:
            errors.append("Metadata is required")
        
        # Check actions exist
        if not sequence.batch_actions:
            errors.append("At least one action is required")
        
        # Validate each action step
        for i, step in enumerate(sequence.batch_actions):
            step_errors = ActionValidator.validate_action_step(step)
            for error in step_errors:
                errors.append(f"Step {i+1}: {error}")
        
        return errors
    
    @staticmethod
    def is_valid_sequence(sequence: ActionSequence) -> bool:
        """Check if action sequence is valid"""
        return len(ActionValidator.validate_action_sequence(sequence)) == 0

# Utility functions for action management
def create_action_step(action_type: ActionType, selector: str = None, 
                      value: str = None, description: str = None, **kwargs) -> ActionStep:
    """Helper function to create action step"""
    return ActionStep(
        action=action_type.value,
        selector=selector,
        value=value,
        description=description,
        **kwargs
    )

def load_or_create_sample_actions(filename: str = "sample_actions.json") -> ActionSequence:
    """Load actions from file or create sample if file doesn't exist"""
    file_manager = ActionFileManager()
    
    # Try to load existing file
    actions = file_manager.load_actions(filename)
    
    if actions is None:
        # Create and save sample actions
        logger.info(f"Creating sample action file: {filename}")
        actions = file_manager.create_sample_actions()
        file_manager.save_actions(actions, filename)
    
    return actions
import re
from typing import Dict, Any


def validate_meeting_id(meeting_id: str) -> bool:
    """
    Validate meeting ID format.
    
    Args:
        meeting_id: Meeting identifier to validate
        
    Returns:
        True if meeting ID is valid, False otherwise
    """
    if not meeting_id or not isinstance(meeting_id, str):
        return False
    
    # Check if meeting ID is reasonable length and contains valid characters
    if len(meeting_id) < 5 or len(meeting_id) > 100:
        return False
    
    # Allow alphanumeric characters, hyphens, and underscores
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, meeting_id))


def format_error_response(error: Exception, meeting_id: str = None) -> Dict[str, Any]:
    """
    Format error response for API endpoints.
    
    Args:
        error: Exception that occurred
        meeting_id: Optional meeting ID for context
        
    Returns:
        Formatted error response dictionary
    """
    response = {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__
    }
    
    if meeting_id:
        response["meeting_id"] = meeting_id
    
    return response


def sanitize_system_prompt(prompt: str) -> str:
    """
    Sanitize system prompt to remove potentially harmful content.
    
    Args:
        prompt: Raw system prompt
        
    Returns:
        Sanitized system prompt
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    
    # Remove excessive whitespace
    prompt = " ".join(prompt.split())
    
    # Limit length
    max_length = 2000
    if len(prompt) > max_length:
        prompt = prompt[:max_length]
    
    return prompt


def parse_model_parameters(temperature: float, top_p: float, top_k: float) -> Dict[str, Any]:
    """
    Parse and validate model parameters.
    
    Args:
        temperature: Temperature parameter (0.0-2.0)
        top_p: Top-p parameter (0.0-1.0)
        top_k: Top-k parameter (>= 0)
        
    Returns:
        Dictionary of validated parameters
    """
    # Clamp values to valid ranges
    temperature = max(0.0, min(2.0, temperature))
    top_p = max(0.0, min(1.0, top_p))
    top_k = max(0.0, top_k)
    
    return {
        "temperature": temperature,
        "top_p": top_p,
        "top_k": int(top_k)
    } 
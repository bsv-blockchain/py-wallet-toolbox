"""Validation utility functions for BRC-100 parameters.

Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
Reference: toolbox/go-wallet-toolbox/pkg/internal/validate/
"""

from typing import Any, Dict, Optional

from bsv_wallet_toolbox.errors import InvalidParameterError


def validate_originator(originator: Optional[str]) -> None:
    """Validate originator parameter according to BRC-100 specifications.
    
    The originator parameter must be:
    - None (optional) or a string
    - At most 250 bytes in length when encoded as UTF-8
    
    Reference: toolbox/ts-wallet-toolbox/src/utility/utilityHelpers.ts
               function validateOriginator
    
    Args:
        originator: Originator domain name (optional)
        
    Raises:
        InvalidParameterError: If originator is invalid
        
    Example:
        >>> validate_originator(None)  # OK
        >>> validate_originator("example.com")  # OK
        >>> validate_originator("a" * 251)  # Raises InvalidParameterError
    """
    if originator is None:
        return
    
    if not isinstance(originator, str):
        raise InvalidParameterError("originator", "a string")
    
    # Check length in bytes (UTF-8 encoding)
    originator_bytes = originator.encode("utf-8")
    if len(originator_bytes) > 250:
        raise InvalidParameterError("originator", "at most 250 bytes in length")


def validate_basket_config(config: Dict[str, Any]) -> None:
    """Validate BasketConfiguration according to BRC-100 specifications.
    
    BasketConfiguration must have:
    - name: non-empty string, at least 1 character and at most 300 bytes
    
    Reference: toolbox/go-wallet-toolbox/pkg/internal/validate/validate_basket_config.go
               ValidateBasketConfiguration
    
    Args:
        config: BasketConfiguration dict containing 'name' field
        
    Raises:
        InvalidParameterError: If basket configuration is invalid
        
    Example:
        >>> validate_basket_config({"name": "MyBasket"})  # OK
        >>> validate_basket_config({"name": ""})  # Raises InvalidParameterError
        >>> validate_basket_config({"name": "a" * 301})  # Raises InvalidParameterError
    """
    if "name" not in config:
        raise InvalidParameterError("name", "required in basket configuration")
    
    name = config["name"]
    
    if not isinstance(name, str):
        raise InvalidParameterError("name", "a string")
    
    # Check minimum length
    if len(name) < 1:
        raise InvalidParameterError("name", "at least 1 character in length")
    
    # Check maximum length in bytes (UTF-8 encoding)
    name_bytes = name.encode("utf-8")
    if len(name_bytes) > 300:
        raise InvalidParameterError("name", "no more than 300 bytes in length")



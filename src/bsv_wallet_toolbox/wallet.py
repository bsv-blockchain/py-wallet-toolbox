"""BRC-100 compliant Bitcoin SV wallet implementation.

Reference: ts-wallet-toolbox/src/Wallet.ts
"""

from typing import Optional

from bsv.wallet.wallet_interface import GetVersionResult

from .errors import InvalidParameterError


class Wallet:
    """BRC-100 compliant wallet implementation.
    
    Implements the WalletInterface defined in bsv-sdk.
    
    Reference: ts-wallet-toolbox/src/Wallet.ts
    
    Note:
        Version is hardcoded as a class constant, matching TypeScript implementation.
        Python implementation uses "0.1.0" during development, will become "1.0.0"
        when all 28 methods are implemented.
        
    Example:
        >>> wallet = Wallet()
        >>> result = await wallet.get_version({})
        >>> print(result["version"])
        0.1.0
    """
    
    # Version constant (matches TypeScript's hardcoded return value)
    VERSION = "0.1.0"  # Will become "1.0.0" when all 28 methods are complete
    
    def __init__(self) -> None:
        """Initialize wallet.
        
        Note: Version is not configurable, it's a class constant.
        """
        pass  # No initialization needed for now
    
    async def get_version(
        self, 
        args: dict,  # Empty dict for getVersion
        originator: Optional[str] = None
    ) -> GetVersionResult:
        """Get wallet version.
        
        BRC-100 WalletInterface method implementation.
        
        Reference:
            - ts-wallet-toolbox/src/Wallet.ts
            - ts-wallet-toolbox/test/Wallet/get/getVersion.test.ts
        
        Args:
            args: Empty dict (getVersion takes no parameters)
            originator: Optional originator domain name (must be string under 250 bytes)
            
        Returns:
            Dictionary with 'version' key containing the version string
            
        Raises:
            InvalidParameterError: If originator is invalid
            
        Example:
            >>> wallet = Wallet()
            >>> result = await wallet.get_version({})
            >>> assert result == {"version": Wallet.VERSION}
        """
        # Validate originator
        if originator is not None:
            if not isinstance(originator, str):
                raise InvalidParameterError("originator", "must be a string")
            if len(originator.encode('utf-8')) > 250:
                raise InvalidParameterError("originator", "must be under 250 bytes")
        
        return {"version": self.VERSION}


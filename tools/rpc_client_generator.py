#!/usr/bin/env python3
"""RPC client generator for creating JSON-RPC client stubs.

Generates Python client code for making JSON-RPC calls to services,
similar to Go's RPC client generation.

Reference: go-wallet-toolbox/tools/client-gen/
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RPCClientGenerator:
    """Generates RPC client code from method specifications."""

    def __init__(self, output_dir: Path):
        """Initialize generator.

        Args:
            output_dir: Directory to write generated files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_rpc_client(self, service_name: str, methods: List[Dict[str, Any]]) -> str:
        """Generate RPC client class from method specifications.

        Args:
            service_name: Name of the service
            methods: List of method specifications

        Returns:
            Generated client code as string
        """
        client_name = f"{service_name}Client"

        lines = [
            '"""Generated RPC client for {service_name}."""',
            '',
            'import json',
            'from typing import Any, Dict, Optional',
            'import aiohttp',
            '',
            '',
            f'class {client_name}:',
            f'    """RPC client for {service_name} service."""',
            '',
            '    def __init__(self, base_url: str, session: Optional[aiohttp.ClientSession] = None):',
            '        """Initialize RPC client.',
            '',
            '        Args:',
            '            base_url: Base URL for the RPC service',
            '            session: Optional HTTP session to use',
            '        """',
            '        self.base_url = base_url.rstrip("/")',
            '        self._session = session',
            '        self._request_id = 0',
            '',
            '    async def __aenter__(self):',
            '        """Async context manager entry."""',
            '        if not self._session:',
            '            self._session = aiohttp.ClientSession()',
            '        return self',
            '',
            '    async def __aexit__(self, exc_type, exc_val, exc_tb):',
            '        """Async context manager exit."""',
            '        if self._session:',
            '            await self._session.close()',
            '',
            '    def _get_next_id(self) -> int:',
            '        """Get next request ID."""',
            '        self._request_id += 1',
            '        return self._request_id',
            '',
            '    async def _make_request(self, method: str, params: Any = None) -> Any:',
            '        """Make JSON-RPC request.',
            '',
            '        Args:',
            '            method: RPC method name',
            '            params: Method parameters',
            '',
            '        Returns:',
            '            RPC response result',
            '',
            '        Raises:',
            '            Exception: If RPC call fails',
            '        """',
            '        if not self._session:',
            '            raise RuntimeError("Client not in context manager")',
            '',
            '        request = {{',
            '            "jsonrpc": "2.0",',
            '            "id": self._get_next_id(),',
            '            "method": method,',
            '            "params": params or []',
            '        }}',
            '',
            '        async with self._session.post(',
            '            f"{{self.base_url}}/rpc",',
            '            json=request,',
            '            headers={{"Content-Type": "application/json"}}',
            '        ) as response:',
            '            if response.status != 200:',
            '                raise Exception(f"RPC call failed: HTTP {{response.status}}")',
            '',
            '            result = await response.json()',
            '            if "error" in result:',
            '                raise Exception(f"RPC error: {{result[\'error\']}}")',
            '',
            '            return result.get("result")',
            '',
        ]

        # Generate method implementations
        for method_spec in methods:
            method_name = method_spec['name']
            description = method_spec.get('description', f'Call {method_name} RPC method')
            params = method_spec.get('params', [])

            # Generate method signature
            param_list = []
            doc_params = []

            for param in params:
                param_name = param['name']
                param_type = param.get('type', 'Any')
                param_required = param.get('required', True)

                if param_required:
                    param_list.append(f'{param_name}: {param_type}')
                else:
                    param_list.append(f'{param_name}: Optional[{param_type}] = None')

                doc_params.append(f'        {param_name}: {param.get("description", param_name)}')

            params_str = ', '.join(param_list)
            method_signature = f'    async def {method_name}(self, {params_str}) -> Any:'

            lines.extend([
                '',
                method_signature,
                f'        """{description}',
                '',
                '        Args:',
            ])
            lines.extend(doc_params)
            lines.extend([
                '',
                '        Returns:',
                '            RPC method result',
                '        """',
                f'        params = {{}}',
            ])

            # Add parameter building
            for param in params:
                param_name = param['name']
                if param.get('required', True):
                    lines.append(f'        params["{param_name}"] = {param_name}')
                else:
                    lines.append(f'        if {param_name} is not None:')
                    lines.append(f'            params["{param_name}"] = {param_name}')

            lines.extend([
                f'        return await self._make_request("{method_name}", params)',
            ])

        return '\n'.join(lines)

    def write_file(self, filename: str, content: str) -> None:
        """Write content to a file in the output directory.

        Args:
            filename: Name of the file to write
            content: Content to write
        """
        output_path = self.output_dir / filename
        output_path.write_text(content)
        logger.info(f"Generated {output_path}")


def main():
    """Main entry point for the RPC client generator."""
    parser = argparse.ArgumentParser(description='Generate RPC client code')
    parser.add_argument('--output-dir', '-o', type=Path, default=Path('generated'),
                       help='Output directory for generated files')
    parser.add_argument('--service-name', required=True,
                       help='Name of the service to generate client for')
    parser.add_argument('--methods-file', type=Path,
                       help='JSON file containing method specifications')

    args = parser.parse_args()

    if not args.methods_file:
        # Generate example methods for demonstration
        methods = [
            {
                'name': 'get_height',
                'description': 'Get current blockchain height',
                'params': []
            },
            {
                'name': 'get_transaction',
                'description': 'Get transaction by ID',
                'params': [
                    {
                        'name': 'txid',
                        'type': 'str',
                        'description': 'Transaction ID',
                        'required': True
                    }
                ]
            },
            {
                'name': 'send_transaction',
                'description': 'Broadcast transaction to network',
                'params': [
                    {
                        'name': 'raw_tx',
                        'type': 'str',
                        'description': 'Raw transaction hex',
                        'required': True
                    }
                ]
            }
        ]
    else:
        with open(args.methods_file) as f:
            methods = json.load(f)

    generator = RPCClientGenerator(args.output_dir)
    content = generator.generate_rpc_client(args.service_name, methods)
    generator.write_file(f'{args.service_name.lower()}_client.py', content)


if __name__ == '__main__':
    main()

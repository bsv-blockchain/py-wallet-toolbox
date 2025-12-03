#!/usr/bin/env python3
"""Code generator for creating interface stubs and client code.

Generates Python interfaces and client stubs from type definitions,
similar to Go's code generation tools.

Reference: go-wallet-toolbox/tools/client-gen/
"""

import argparse
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Type, get_type_hints

logger = logging.getLogger(__name__)


class InterfaceGenerator:
    """Generates interface stubs and client code from Python classes."""

    def __init__(self, output_dir: Path):
        """Initialize generator.

        Args:
            output_dir: Directory to write generated files
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_interface_stub(self, cls: Type, name: str) -> str:
        """Generate a protocol/interface stub from a class.

        Args:
            cls: Class to generate interface for
            name: Name for the generated interface

        Returns:
            Generated interface code as string
        """
        methods = self._extract_methods(cls)

        lines = [
            '"""Generated interface stub."""',
            '',
            'from abc import ABC, abstractmethod',
            'from typing import Any',
            '',
            '',
            f'class {name}(ABC):',
            f'    """Generated interface for {cls.__name__}."""',
            '',
        ]

        for method_name, method_info in methods.items():
            signature = method_info['signature']
            docstring = method_info['docstring']

            lines.append(f'    @abstractmethod')
            lines.append(f'    {signature}:')
            if docstring:
                lines.extend(f'        {line}' for line in docstring.split('\n'))
            else:
                lines.append('        """Abstract method."""')
            lines.append('        ...')
            lines.append('')

        return '\n'.join(lines)

    def generate_client_stub(self, cls: Type, name: str) -> str:
        """Generate a client stub that implements the interface.

        Args:
            cls: Class to generate client for
            name: Name for the generated client

        Returns:
            Generated client code as string
        """
        methods = self._extract_methods(cls)

        lines = [
            '"""Generated client stub."""',
            '',
            'from typing import Any',
            '',
            '',
            f'class {name}:',
            f'    """Generated client stub for {cls.__name__}."""',
            '',
            '    def __init__(self):',
            '        """Initialize client."""',
            '        pass',
            '',
        ]

        for method_name, method_info in methods.items():
            signature = method_info['signature']
            docstring = method_info['docstring']

            lines.append(f'    {signature}:')
            if docstring:
                lines.extend(f'        {line}' for line in docstring.split('\n'))
            else:
                lines.append('        """Generated method stub."""')
            lines.append('        # TODO: Implement method')
            lines.append('        raise NotImplementedError("Method not implemented")')
            lines.append('')

        return '\n'.join(lines)

    def _extract_methods(self, cls: Type) -> Dict[str, Dict[str, Any]]:
        """Extract method information from a class.

        Args:
            cls: Class to analyze

        Returns:
            Dict mapping method names to method info
        """
        methods = {}

        for name, member in inspect.getmembers(cls):
            if not name.startswith('_') and callable(member) and not inspect.isclass(member):
                try:
                    signature = inspect.signature(member)
                    params = []

                    # Skip 'self' parameter
                    for param_name, param in signature.parameters.items():
                        if param_name == 'self':
                            continue

                        # Convert parameter to string representation
                        if param.default is inspect.Parameter.empty:
                            params.append(param_name)
                        else:
                            params.append(f'{param_name}={repr(param.default)}')

                    # Build method signature
                    params_str = ', '.join(params)
                    return_annotation = signature.return_annotation
                    if return_annotation != inspect.Signature.empty:
                        try:
                            return_str = str(return_annotation)
                        except:
                            return_str = 'Any'
                    else:
                        return_str = 'None'

                    method_signature = f'def {name}({params_str}) -> {return_str}'

                    # Get docstring
                    docstring = member.__doc__ or ""

                    methods[name] = {
                        'signature': method_signature,
                        'docstring': docstring.strip(),
                        'member': member
                    }

                except Exception as e:
                    logger.warning(f"Could not process method {name}: {e}")
                    continue

        return methods

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
    """Main entry point for the interface generator."""
    parser = argparse.ArgumentParser(description='Generate interface stubs and client code')
    parser.add_argument('--output-dir', '-o', type=Path, default=Path('generated'),
                       help='Output directory for generated files')
    parser.add_argument('--interface', action='store_true',
                       help='Generate interface/protocol stubs')
    parser.add_argument('--client', action='store_true',
                       help='Generate client stubs')
    parser.add_argument('--class-name', required=True,
                       help='Python class to generate code for (e.g., mymodule.MyClass)')
    parser.add_argument('--name', required=True,
                       help='Name for generated class/interface')

    args = parser.parse_args()

    # Import the class dynamically
    module_name, class_name = args.class_name.rsplit('.', 1)
    module = __import__(module_name, fromlist=[class_name])
    cls = getattr(module, class_name)

    generator = InterfaceGenerator(args.output_dir)

    if args.interface:
        content = generator.generate_interface_stub(cls, args.name)
        generator.write_file(f'{args.name.lower()}_interface.py', content)

    if args.client:
        content = generator.generate_client_stub(cls, args.name)
        generator.write_file(f'{args.name.lower()}_client.py', content)


if __name__ == '__main__':
    main()

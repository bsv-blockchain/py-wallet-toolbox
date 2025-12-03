#!/usr/bin/env python3
"""
Analyze Skipped Tests Script

Analyzes each skipped test to determine if it can potentially be unskipped
by checking if the blocking functionality now exists in the codebase.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Any


class SkippedTestAnalyzer:
    """Analyzes skipped tests to determine unskippability."""

    def __init__(self, skipped_tests_file: str, project_root: str):
        self.skipped_tests_file = skipped_tests_file
        self.project_root = Path(project_root)
        self.skipped_tests = []
        self.analysis_results = {
            'can_be_unskipped': [],
            'needs_implementation': [],
            'requires_environment': [],
            'design_difference': [],
            'needs_fixtures': [],
            'uncategorized': []
        }

    def load_skipped_tests(self) -> None:
        """Load skipped tests from JSON file."""
        with open(self.skipped_tests_file, 'r') as f:
            self.skipped_tests = json.load(f)

    def analyze_all_tests(self) -> None:
        """Analyze all skipped tests and categorize them."""
        for test in self.skipped_tests:
            category = self._categorize_skip_reason(test)
            self.analysis_results[category].append(test)

    def _categorize_skip_reason(self, test: Dict[str, Any]) -> str:
        """Categorize a skip reason based on its content."""
        reason = test['reason'].lower()

        # Can be unskipped - utility functions or implementations that may now exist
        if any(phrase in reason for phrase in [
            'utility functions not available',
            'lookupresolver is not fully implemented',
            'requires walletstoragemanager implementation',
            'fixture wallet_with_mocked_create_action not yet implemented',
            'cannot create authcontext',
            'cannot initialize cwiStylewalletmanager',
            'cannot initialize simplewalletmanager',
            'cannot initialize walletservices',
            'module not yet implemented',
            'requires full monitor system implementation',
            'requires unimplemented task attributes'
        ]):
            return 'can_be_unskipped'

        # Needs implementation - core functionality missing
        elif any(phrase in reason for phrase in [
            'requires full certificate subsystem implementation',
            'requires transaction building infrastructure',
            'needs valid transaction bytes',
            'requires proper transaction state setup',
            'requires full provider infrastructure',
            'requires full transaction infrastructure',
            'requires deterministic wallet state',
            'requires deterministic key derivation setup',
            'requires populated test database',
            'test vector incomplete',
            'complex async callback testing'
        ]):
            return 'needs_implementation'

        # Requires environment - external dependencies
        elif any(phrase in reason for phrase in [
            'no \'main\' environment configured',
            'integration test requiring live network',
            'requires network access to cdn',
            'requires running chaintracks service',
            'requires local test data files',
            'requires working chaintracker with network access',
            'chaintrackschaintracker not available',
            'needs chaintracks client api implementation'
        ]):
            return 'requires_environment'

        # Design differences - intentionally different from reference implementation
        elif any(phrase in reason for phrase in [
            'by design:',
            'ensure_protocol_permission method does not exist',
            'testing private methods.*do not exist',
            'takes too long to run'
        ]):
            return 'design_difference'

        # Needs fixtures - test setup issues
        elif any(phrase in reason for phrase in [
            'requires specific initialization',
            'services requires specific initialization'
        ]):
            return 'needs_fixtures'

        # Uncategorized
        else:
            return 'uncategorized'

    def check_unskippable_implementations(self) -> None:
        """Check if implementations exist for tests that can potentially be unskipped."""
        for test in self.analysis_results['can_be_unskipped']:
            self._check_specific_test(test)

    def _check_specific_test(self, test: Dict[str, Any]) -> None:
        """Check if a specific test can now be unskipped."""
        reason = test['reason'].lower()
        file_path = test['file']

        # Check utility functions
        if 'utility functions not available' in reason:
            if self._check_utility_functions_exist(file_path):
                test['can_unskip'] = True
                test['unskip_reason'] = 'Utility functions now exist'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'Utility functions still missing'

        # Check LookupResolver
        elif 'lookupresolver is not fully implemented' in reason:
            if self._check_lookup_resolver_exists():
                test['can_unskip'] = True
                test['unskip_reason'] = 'LookupResolver implementation found'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'LookupResolver still not implemented'

        # Check WalletStorageManager
        elif 'requires walletstoragemanager implementation' in reason:
            if self._check_wallet_storage_manager_exists():
                test['can_unskip'] = True
                test['unskip_reason'] = 'WalletStorageManager implementation found'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'WalletStorageManager still missing'

        # Check AuthContext
        elif 'cannot create authcontext' in reason:
            if self._check_auth_context_exists():
                test['can_unskip'] = True
                test['unskip_reason'] = 'AuthContext implementation found'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'AuthContext still missing'

        # Check wallet managers
        elif 'cannot initialize' in reason and ('cwiStylewalletmanager' in reason or 'simplewalletmanager' in reason):
            if self._check_wallet_managers_exist():
                test['can_unskip'] = True
                test['unskip_reason'] = 'Wallet manager implementation found'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'Wallet manager still missing'

        # Check monitor system
        elif 'requires full monitor system implementation' in reason:
            if self._check_monitor_system_exists():
                test['can_unskip'] = True
                test['unskip_reason'] = 'Monitor system implementation found'
            else:
                test['can_unskip'] = False
                test['unskip_reason'] = 'Monitor system still missing'

        # Default to cannot unskip if we can't determine
        else:
            test['can_unskip'] = False
            test['unskip_reason'] = 'Cannot determine unskippability'

    def _check_utility_functions_exist(self, test_file: str) -> bool:
        """Check if utility functions exist for a test file."""
        # Look for the specific utility imports that tests try to use
        if 'monitor' in test_file:
            # Check if monitor utility functions exist
            utils_file = self.project_root / 'tests' / 'utils' / 'test_utils_wallet_storage.py'
            return utils_file.exists()
        return False

    def _check_lookup_resolver_exists(self) -> bool:
        """Check if LookupResolver is implemented."""
        # Search for LookupResolver in the codebase
        grep_results = self._grep_codebase('class LookupResolver')
        return len(grep_results) > 0

    def _check_wallet_storage_manager_exists(self) -> bool:
        """Check if WalletStorageManager is implemented."""
        grep_results = self._grep_codebase('class WalletStorageManager')
        return len(grep_results) > 0

    def _check_auth_context_exists(self) -> bool:
        """Check if AuthContext is implemented."""
        grep_results = self._grep_codebase('class AuthContext')
        return len(grep_results) > 0

    def _check_wallet_managers_exist(self) -> bool:
        """Check if wallet managers are implemented."""
        managers = ['CWIStyleWalletManager', 'SimpleWalletManager']
        for manager in managers:
            if len(self._grep_codebase(f'class {manager}')) > 0:
                return True
        return False

    def _check_monitor_system_exists(self) -> bool:
        """Check if monitor system is implemented."""
        # Check for Monitor class and tasks
        monitor_exists = len(self._grep_codebase('class Monitor')) > 0
        tasks_exist = len(self._grep_codebase('class Task')) > 0
        return monitor_exists and tasks_exist

    def _grep_codebase(self, pattern: str) -> List[str]:
        """Simple grep-like search in Python files."""
        results = []
        for py_file in self.project_root.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(pattern, content, re.IGNORECASE):
                        results.append(str(py_file))
            except Exception:
                continue
        return results

    def generate_missing_functionality_report(self) -> str:
        """Generate a report on missing functionality."""
        report = []

        # Summary
        total_skipped = len(self.skipped_tests)
        can_unskip = len([t for t in self.analysis_results['can_be_unskipped'] if t.get('can_unskip', False)])

        report.append("# Missing Functionality Analysis Report")
        report.append("")
        report.append(f"Total skipped tests: {total_skipped}")
        report.append(f"Tests that can potentially be unskipped: {len(self.analysis_results['can_be_unskipped'])}")
        report.append(f"Tests confirmed unskippable: {can_unskip}")
        report.append("")

        # Tests that can be unskipped
        report.append("## Tests That Can Be Unskipped")
        report.append("")
        for test in self.analysis_results['can_be_unskipped']:
            if test.get('can_unskip', False):
                report.append(f"### {test['file']}")
                report.append(f"- **Reason**: {test['reason']}")
                report.append(f"- **Unskip Reason**: {test.get('unskip_reason', 'Unknown')}")
                report.append("")

        # Tests needing implementation
        report.append("## Tests Needing Implementation")
        report.append("")
        implementation_needed = defaultdict(list)
        for test in self.analysis_results['needs_implementation']:
            key = test['reason']
            implementation_needed[key].append(test['file'])

        for reason, files in implementation_needed.items():
            report.append(f"### {reason}")
            report.append(f"**Affected files**: {len(files)}")
            for file in files[:5]:  # Show first 5 files
                report.append(f"- {file}")
            if len(files) > 5:
                report.append(f"- ... and {len(files) - 5} more")
            report.append("")

        return '\n'.join(report)

    def save_analysis_results(self, output_dir: str = '.') -> None:
        """Save analysis results to JSON file."""
        output_path = Path(output_dir) / 'skipped_tests_detailed_analysis.json'
        with open(output_path, 'w') as f:
            json.dump(self.analysis_results, f, indent=2)


def main():
    """Main entry point."""
    analyzer = SkippedTestAnalyzer('skipped_tests_analysis.json', '.')
    analyzer.load_skipped_tests()
    analyzer.analyze_all_tests()
    analyzer.check_unskippable_implementations()
    analyzer.save_analysis_results()

    # Print summary
    print("Skipped Test Analysis Complete")
    print(f"Total skipped tests: {len(analyzer.skipped_tests)}")
    print(f"Can be unskipped: {len(analyzer.analysis_results['can_be_unskipped'])}")
    print(f"Needs implementation: {len(analyzer.analysis_results['needs_implementation'])}")
    print(f"Requires environment: {len(analyzer.analysis_results['requires_environment'])}")
    print(f"Design differences: {len(analyzer.analysis_results['design_difference'])}")

    # Print detailed report
    report = analyzer.generate_missing_functionality_report()
    with open('missing_functionality_report.md', 'w') as f:
        f.write(report)


if __name__ == '__main__':
    main()

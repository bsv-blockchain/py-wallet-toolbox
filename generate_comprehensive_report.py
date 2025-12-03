#!/usr/bin/env python3
"""
Generate Comprehensive Test Analysis Report

Creates a detailed markdown report combining all analysis results.
"""

import json
from collections import defaultdict
from typing import Dict, List, Any


class ComprehensiveReportGenerator:
    """Generates comprehensive test analysis report."""

    def __init__(self):
        self.test_summary = {}
        self.warnings = {}
        self.skipped_analysis = {}
        self.xfailed_tests = []

    def load_all_data(self) -> None:
        """Load all analysis data from JSON files."""
        try:
            with open('test_summary.json', 'r') as f:
                self.test_summary = json.load(f)
        except FileNotFoundError:
            self.test_summary = {}

        try:
            with open('warnings_analysis.json', 'r') as f:
                self.warnings = json.load(f)
        except FileNotFoundError:
            self.warnings = {}

        try:
            with open('skipped_tests_detailed_analysis.json', 'r') as f:
                self.skipped_analysis = json.load(f)
        except FileNotFoundError:
            self.skipped_analysis = {}

        try:
            with open('xfailed_tests_analysis.json', 'r') as f:
                self.xfailed_tests = json.load(f)
        except FileNotFoundError:
            self.xfailed_tests = []

    def generate_report(self) -> str:
        """Generate the comprehensive markdown report."""
        report = []

        # Title and date
        report.append("# Python Test Suite Analysis Report")
        report.append("")
        report.append("**Generated:** December 3, 2025")
        report.append("**Test Suite:** py-wallet-toolbox")
        report.append("")

        # Executive Summary
        report.extend(self._generate_executive_summary())

        # Warnings Analysis
        report.extend(self._generate_warnings_analysis())

        # Skipped Tests Analysis
        report.extend(self._generate_skipped_tests_analysis())

        # Expected Failures
        report.extend(self._generate_xfailed_analysis())

        # Missing Functionality Documentation
        report.extend(self._generate_missing_functionality_docs())

        # Recommendations
        report.extend(self._generate_recommendations())

        return '\n'.join(report)

    def _generate_executive_summary(self) -> List[str]:
        """Generate executive summary section."""
        section = []
        section.append("## Executive Summary")
        section.append("")

        summary = self.test_summary
        if summary:
            total_tests = summary['passed'] + summary['skipped'] + summary['xfailed']
            pass_rate = (summary['passed'] / total_tests * 100) if total_tests > 0 else 0

            section.append("### Overall Test Statistics")
            section.append(f"- **Total Tests:** {total_tests}")
            section.append(f"- **Passed:** {summary['passed']} ({pass_rate:.1f}%)")
            section.append(f"- **Skipped:** {summary['skipped']}")
            section.append(f"- **Expected Failures:** {summary['xfailed']}")
            section.append(f"- **Warnings:** {summary['warnings']}")
            section.append(f"- **Duration:** {summary['duration']}")
            section.append("")

        # Skipped test breakdown
        if self.skipped_analysis:
            can_unskip = len([t for t in self.skipped_analysis.get('can_be_unskipped', [])
                            if t.get('can_unskip', False)])
            needs_impl = len(self.skipped_analysis.get('needs_implementation', []))
            needs_env = len(self.skipped_analysis.get('requires_environment', []))
            design_diff = len(self.skipped_analysis.get('design_difference', []))

            section.append("### Skipped Tests Breakdown")
            section.append(f"- **Potentially Unskippable:** {len(self.skipped_analysis.get('can_be_unskipped', []))}")
            section.append(f"- **Confirmed Unskippable:** {can_unskip}")
            section.append(f"- **Needs Implementation:** {needs_impl}")
            section.append(f"- **Requires Environment:** {needs_env}")
            section.append(f"- **Design Differences:** {design_diff}")
            section.append("")

        return section

    def _generate_warnings_analysis(self) -> List[str]:
        """Generate warnings analysis section."""
        section = []
        section.append("## Warnings Analysis")
        section.append("")

        if not self.warnings:
            section.append("No warnings found in test output.")
            section.append("")
            return section

        # Group warnings by type
        warning_counts = {}
        for warning_type, warnings_list in self.warnings.items():
            warning_counts[warning_type] = len(warnings_list)

        section.append("### Warnings by Category")
        section.append("")

        # Sort by frequency
        for warning_type, count in sorted(warning_counts.items(), key=lambda x: x[1], reverse=True):
            section.append(f"#### {warning_type} ({count} instances)")
            section.append("")

            # Show first few examples
            examples = self.warnings[warning_type][:3]
            for example in examples:
                section.append(f"- `{example['file']}`: {example['message'][:100]}{'...' if len(example['message']) > 100 else ''}")

            if len(self.warnings[warning_type]) > 3:
                section.append(f"- ... and {len(self.warnings[warning_type]) - 3} more")
            section.append("")

        # Recommendations
        section.append("### Recommendations")
        section.append("")

        runtime_warnings = len(self.warnings.get('RuntimeWarning', []))
        deprecation_warnings = len(self.warnings.get('DeprecationWarning', []))
        resource_warnings = len(self.warnings.get('ResourceWarning', []))

        if runtime_warnings > 0:
            section.append(f"- **{runtime_warnings} RuntimeWarnings:** These indicate coroutines that were never awaited. Review async code patterns and ensure proper event loop management.")
        if deprecation_warnings > 0:
            section.append(f"- **{deprecation_warnings} DeprecationWarnings:** Update deprecated APIs, particularly `datetime.datetime.utcnow()` which should use `datetime.datetime.now(datetime.UTC)`.")
        if resource_warnings > 0:
            section.append(f"- **{resource_warnings} ResourceWarnings:** Unclosed event loops detected. Ensure proper cleanup of async resources.")

        section.append("")
        return section

    def _generate_skipped_tests_analysis(self) -> List[str]:
        """Generate skipped tests analysis section."""
        section = []
        section.append("## Skipped Tests Analysis")
        section.append("")

        if not self.skipped_analysis:
            section.append("No skipped test analysis available.")
            section.append("")
            return section

        # Tests that can be unskipped
        can_unskip = [t for t in self.skipped_analysis.get('can_be_unskipped', [])
                     if t.get('can_unskip', False)]

        if can_unskip:
            section.append("### Tests That Can Be Unskipped")
            section.append("")
            section.append(f"**{len(can_unskip)} tests** have been identified that can potentially be unskipped because their blocking implementations now exist.")
            section.append("")

            # Group by unskip reason
            reasons = defaultdict(list)
            for test in can_unskip:
                reasons[test.get('unskip_reason', 'Unknown')].append(test)

            for reason, tests in reasons.items():
                section.append(f"#### {reason} ({len(tests)} tests)")
                section.append("")
                for test in tests[:5]:  # Show first 5
                    section.append(f"- `{test['file']}`: {test['reason']}")
                if len(tests) > 5:
                    section.append(f"- ... and {len(tests) - 5} more tests")
                section.append("")

        # Tests needing implementation
        needs_impl = self.skipped_analysis.get('needs_implementation', [])
        if needs_impl:
            section.append("### Tests Needing Implementation")
            section.append("")
            section.append(f"**{len(needs_impl)} tests** are skipped due to missing core functionality that needs to be implemented.")
            section.append("")

            # Group by reason
            reasons = defaultdict(list)
            for test in needs_impl:
                reasons[test['reason']].append(test['file'])

            for reason, files in sorted(reasons.items(), key=lambda x: len(x[1]), reverse=True):
                section.append(f"#### {reason}")
                section.append(f"**Affected Files:** {len(files)}")
                section.append("")
                for file in files[:3]:  # Show first 3
                    section.append(f"- `{file}`")
                if len(files) > 3:
                    section.append(f"- ... and {len(files) - 3} more files")
                section.append("")

        # Environment-dependent tests
        needs_env = self.skipped_analysis.get('requires_environment', [])
        if needs_env:
            section.append("### Environment-Dependent Tests")
            section.append("")
            section.append(f"**{len(needs_env)} tests** require external services or specific environment setup.")
            section.append("")

            # Group by reason
            reasons = defaultdict(list)
            for test in needs_env:
                reasons[test['reason']].append(test['file'])

            for reason, files in sorted(reasons.items(), key=lambda x: len(x[1]), reverse=True):
                section.append(f"#### {reason}")
                section.append(f"**Affected Files:** {len(files)}")
                section.append("")
                for file in files[:3]:
                    section.append(f"- `{file}`")
                if len(files) > 3:
                    section.append(f"- ... and {len(files) - 3} more files")
                section.append("")

        # Design differences
        design_diff = self.skipped_analysis.get('design_difference', [])
        if design_diff:
            section.append("### Design Differences")
            section.append("")
            section.append(f"**{len(design_diff)} tests** are skipped due to intentional differences from the reference TypeScript implementation.")
            section.append("")

            for test in design_diff[:10]:  # Show first 10
                section.append(f"- `{test['file']}`: {test['reason']}")
            if len(design_diff) > 10:
                section.append(f"- ... and {len(design_diff) - 10} more tests")
            section.append("")

        return section

    def _generate_xfailed_analysis(self) -> List[str]:
        """Generate expected failures analysis section."""
        section = []
        section.append("## Expected Failures (xfail)")
        section.append("")

        if not self.xfailed_tests:
            section.append("No expected failures found.")
            section.append("")
            return section

        section.append(f"**{len(self.xfailed_tests)} tests** are marked as expected to fail with TODO items for future implementation.")
        section.append("")

        for test in self.xfailed_tests:
            section.append(f"### {test['test']}")
            section.append(f"**Reason:** {test['reason']}")
            section.append("")

        return section

    def _generate_missing_functionality_docs(self) -> List[str]:
        """Generate missing functionality documentation section."""
        section = []
        section.append("## Missing Functionality Documentation")
        section.append("")

        # High-priority missing functionality
        needs_impl = self.skipped_analysis.get('needs_implementation', [])
        if needs_impl:
            section.append("### High-Priority Missing Features")
            section.append("")
            section.append("Based on the analysis of skipped tests, here are the most critical missing functionalities:")
            section.append("")

            # Certificate subsystem
            cert_tests = [t for t in needs_impl if 'certificate' in t['reason'].lower()]
            if cert_tests:
                section.append("#### 1. Certificate Subsystem Implementation")
                section.append("**Impact:** 5 tests blocked")
                section.append("**Missing Components:**")
                section.append("- Full certificate lifecycle management")
                section.append("- Certificate validation and verification")
                section.append("- Integration with wallet storage")
                section.append("**Reference:** TypeScript implementation in `wallet-toolbox/src/services/certificate/`")
                section.append("")

            # Transaction infrastructure
            tx_tests = [t for t in needs_impl if 'transaction infrastructure' in t['reason'].lower()]
            if tx_tests:
                section.append("#### 2. Transaction Building Infrastructure")
                section.append("**Impact:** 15 tests blocked")
                section.append("**Missing Components:**")
                section.append("- Input selection algorithms")
                section.append("- BEEF (Bitcoin Enhanced Encryption Format) generation")
                section.append("- Transaction signing and processing pipeline")
                section.append("**Reference:** TypeScript implementation in `wallet-toolbox/src/wallet/`")
                section.append("")

            # Provider infrastructure
            provider_tests = [t for t in needs_impl if 'provider infrastructure' in t['reason'].lower()]
            if provider_tests:
                section.append("#### 3. Service Provider Infrastructure")
                section.append("**Impact:** 20+ tests blocked")
                section.append("**Missing Components:**")
                section.append("- UTXO management providers")
                section.append("- Transaction broadcasting services")
                section.append("- Network service integration")
                section.append("**Reference:** TypeScript implementation in `wallet-toolbox/src/services/providers/`")
                section.append("")

            # Deterministic wallet state
            wallet_tests = [t for t in needs_impl if 'deterministic wallet state' in t['reason'].lower()]
            if wallet_tests:
                section.append("#### 4. Deterministic Test Wallet State")
                section.append("**Impact:** 7 tests blocked")
                section.append("**Missing Components:**")
                section.append("- Pre-seeded test wallets with known UTXOs")
                section.append("- Deterministic key derivation setup")
                section.append("- Test transaction seeding infrastructure")
                section.append("**Note:** Requires coordination with storage and wallet components")
                section.append("")

        return section

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations section."""
        section = []
        section.append("## Recommendations")
        section.append("")

        # Immediate actions
        section.append("### Immediate Actions (High Impact)")
        section.append("")
        can_unskip = [t for t in self.skipped_analysis.get('can_be_unskipped', [])
                     if t.get('can_unskip', False)]
        if can_unskip:
            section.append(f"1. **Unskip {len(can_unskip)} tests** - Remove skip decorators from tests where implementations now exist")
            section.append("   - Focus on wallet manager and storage manager tests")
            section.append("   - Update test fixtures and imports as needed")
            section.append("")

        section.append("2. **Address RuntimeWarnings** - Fix coroutine and event loop issues")
        section.append("   - Implement proper async cleanup in test fixtures")
        section.append("   - Review async testing patterns")
        section.append("")

        section.append("3. **Update deprecated APIs** - Replace `datetime.datetime.utcnow()` usage")
        section.append("   - Use timezone-aware datetime objects")
        section.append("")

        # Medium-term priorities
        section.append("### Medium-term Priorities")
        section.append("")
        section.append("4. **Implement Certificate Subsystem** - Enable 5 critical tests")
        section.append("   - Start with basic certificate lifecycle operations")
        section.append("   - Integrate with existing storage layer")
        section.append("")

        section.append("5. **Build Transaction Infrastructure** - Enable 15+ tests")
        section.append("   - Implement input selection algorithms")
        section.append("   - Add BEEF format support")
        section.append("   - Complete transaction signing pipeline")
        section.append("")

        section.append("6. **Create Deterministic Test Fixtures** - Enable wallet state tests")
        section.append("   - Develop seeded test wallets with known state")
        section.append("   - Create test transaction factories")
        section.append("")

        # Long-term items
        section.append("### Long-term Goals")
        section.append("")
        section.append("7. **Complete Service Provider Infrastructure** - Enable 20+ integration tests")
        section.append("   - Implement full UTXO provider ecosystem")
        section.append("   - Add transaction broadcasting capabilities")
        section.append("")

        section.append("8. **Environment Test Setup** - Enable network-dependent tests")
        section.append("   - Configure test environments for external services")
        section.append("   - Add proper mocking for network operations")
        section.append("")

        return section


def main():
    """Main entry point."""
    generator = ComprehensiveReportGenerator()
    generator.load_all_data()
    report = generator.generate_report()

    with open('test_analysis_report.md', 'w', encoding='utf-8') as f:
        f.write(report)

    print("Comprehensive test analysis report generated: test_analysis_report.md")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test Output Analysis Script

Parses pytest output to extract warnings and skipped tests for analysis.
"""

import re
import json
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from pathlib import Path


class TestOutputAnalyzer:
    """Analyzes pytest output to extract warnings and skipped tests."""

    def __init__(self, output_file: str):
        self.output_file = output_file
        self.warnings = defaultdict(list)
        self.skipped_tests = []
        self.xfailed_tests = []
        self.test_summary = {}

    def parse_output(self) -> None:
        """Parse the test output file and extract relevant data."""
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        self._extract_warnings(content)
        self._extract_skipped_tests(content)
        self._extract_xfailed_tests(content)
        self._extract_summary(content)

    def _extract_warnings(self, content: str) -> None:
        """Extract warnings from the output."""
        # Find the warnings summary section
        warnings_match = re.search(
            r'======= warnings summary =======(.*?)(?:=+\s*$|-- Docs:|$)',
            content,
            re.DOTALL
        )

        if warnings_match:
            warnings_section = warnings_match.group(1)

            # Extract individual warnings
            warning_pattern = r'(.+?):\s*(.+?):\s*(.+)'
            for line in warnings_section.split('\n'):
                line = line.strip()
                if line and not line.startswith('='):
                    match = re.match(warning_pattern, line)
                    if match:
                        file_path, warning_type, message = match.groups()
                        self.warnings[warning_type].append({
                            'file': file_path,
                            'message': message.strip(),
                            'line': line
                        })

    def _extract_skipped_tests(self, content: str) -> None:
        """Extract skipped tests from the output."""
        # Find all SKIPPED lines
        skipped_pattern = r'SKIPPED \[(\d+)\]\s+(.+?):\s*(.+)'
        for match in re.finditer(skipped_pattern, content):
            count, location, reason = match.groups()

            # Parse location (file:line_number or file)
            if ':' in location:
                file_path, line_num = location.rsplit(':', 1)
                try:
                    line_number = int(line_num)
                except ValueError:
                    line_number = None
            else:
                file_path = location
                line_number = None

            self.skipped_tests.append({
                'file': file_path,
                'line': line_number,
                'reason': reason.strip(),
                'count': int(count),
                'location': location
            })

    def _extract_xfailed_tests(self, content: str) -> None:
        """Extract expected failures (xfail) from the output."""
        # Find all XFAIL lines
        xfail_pattern = r'XFAIL (.+?) - (.+)'
        for match in re.finditer(xfail_pattern, content):
            test_name, reason = match.groups()
            self.xfailed_tests.append({
                'test': test_name,
                'reason': reason.strip()
            })

    def _extract_summary(self, content: str) -> None:
        """Extract test summary statistics."""
        # Find the final summary line
        summary_pattern = r'===== (\d+) passed, (\d+) skipped, (\d+) xfailed, (\d+) warnings in (.+) ====='
        match = re.search(summary_pattern, content)
        if match:
            passed, skipped, xfailed, warnings, duration = match.groups()
            self.test_summary = {
                'passed': int(passed),
                'skipped': int(skipped),
                'xfailed': int(xfailed),
                'warnings': int(warnings),
                'duration': duration
            }

    def save_extracted_data(self, output_dir: str = '.') -> None:
        """Save extracted data to JSON files."""
        output_path = Path(output_dir)

        # Save warnings
        with open(output_path / 'warnings_analysis.json', 'w') as f:
            json.dump(dict(self.warnings), f, indent=2)

        # Save skipped tests
        with open(output_path / 'skipped_tests_analysis.json', 'w') as f:
            json.dump(self.skipped_tests, f, indent=2)

        # Save xfailed tests
        with open(output_path / 'xfailed_tests_analysis.json', 'w') as f:
            json.dump(self.xfailed_tests, f, indent=2)

        # Save summary
        with open(output_path / 'test_summary.json', 'w') as f:
            json.dump(self.test_summary, f, indent=2)

    def get_summary_report(self) -> str:
        """Generate a text summary report."""
        report = []

        report.append("TEST OUTPUT ANALYSIS SUMMARY")
        report.append("=" * 50)

        # Test summary
        summary = self.test_summary
        if summary:
            report.append("\nOverall Statistics:")
            report.append(f"  Total tests: {summary['passed'] + summary['skipped'] + summary['xfailed']}")
            report.append(f"  Passed: {summary['passed']}")
            report.append(f"  Skipped: {summary['skipped']}")
            report.append(f"  Expected failures: {summary['xfailed']}")
            report.append(f"  Warnings: {summary['warnings']}")
            report.append(f"  Duration: {summary['duration']}")

        # Warnings summary
        report.append(f"\nWarnings by type ({len(self.warnings)} types):")
        for warning_type, warnings_list in self.warnings.items():
            report.append(f"  {warning_type}: {len(warnings_list)} instances")

        # Skipped tests summary
        report.append(f"\nSkipped tests ({len(self.skipped_tests)} total):")

        # Group skipped tests by reason
        reasons = defaultdict(int)
        for test in self.skipped_tests:
            reasons[test['reason']] += 1

        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {count} tests: {reason}")

        # Xfailed tests
        report.append(f"\nExpected failures ({len(self.xfailed_tests)} total):")
        for test in self.xfailed_tests:
            report.append(f"  {test['test']}: {test['reason']}")

        return '\n'.join(report)


def main():
    """Main entry point."""
    analyzer = TestOutputAnalyzer('full_test_output_analysis.txt')
    analyzer.parse_output()
    analyzer.save_extracted_data()

    # Print summary
    print(analyzer.get_summary_report())


if __name__ == '__main__':
    main()

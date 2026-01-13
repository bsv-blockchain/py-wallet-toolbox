import argparse
import csv
import re
from pathlib import Path

import libcst as cst
from libcst.metadata import PositionProvider

# --- Configuration ---
INPUT_CSV = "snake_case_keys_report.csv"

def load_mapping(csv_path):
    """Load CSV and create a dictionary {(filename, line, column, original_key): new_key}"""
    mapping = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (
                str(Path(row["file"]).resolve()),
                int(row["line"]),
                int(row["column"]),
                row["original_key"]
            )
            mapping[key] = row["proposed_key"]
    return mapping


def normalize_literal(value: str) -> str:
    """Remove quotes and prefixes using the same logic as extractor."""
    return re.sub(r"^([rfb]*['\"]{1,3})|(['\"]{1,3})$", "", value)


class SnakeToCamelTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, file_path, mapping, source_lines):
        super().__init__()
        self.file_path = str(Path(file_path).resolve())
        self.mapping = mapping
        self.count = 0  # Number of conversions in this file
        self.source_lines = source_lines
        self.change_records = []

    def _get_new_key(self, node, current_value):
        pos = self.get_metadata(PositionProvider, node).start
        actual_val = normalize_literal(current_value)
        
        lookup_key = (self.file_path, pos.line, pos.column, actual_val)
        
        if lookup_key in self.mapping:
            new_val = self.mapping[lookup_key]
            # Preserve original quote format (' or ") when replacing
            quote = current_value[0] if current_value[0] in ("'", '"') else "'"
            new_value_str = f"{quote}{new_val}{quote}"
            original_line = self.source_lines[pos.line - 1] if self.source_lines and pos.line - 1 < len(self.source_lines) else ""
            updated_line = original_line
            if original_line:
                updated_line = original_line.replace(current_value, new_value_str, 1)
            self.count += 1
            self.change_records.append(
                {
                    "line": pos.line,
                    "column": pos.column,
                    "before": original_line.rstrip("\n"),
                    "after": updated_line.rstrip("\n"),
                },
            )
            return new_value_str
        return None

    def leave_SimpleString(self, original_node, updated_node):
        # Dictionary keys, strings in brackets, .get() arguments, etc.
        # all appear as SimpleString, so check them all here
        new_value_str = self._get_new_key(original_node, original_node.value)
        if new_value_str:
            return updated_node.with_changes(value=new_value_str)
        return updated_node

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Display results without modifying files")
    args = parser.parse_args()

    if not Path(INPUT_CSV).exists():
        print(f"Error: {INPUT_CSV} not found.")
        return

    mapping = load_mapping(INPUT_CSV)
    files_to_process = sorted(list(set(k[0] for k in mapping.keys())))
    
    total_files = len(files_to_process)
    print(f"Loaded {len(mapping)} conversion rules for {total_files} files.")
    print("-" * 50)

    for i, file_path in enumerate(files_to_process, 1):
        p = Path(file_path)
        if not p.exists():
            print(f"[{i}/{total_files}] Skip: {file_path} (File not found)")
            continue

        display_path = (
            p.relative_to(Path.cwd().parent.parent.parent.parent.parent.parent.parent.parent)
            if "home" in str(p)
            else p
        )
        print(f"[{i}/{total_files}] Processing: {display_path}")
        
        try:
            with open(p, "r", encoding="utf-8") as f:
                source_code = f.read()
            source_lines = source_code.splitlines()

            tree = cst.parse_module(source_code)
            wrapper = cst.metadata.MetadataWrapper(tree)
            transformer = SnakeToCamelTransformer(file_path, mapping, source_lines)
            
            # Execute transformation
            new_tree = wrapper.visit(transformer)
            
            if transformer.count == 0:
                print("    No changes.")
            elif args.dry_run:
                print(f"    Dry run: {transformer.count} keys would change.")
                for change in transformer.change_records:
                    before = change["before"]
                    after = change["after"]
                    print(f"      L{change['line']}: {before}")
                    print(f"                -> {after}")
            else:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(new_tree.code)
                print(f"    Fixed {transformer.count} keys.")
                
        except Exception as e:
            print(f"    ERROR: {e}")

    print("-" * 50)
    print("All tasks completed!")

if __name__ == "__main__":
    main()


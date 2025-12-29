import libcst as cst
from libcst.metadata import PositionProvider
import libcst.matchers as m
import csv
import re
from pathlib import Path

# --- 設定 ---
TARGET_DIRS = ["../../src", "../../tests"] 
OUTPUT_CSV = "snake_case_keys_report.csv"

def to_camel_case(snake_str):
    """snake_case を camelCase に変換する"""
    if "_" not in snake_str:
        return snake_str
    prefix = re.match(r'^_+', snake_str)
    prefix_str = prefix.group(0) if prefix else ""
    content = snake_str.lstrip('_')
    
    components = content.split('_')
    if not components or not components[0]: 
        return snake_str
        
    camel = components[0] + ''.join(x.title() for x in components[1:])
    return prefix_str + camel

# Metadata を扱うシンプルな Visitor（MetadataWrapper.visit 経由で位置情報を取得）
class SnakeCaseKeyExtractor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.results = []

    def _add_result(self, node, key_value):
        # クォートの除去（raw文字列や複数行クォートにも対応できるよう改善）
        actual_key = re.sub(r"^([rfb]*['\"]{1,3})|(['\"]{1,3})$", "", key_value)
        
        # 全て大文字（例: LOG_LEVEL）は設定定数として扱い、snake_case とは見なさない
        if "_" in actual_key and re.search(r"[a-z]", actual_key):
            # MetadataWrapper経由で実行した際に位置情報を取得
            pos = self.get_metadata(PositionProvider, node).start
            self.results.append({
                "file": self.file_path,
                "line": pos.line,
                "column": pos.column,
                "original_key": actual_key,
                "proposed_key": to_camel_case(actual_key)
            })

    # 1. 辞書リテラル: { "a_b": 1 }
    def visit_DictElement(self, node) -> None:
        if m.matches(node.key, m.SimpleString()):
            self._add_result(node.key, node.key.value)

    # 2. ブラケット参照: obj["a_b"]
    def visit_Subscript(self, node) -> None:
        # Index内のSimpleStringを安全に抽出
        if m.matches(node, m.Subscript(slice=[m.SubscriptElement(slice=m.Index(value=m.SimpleString()))])):
            # マッチャーで検証済みなので安全にアクセス可能
            index_node = node.slice[0].slice.value
            self._add_result(index_node, index_node.value)

    # 3. .get() メソッド: obj.get("a_b")
    def visit_Call(self, node) -> None:
        if m.matches(node.func, m.Attribute(attr=m.Name("get"))):
            if node.args and m.matches(node.args[0].value, m.SimpleString()):
                self._add_result(node.args[0].value, node.args[0].value.value)

def main():
    all_results = []
    
    for target_dir in TARGET_DIRS:
        path = Path(target_dir).resolve()
        if not path.exists():
            print(f"Warning: Directory {target_dir} not found.")
            continue

        print(f"Scanning: {path}")
        for py_file in path.rglob("*.py"):
            try:
                print(f"  - Scanning file: {py_file}")
                with open(py_file, "r", encoding="utf-8") as f:
                    code = f.read()
                
                tree = cst.parse_module(code)
                wrapper = cst.metadata.MetadataWrapper(tree)
                visitor = SnakeCaseKeyExtractor(str(py_file))
                # visit ではなく wrapper.visit を使用してメタデータを注入
                wrapper.visit(visitor)
                all_results.extend(visitor.results)
            except Exception as e:
                print(f"Error parsing {py_file}: {e}")

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "line", "column", "original_key", "proposed_key"])
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"\nSuccessfully extracted {len(all_results)} items to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()


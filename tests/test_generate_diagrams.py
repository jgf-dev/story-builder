import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# Add the script directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".agent/skills/codebase-diagrammer/scripts"))

from generate_diagrams import clean_id, clean_label, CodebaseAnalyzer

class TestGenerateDiagrams(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_clean_id(self):
        self.assertEqual(clean_id("foo-bar.baz"), "foo_bar_baz")
        self.assertEqual(clean_id("foo/bar/baz.py"), "foo_bar_baz_py")
        self.assertEqual(clean_id("!!!a_b_c!!!"), "a_b_c")

    def test_clean_label(self):
        self.assertEqual(clean_label('Label with "quotes"'), 'Label with \\"quotes\\"')
        self.assertEqual(clean_label('Label with [brackets]'), 'Label with (brackets)')

    def test_analyzer_scan_and_analyze(self):
        # Create a mock directory structure
        (self.root / "sub1").mkdir()
        (self.root / "sub2").mkdir()
        (self.root / ".git").mkdir() # should be excluded

        # Create Python files
        py1 = self.root / "sub1" / "module_a.py"
        py1.write_text("""
import sqlite3
import streamlit as st
from sub2.module_b import Helper

class Processor:
    name: str = "processor"
    value: int
    
    def process_data(self):
        helper = Helper()
        helper.do_something()

def main():
    p = Processor()
    p.process_data()
""", encoding='utf-8')

        py2 = self.root / "sub2" / "module_b.py"
        py2.write_text("""
import chromadb

class Helper:
    def do_something(self):
        client = chromadb.Client()
""", encoding='utf-8')

        # Create SQL file
        sql_file = self.root / "schema.sql"
        sql_file.write_text("CREATE TABLE users (id INTEGER PRIMARY KEY);", encoding='utf-8')

        # Create Shell file
        sh_file = self.root / "run.sh"
        sh_file.write_text("python sub1/module_a.py", encoding='utf-8')

        # Run analyzer
        analyzer = CodebaseAnalyzer(self.temp_dir)
        analyzer.analyze()

        # 1. Verify Scan Files (excluding .git)
        rel_files = [str(f) for f in analyzer.files]
        self.assertIn("sub1/module_a.py", rel_files)
        self.assertIn("sub2/module_b.py", rel_files)
        self.assertIn("schema.sql", rel_files)
        self.assertIn("run.sh", rel_files)
        # Should exclude .git files or directories
        for f in rel_files:
            self.assertFalse(f.startswith(".git"))

        # 2. Verify Python imports / dependencies
        self.assertIn("sub1/module_a.py", analyzer.imports)
        self.assertIn("sub2/module_b.py", analyzer.imports["sub1/module_a.py"])

        # 3. Verify Classes & Functions & Fields
        self.assertIn("Processor", analyzer.classes["sub1/module_a.py"])
        self.assertIn("Helper", analyzer.classes["sub2/module_b.py"])
        
        # Verify fields of Processor class
        fields = analyzer.class_fields["Processor"]
        # name: str = "processor" -> field name, type str
        self.assertIn(("name", "str"), fields)
        # value: int -> field value, type int
        self.assertIn(("value", "int"), fields)
        
        funcs_a = analyzer.functions["sub1/module_a.py"]
        self.assertIn(("main", None), funcs_a)
        self.assertIn(("process_data", "Processor"), funcs_a)

        # 4. Verify DB / UI detections
        self.assertIn("SQLite", analyzer.databases["sub1/module_a.py"])
        self.assertIn("ChromaDB", analyzer.databases["sub2/module_b.py"])
        self.assertIn("Streamlit", analyzer.uis["sub1/module_a.py"])
        self.assertIn("SQL Schema (Tables: users)", analyzer.databases["schema.sql"])

        # 5. Verify script runs detection
        self.assertIn("sub1/module_a.py", analyzer.imports["run.sh"])

        # 6. Verify Markdown generation contains standard sections and clean quotes
        md = analyzer.generate_diagrams_markdown()
        self.assertIn("# Codebase Architecture and Flow Diagrams", md)
        self.assertIn("## 1. Directory & Component Structure", md)
        self.assertIn("## 2. Module & File Dependencies", md)
        self.assertIn("## 3. Key Classes & Functions", md)
        self.assertIn("## 4. Data Storage & API Flows", md)
        self.assertIn("## 5. UI & Presentation Layers", md)
        
        # Check quoted subgraph label
        self.assertIn('subgraph Root ["Workspace Root"]', md)
        # Check class fields are printed
        self.assertIn("+str name", md)
        self.assertIn("+int value", md)

if __name__ == "__main__":
    unittest.main()

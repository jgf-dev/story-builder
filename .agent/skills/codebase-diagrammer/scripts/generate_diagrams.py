#!/usr/bin/env python3
import os
import ast
import re
import argparse
from pathlib import Path

def clean_id(name):
    """Generates a valid Mermaid node ID from a string."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', str(name)).strip('_')

def clean_label(label):
    """Escapes labels for Mermaid node displays."""
    return str(label).replace('"', '\\"').replace('[', '(').replace(']', ')')

def get_annotation_str(node):
    """Recursively converts an AST annotation node to a string representation."""
    if node is None:
        return ""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Subscript):
        val = get_annotation_str(node.value)
        slc = get_annotation_str(node.slice)
        return f"{val}[{slc}]"
    elif isinstance(node, ast.Attribute):
        val = get_annotation_str(node.value)
        return f"{val}.{node.attr}"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = get_annotation_str(node.left)
        right = get_annotation_str(node.right)
        return f"{left} | {right}"
    elif isinstance(node, ast.Tuple):
        return ", ".join(get_annotation_str(elt) for elt in node.elts)
    elif isinstance(node, ast.List):
        return ", ".join(get_annotation_str(elt) for elt in node.elts)
    return str(node)

class CodebaseAnalyzer:
    def __init__(self, root_dir, exclude_dirs=None):
        self.root_dir = Path(root_dir).resolve()
        self.exclude_dirs = set(exclude_dirs or [
            '.git', '__pycache__', '.venv', 'venv', 'node_modules', 
            '.pytest_cache', '.mypy_cache', '.agent', '.crush', 
            '.hermes', '.qoder', 'dist', 'build', '.github'
        ])
        self.files = []
        self.modules = {} # rel_path -> ast.AST or None
        self.imports = {} # rel_path -> list of imported local modules
        self.classes = {} # rel_path -> list of class names
        self.class_fields = {} # class_name -> list of (field_name, field_type)
        self.functions = {} # rel_path -> list of (func_name, class_name_or_None)
        self.calls = [] # list of (caller_file, caller_func, callee_name)
        self.databases = {} # rel_path -> list of DB technologies or files referenced
        self.uis = {} # rel_path -> list of UI patterns found

    def scan(self):
        for root, dirs, filenames in os.walk(self.root_dir):
            # Prune directory list in-place to avoid descending excluded dirs
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for f in filenames:
                file_path = Path(root) / f
                rel_path = file_path.relative_to(self.root_dir)
                self.files.append(rel_path)

    def analyze(self):
        self.scan()
        for rel_path in self.files:
            abs_path = self.root_dir / rel_path
            ext = rel_path.suffix.lower()
            
            # Skip test files and directory contents for relationship diagrams
            is_test = 'tests' in rel_path.parts or rel_path.name.startswith('test')
            
            if ext == '.py':
                self.analyze_python(rel_path, abs_path, is_test)
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                if not is_test:
                    self.analyze_js_ts(rel_path, abs_path)
            elif ext in ['.sql']:
                if not is_test:
                    self.analyze_sql(rel_path, abs_path)
            elif ext in ['.sh']:
                if not is_test:
                    self.analyze_shell(rel_path, abs_path)

    def analyze_python(self, rel_path, abs_path, is_test=False):
        if is_test:
            # We skip detailed analysis of test files to keep diagrams clean
            return

        try:
            content = abs_path.read_text(encoding='utf-8')
        except Exception:
            return

        # Check for DB & UI mentions in raw content
        db_techs = []
        if 'sqlite3' in content or 'sqlite' in content or '.db' in content:
            db_techs.append('SQLite')
        if 'chromadb' in content or 'ChromaDB' in content:
            db_techs.append('ChromaDB')
        if 'boto3' in content or 'bedrock' in content:
            db_techs.append('AWS Bedrock/S3')
        if 'cartesia' in content:
            db_techs.append('Cartesia TTS')
        if 'google-genai' in content or 'google.genai' in content:
            db_techs.append('Google GenAI')
        if 'xai-sdk' in content or 'xaiapi' in content:
            db_techs.append('xAI API')
        if db_techs:
            self.databases[str(rel_path)] = db_techs

        ui_techs = []
        if 'streamlit' in content or 'import streamlit' in content:
            ui_techs.append('Streamlit')
        if 'plotly' in content or 'matplotlib' in content:
            ui_techs.append('Visualization Plot')
        if ui_techs:
            self.uis[str(rel_path)] = ui_techs

        try:
            tree = ast.parse(content, filename=str(abs_path))
            self.modules[str(rel_path)] = tree
        except Exception:
            self.modules[str(rel_path)] = None
            return

        local_imports = []
        classes_in_file = []
        funcs_in_file = []
        
        parts = rel_path.with_suffix('').parts

        class ASTVisitor(ast.NodeVisitor):
            def __init__(self, analyzer_obj):
                self.analyzer = analyzer_obj
                self.current_class = None
                self.current_func = None

            def visit_Import(self, node):
                for alias in node.names:
                    self.add_local_import(alias.name)
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    self.add_local_import(node.module, level=node.level)
                self.generic_visit(node)

            def add_local_import(self, module_name, level=0):
                resolved = None
                if level > 0:
                    parent_parts = parts[:-level]
                    resolved = '.'.join(parent_parts + tuple(module_name.split('.')))
                else:
                    first_part = module_name.split('.')[0]
                    if (self.analyzer.root_dir / first_part).is_dir() or (self.analyzer.root_dir / f"{first_part}.py").is_file():
                        resolved = module_name

                if resolved:
                    resolved_path = resolved.replace('.', '/')
                    py_file = self.analyzer.root_dir / f"{resolved_path}.py"
                    dir_init = self.analyzer.root_dir / resolved_path / "__init__.py"
                    if py_file.is_file():
                        local_imports.append(str(py_file.relative_to(self.analyzer.root_dir)))
                    elif dir_init.is_file():
                        local_imports.append(str(dir_init.relative_to(self.analyzer.root_dir)))

            def visit_ClassDef(self, node):
                classes_in_file.append(node.name)
                
                # Extract fields
                fields = []
                for body_item in node.body:
                    if isinstance(body_item, ast.AnnAssign):
                        if isinstance(body_item.target, ast.Name):
                            field_name = body_item.target.id
                            field_type = get_annotation_str(body_item.annotation) or "Any"
                            fields.append((field_name, field_type))
                    elif isinstance(body_item, ast.Assign):
                        for target in body_item.targets:
                            if isinstance(target, ast.Name):
                                val_str = "Any"
                                if isinstance(body_item.value, ast.Constant):
                                    val_str = type(body_item.value.value).__name__
                                fields.append((target.id, val_str))
                
                self.analyzer.class_fields[node.name] = fields

                old_class = self.current_class
                self.current_class = node.name
                self.generic_visit(node)
                self.current_class = old_class

            def visit_FunctionDef(self, node):
                funcs_in_file.append((node.name, self.current_class))
                old_func = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = old_func

            def visit_AsyncFunctionDef(self, node):
                funcs_in_file.append((node.name, self.current_class))
                old_func = self.current_func
                self.current_func = node.name
                self.generic_visit(node)
                self.current_func = old_func

            def visit_Call(self, node):
                callee = None
                if isinstance(node.func, ast.Name):
                    callee = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    callee = node.func.attr
                
                if callee and self.current_func:
                    caller_context = f"{self.current_class}.{self.current_func}" if self.current_class else self.current_func
                    self.analyzer.calls.append((str(rel_path), caller_context, callee))
                self.generic_visit(node)

        visitor = ASTVisitor(self)
        visitor.visit(tree)

        if local_imports:
            self.imports[str(rel_path)] = list(set(local_imports))
        if classes_in_file:
            self.classes[str(rel_path)] = classes_in_file
        if funcs_in_file:
            self.functions[str(rel_path)] = funcs_in_file

    def analyze_js_ts(self, rel_path, abs_path):
        try:
            content = abs_path.read_text(encoding='utf-8')
        except Exception:
            return

        db_techs = []
        if 'sqlite' in content or 'better-sqlite3' in content:
            db_techs.append('SQLite')
        if 'postgres' in content or 'pg' in content:
            db_techs.append('PostgreSQL')
        if 'prisma' in content:
            db_techs.append('Prisma ORM')
        if db_techs:
            self.databases[str(rel_path)] = db_techs

        ui_techs = []
        if 'react' in content or 'React' in content:
            ui_techs.append('React')
        if 'vue' in content:
            ui_techs.append('Vue')
        if ui_techs:
            self.uis[str(rel_path)] = ui_techs

        local_imports = []
        imports_matches = re.findall(r'import\s+.*?\s+from\s+[\'"](\./.*?)[\'"]', content)
        imports_matches += re.findall(r'require\(\s*[\'"](\./.*?)[\'"]\s*\)', content)
        
        for imp in imports_matches:
            resolved_p = (rel_path.parent / imp).resolve()
            try:
                rel_resolved = resolved_p.relative_to(self.root_dir)
                for ext in ['.js', '.ts', '.jsx', '.tsx', '/index.js', '/index.ts']:
                    test_file = self.root_dir / f"{rel_resolved}{ext}"
                    if test_file.is_file():
                        local_imports.append(str(test_file.relative_to(self.root_dir)))
                        break
            except Exception:
                pass
        
        if local_imports:
            self.imports[str(rel_path)] = list(set(local_imports))

    def analyze_sql(self, rel_path, abs_path):
        try:
            content = abs_path.read_text(encoding='utf-8')
        except Exception:
            return
        
        tables = re.findall(r'CREATE\s+TABLE\s+(\w+)', content, re.IGNORECASE)
        if tables:
            self.databases[str(rel_path)] = [f"SQL Schema (Tables: {', '.join(tables)})"]

    def analyze_shell(self, rel_path, abs_path):
        try:
            content = abs_path.read_text(encoding='utf-8')
        except Exception:
            return

        runs = []
        for line in content.splitlines():
            matches = re.findall(r'(python\d?|uv run|sh|bash)\s+([a-zA-Z0-9_\-\./]+)', line)
            for _, run_script in matches:
                if (self.root_dir / run_script).is_file():
                    runs.append(run_script)
        if runs:
            self.imports[str(rel_path)] = list(set(runs))

    def generate_diagrams_markdown(self):
        md = []
        md.append("# Codebase Architecture and Flow Diagrams")
        md.append("\nThis document contains Mermaid diagrams visualizing the codebase, automatically generated by the Codebase Diagrammer skill.")
        md.append("\n---")

        # 1. Component & Directory Structure Diagram
        md.append("\n## 1. Directory & Component Structure")
        md.append("High-level layout of directories and files in the repository.")
        md.append("\n```mermaid")
        md.append("flowchart TD")
        md.append("    subgraph Root [\"Workspace Root\"]")
        
        subgraphs = {}
        root_nodes = []
        for f in sorted(self.files):
            p = f.parts
            if len(p) == 1:
                node_id_str = clean_id(f)
                root_nodes.append(f"        {node_id_str}[\"{clean_label(f.name)}\"]")
            else:
                sub = p[0]
                if sub not in subgraphs:
                    subgraphs[sub] = []
                subgraphs[sub].append(f)
        
        for node in root_nodes:
            md.append(node)
        md.append("    end")

        for sub, paths in sorted(subgraphs.items()):
            sub_id = clean_id(sub)
            md.append(f"\n    subgraph {sub_id} [\"/{sub}\"]")
            for f in sorted(paths):
                display_name = str(f.relative_to(sub))
                node_id_str = clean_id(f)
                md.append(f"        {node_id_str}[\"{clean_label(display_name)}\"]")
            md.append("    end")
        md.append("```")

        # 2. Module & Script Dependency Diagram
        md.append("\n---")
        md.append("\n## 2. Module & File Dependencies")
        md.append("Visualizes import relationships and dependency flows between local scripts and modules.")
        md.append("\n```mermaid")
        md.append("flowchart RL")
        has_imports = False
        for caller, callees in sorted(self.imports.items()):
            caller_id = clean_id(caller)
            for callee in sorted(callees):
                callee_id = clean_id(callee)
                md.append(f"    {caller_id}[\"{clean_label(caller)}\"] --> {callee_id}[\"{clean_label(callee)}\"]")
                has_imports = True
        if not has_imports:
            md.append("    NoDependencies[\"No inter-file dependencies detected.\"]")
        md.append("```")

        # 3. Class and Function Map
        md.append("\n---")
        md.append("\n## 3. Key Classes & Functions")
        md.append("Outlines the primary class structures and key functions defined in each module.")
        md.append("\n```mermaid")
        md.append("classDiagram")
        has_classes = False
        for file_path, classes in sorted(self.classes.items()):
            file_name_clean = clean_id(Path(file_path).stem)
            for cls in classes:
                md.append(f"    class {cls} {{")
                # Print fields
                fields = self.class_fields.get(cls, [])
                for field_name, field_type in fields:
                    md.append(f"        +{field_type} {field_name}")
                # List functions belonging to this class
                funcs = self.functions.get(file_path, [])
                for func, owner in funcs:
                    if owner == cls:
                        md.append(f"        +{func}()")
                md.append("    }")
                has_classes = True
        
        # Show functions defined at the module level (not inside classes)
        for file_path, funcs in sorted(self.functions.items()):
            file_name_clean = clean_id(Path(file_path).stem)
            module_level_funcs = [f for f, owner in funcs if owner is None]
            if module_level_funcs:
                md.append(f"    class {file_name_clean}_Module {{")
                for func in module_level_funcs:
                    md.append(f"        +{func}()")
                md.append("    }")
                has_classes = True

        # Render relationships between classes based on type fields references
        all_class_names = set()
        for classes in self.classes.values():
            all_class_names.update(classes)

        relationships = []
        for cls, fields in self.class_fields.items():
            if cls not in all_class_names:
                continue
            for field_name, field_type in fields:
                for other_cls in all_class_names:
                    if other_cls == cls:
                        continue
                    if re.search(r'\b' + re.escape(other_cls) + r'\b', field_type):
                        relationships.append(f"    {cls} --> {other_cls}")

        for rel in sorted(list(set(relationships))):
            md.append(rel)

        if not has_classes:
            md.append("    class NoClasses {")
            md.append("        +no_classes_found()")
            md.append("    }")
        md.append("```")

        # 4. Storage & Data Models
        md.append("\n---")
        md.append("\n## 4. Data Storage & API Flows")
        md.append("Represents database connections, local caches, APIs, and external services consumed by scripts.")
        md.append("\n```mermaid")
        md.append("flowchart LR")
        
        all_dbs = set()
        for techs in self.databases.values():
            all_dbs.update(techs)
            
        for db in sorted(all_dbs):
            db_id = clean_id(db)
            md.append(f"    {db_id}[(\"{clean_label(db)}\")]")
            
        has_storage = False
        for file_path, techs in sorted(self.databases.items()):
            file_id = clean_id(file_path)
            for db in techs:
                db_id = clean_id(db)
                md.append(f"    {file_id}[\"{clean_label(file_path)}\"] -.-> {db_id}")
                has_storage = True
                
        if not has_storage:
            md.append("    NoStorage[\"No storage integrations or local databases detected.\"]")
        md.append("```")

        # 5. UI and Client Interfaces
        md.append("\n---")
        md.append("\n## 5. UI & Presentation Layers")
        md.append("Tracks user interfaces, scripts utilizing Streamlit or plotting modules, and entrypoints.")
        md.append("\n```mermaid")
        md.append("flowchart TD")
        
        all_uis = set()
        for techs in self.uis.values():
            all_uis.update(techs)
            
        for ui in sorted(all_uis):
            ui_id = clean_id(ui)
            md.append(f"    {ui_id}{{\"{clean_label(ui)}\"}}")
            
        has_ui = False
        for file_path, techs in sorted(self.uis.items()):
            file_id = clean_id(file_path)
            for ui in techs:
                ui_id = clean_id(ui)
                md.append(f"    {file_id}[\"{clean_label(file_path)}\"] ===> {ui_id}")
                has_ui = True
                
        if not has_ui:
            md.append("    NoUI[\"No client interfaces or UI libraries detected.\"]")
        md.append("```")

        return "\n".join(md)

def main():
    parser = argparse.ArgumentParser(description="Analyze a codebase and output structured Mermaid diagrams.")
    parser.add_argument("--root-dir", default=".", help="Root directory of the codebase to analyze.")
    parser.add_argument("--output-file", default="architecture.md", help="Output path for the generated markdown file.")
    args = parser.parse_args()

    analyzer = CodebaseAnalyzer(args.root_dir)
    analyzer.analyze()
    markdown_content = analyzer.generate_diagrams_markdown()

    output_path = Path(args.output_file)
    output_path.write_text(markdown_content, encoding='utf-8')
    print(f"Successfully generated codebase diagrams at: {output_path.resolve()}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import ast
import os
import re
from typing import Dict, List, Tuple, Optional, Any, Union

class ComplexityMetrics:
    """Calculates code quality metrics for Python files.

    This class analyzes Python code and calculates various metrics to evaluate code quality,
    similar to tools like sourcery.ai.

    Attributes:
        MAX_COMPLEXITY: Maximum acceptable cyclomatic complexity per function
        MAX_METHOD_LENGTH: Maximum acceptable number of lines per function
        MAX_WORKING_MEMORY: Maximum acceptable number of variables in a function's scope
    """
    
    MAX_COMPLEXITY = 10
    MAX_METHOD_LENGTH = 50
    MAX_WORKING_MEMORY = 8
    
    def __init__(self, file_path: str):
        """Initialize the complexity metrics calculator.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Examples:
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            ...     _ = temp.write(b'def simple_func():\\n    return 42\\n')
            ...     temp_path = temp.name
            >>> metrics = ComplexityMetrics(temp_path)
            >>> isinstance(metrics, ComplexityMetrics)
            True
            >>> import os
            >>> os.unlink(temp_path)  # Clean up
        """
        self.file_path = file_path
        self.code = ""
        self._read_file()
        self.ast_tree = None
        self._parse_ast()
        
    def _read_file(self) -> None:
        """Read the content of the file."""
        try:
            with open(self.file_path, 'r') as f:
                self.code = f.read()
        except Exception as e:
            print(f"Error reading file {self.file_path}: {e}")
            self.code = ""
            
    def _parse_ast(self) -> None:
        """Parse the code into an AST (Abstract Syntax Tree)."""
        try:
            self.ast_tree = ast.parse(self.code)
        except SyntaxError as e:
            print(f"Syntax error in file {self.file_path}: {e}")
            self.ast_tree = None
    
    def calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate the cyclomatic complexity of a function.
        
        Cyclomatic complexity counts the number of decision points in a function
        plus one. Decision points include if, while, for, and, or, etc.
        
        Args:
            node: The AST node representing a function definition
            
        Returns:
            The cyclomatic complexity score
            
        Examples:
            >>> code = '''
            ... def complex_func(x):
            ...     if x > 0:
            ...         if x > 10:
            ...             return "large positive"
            ...         return "positive"
            ...     elif x < 0:
            ...         return "negative"
            ...     else:
            ...         return "zero"
            ... '''
            >>> tree = ast.parse(code)
            >>> # Create a metrics object with a dummy file that doesn't get read
            >>> metrics = ComplexityMetrics.__new__(ComplexityMetrics)
            >>> metrics.ast_tree = tree  # Set ast_tree directly
            >>> func_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            >>> metrics.calculate_cyclomatic_complexity(func_node)
            4
        """
        if not self.ast_tree:
            return 0
            
        complexity = 1  # Base complexity is 1
        
        # Count control flow statements that increase complexity
        decision_nodes = (
            ast.If, ast.While, ast.For, ast.IfExp,
            ast.Assert, ast.Try, ast.ExceptHandler
        )
        
        def _count_boolean_ops(node: ast.BoolOp) -> int:
            """Count boolean operations (and, or) as they add complexity."""
            return len(node.values) - 1
        
        for inner_node in ast.walk(node):
            if isinstance(inner_node, decision_nodes):
                complexity += 1
            elif isinstance(inner_node, ast.BoolOp):
                complexity += _count_boolean_ops(inner_node)
                
        return complexity
    
    def calculate_method_length(self, node: ast.FunctionDef) -> int:
        """Calculate the length of a function in lines of code.
        
        Args:
            node: The AST node representing a function definition
            
        Returns:
            The number of lines in the function
            
        Examples:
            >>> code = '''
            ... def multi_line_func():
            ...     a = 1
            ...     b = 2
            ...     c = 3
            ...     return a + b + c
            ... '''
            >>> tree = ast.parse(code)
            >>> # Create a metrics object with a dummy file that doesn't get read
            >>> metrics = ComplexityMetrics.__new__(ComplexityMetrics)
            >>> metrics.ast_tree = tree  # Set ast_tree directly
            >>> func_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            >>> metrics.calculate_method_length(func_node)
            5
        """
        if not node.body:
            return 0
            
        start_line = node.lineno
        last_node = node.body[-1]
        
        # Find the end line by traversing to the last child node
        end_line = start_line
        for n in ast.walk(last_node):
            if hasattr(n, 'lineno'):
                end_line = max(end_line, n.lineno)
        
        return end_line - start_line + 1
    
    def calculate_working_memory(self, node: ast.FunctionDef) -> int:
        """Calculate the working memory score for a function.
        
        Working memory is the number of variables in scope that a developer
        needs to keep track of while reading the function.
        
        Args:
            node: The AST node representing a function definition
            
        Returns:
            The working memory score
            
        Examples:
            >>> code = '''
            ... def memory_heavy_func():
            ...     a = 1
            ...     b = 2
            ...     c = 3
            ...     d = 4
            ...     return a + b + c + d
            ... '''
            >>> tree = ast.parse(code)
            >>> # Create a metrics object with a dummy file that doesn't get read
            >>> metrics = ComplexityMetrics.__new__(ComplexityMetrics)
            >>> metrics.ast_tree = tree  # Set ast_tree directly
            >>> func_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            >>> metrics.calculate_working_memory(func_node)
            4
        """
        if not node.body:
            return 0
            
        variables = set()
        
        # Find all variable assignments
        for inner_node in ast.walk(node):
            # Track variable assignments
            if isinstance(inner_node, ast.Assign):
                for target in inner_node.targets:
                    if isinstance(target, ast.Name):
                        variables.add(target.id)
            # Track variable in augmented assignments (e.g., x += 1)
            elif isinstance(inner_node, ast.AugAssign):
                if isinstance(inner_node.target, ast.Name):
                    variables.add(inner_node.target.id)
            # Track variables in for loops
            elif isinstance(inner_node, ast.For):
                if isinstance(inner_node.target, ast.Name):
                    variables.add(inner_node.target.id)
        
        # Add function parameters to variables
        for arg in node.args.args:
            variables.add(arg.arg)
            
        return len(variables)
    
    def evaluate_function(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Evaluate all metrics for a single function.
        
        Args:
            node: The AST node representing a function definition
            
        Returns:
            A dictionary containing all calculated metrics and overall score
            
        Examples:
            >>> code = '''
            ... def sample_func(x, y):
            ...     if x > y:
            ...         return x
            ...     else:
            ...         return y
            ... '''
            >>> tree = ast.parse(code)
            >>> # Create a metrics object with a dummy file that doesn't get read
            >>> metrics = ComplexityMetrics.__new__(ComplexityMetrics)
            >>> metrics.ast_tree = tree  # Set ast_tree directly
            >>> func_node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            >>> result = metrics.evaluate_function(func_node)
            >>> all(key in result for key in ['name', 'complexity', 'method_length', 'working_memory', 'overall_score'])
            True
        """
        complexity = self.calculate_cyclomatic_complexity(node)
        method_length = self.calculate_method_length(node)
        working_memory = self.calculate_working_memory(node)
        
        # Calculate scores on a scale of 0-10 (10 being best)
        complexity_score = max(0, 10 - (complexity / self.MAX_COMPLEXITY) * 10)
        length_score = max(0, 10 - (method_length / self.MAX_METHOD_LENGTH) * 10)
        memory_score = max(0, 10 - (working_memory / self.MAX_WORKING_MEMORY) * 10)
        
        # Calculate overall score as weighted average
        overall_score = (complexity_score * 0.4 + length_score * 0.3 + memory_score * 0.3)
        
        return {
            'name': node.name,
            'complexity': {
                'value': complexity,
                'score': round(complexity_score, 1),
                'max': self.MAX_COMPLEXITY
            },
            'method_length': {
                'value': method_length,
                'score': round(length_score, 1),
                'max': self.MAX_METHOD_LENGTH
            },
            'working_memory': {
                'value': working_memory,
                'score': round(memory_score, 1),
                'max': self.MAX_WORKING_MEMORY
            },
            'overall_score': round(overall_score, 1)
        }
        
    def evaluate_file(self) -> Dict[str, Any]:
        """Evaluate all metrics for the entire file.
        
        Returns:
            A dictionary containing metrics for each function and overall file score
            
        Examples:
            >>> code = '''
            ... def func1(x):
            ...     return x + 1
            ... 
            ... def func2(y):
            ...     if y > 0:
            ...         return y * 2
            ...     return 0
            ... '''
            >>> import tempfile
            >>> with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
            ...     _ = temp.write(code.encode('utf-8'))
            ...     temp_path = temp.name
            >>> metrics = ComplexityMetrics(temp_path)
            >>> result = metrics.evaluate_file()
            >>> len(result['functions']) >= 2
            True
            >>> import os
            >>> os.unlink(temp_path)  # Clean up
        """
        if not self.ast_tree:
            return {
                'filename': os.path.basename(self.file_path),
                'functions': [],
                'overall_score': 0.0
            }
            
        functions = []
        for node in ast.walk(self.ast_tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(self.evaluate_function(node))
                
        # Calculate overall file score as average of function scores
        if functions:
            overall_score = sum(f['overall_score'] for f in functions) / len(functions)
        else:
            overall_score = 10.0  # Perfect score for empty files
            
        return {
            'filename': os.path.basename(self.file_path),
            'functions': functions,
            'overall_score': round(overall_score, 1)
        }


def evaluate_python_file(file_path: str) -> Dict[str, Any]:
    """Evaluate code quality for a Python file.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        A dictionary containing all code quality metrics
        
    Examples:
        >>> import tempfile
        >>> with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as temp:
        ...     _ = temp.write(b'def simple_func():\\n    return 42\\n')
        ...     temp_path = temp.name
        >>> result = evaluate_python_file(temp_path)
        >>> 'filename' in result and 'overall_score' in result
        True
        >>> import os
        >>> os.unlink(temp_path)  # Clean up
    """
    metrics = ComplexityMetrics(file_path)
    return metrics.evaluate_file()


def evaluate_directory(directory: str) -> List[Dict[str, Any]]:
    """Evaluate code quality for all Python files in a directory.
    
    Args:
        directory: Path to the directory to analyze
        
    Returns:
        A list of dictionaries containing metrics for each Python file
        
    Examples:
        >>> import tempfile, os, shutil
        >>> # Create a temporary directory with sample Python files
        >>> temp_dir = tempfile.mkdtemp()
        >>> with open(os.path.join(temp_dir, 'test1.py'), 'w') as f:
        ...     _ = f.write('def func1(): return 42')
        >>> with open(os.path.join(temp_dir, 'test2.py'), 'w') as f:
        ...     _ = f.write('def func2(x): return x * 2')
        >>> results = evaluate_directory(temp_dir)
        >>> len(results) >= 2
        True
        >>> shutil.rmtree(temp_dir)  # Clean up
    """
    results = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    result = evaluate_python_file(file_path)
                    results.append(result)
                except Exception as e:
                    print(f"Error evaluating {file_path}: {e}")
                    
    return results


def format_quality_report(evaluations: List[Dict[str, Any]]) -> str:
    """Format code quality evaluation results as a readable report.
    
    Args:
        evaluations: List of evaluation results from evaluate_directory or evaluate_python_file
        
    Returns:
        A formatted string report
        
    Examples:
        >>> eval_result = {
        ...     'filename': 'test.py',
        ...     'functions': [
        ...         {
        ...             'name': 'test_func',
        ...             'complexity': {'value': 2, 'score': 8.0, 'max': 10},
        ...             'method_length': {'value': 5, 'score': 9.0, 'max': 50},
        ...             'working_memory': {'value': 3, 'score': 6.2, 'max': 8},
        ...             'overall_score': 7.7
        ...         }
        ...     ],
        ...     'overall_score': 7.7
        ... }
        >>> report = format_quality_report([eval_result])
        >>> 'Code Quality Report' in report
        True
        >>> 'test.py' in report
        True
    """
    if not evaluations:
        return "No Python files found for evaluation."
    
    report = ["# Code Quality Report", ""]
    
    # Sort files by overall score (ascending, so worst files come first)
    sorted_evals = sorted(evaluations, key=lambda x: x['overall_score'])
    
    for eval_result in sorted_evals:
        filename = eval_result['filename']
        overall_score = eval_result['overall_score']
        
        # Add file header with overall score
        report.append(f"## {filename} (Overall: {overall_score}/10)")
        
        if not eval_result['functions']:
            report.append("No functions found in this file.")
            report.append("")
            continue
            
        # Sort functions by overall score (ascending)
        sorted_funcs = sorted(eval_result['functions'], key=lambda x: x['overall_score'])
        
        for func in sorted_funcs:
            report.append(f"### {func['name']} (Score: {func['overall_score']}/10)")
            
            # Add metrics
            complexity = func['complexity']
            report.append(f"- Complexity: {complexity['value']}/{complexity['max']} (Score: {complexity['score']}/10)")
            
            length = func['method_length']
            report.append(f"- Method Length: {length['value']}/{length['max']} (Score: {length['score']}/10)")
            
            memory = func['working_memory']
            report.append(f"- Working Memory: {memory['value']}/{memory['max']} (Score: {memory['score']}/10)")
            
            report.append("")
            
        report.append("")
        
    return "\n".join(report)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code_quality.py <directory_or_file>")
        sys.exit(1)
        
    path = sys.argv[1]
    
    if os.path.isfile(path):
        evaluation = [evaluate_python_file(path)]
    else:
        evaluation = evaluate_directory(path)
        
    print(format_quality_report(evaluation))
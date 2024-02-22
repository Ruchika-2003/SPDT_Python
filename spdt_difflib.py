import re
import clang.cindex
from zss import simple_distance, Node
import itertools
from prettytable import PrettyTable
import os
import subprocess
import time
import difflib

# Memoization cache for storing previously calculated ASTs and similarities
ast_cache = {}
similarity_cache = {}

def extract_functions(code):
    functions = re.findall(r'\b(?:(?:void|int|float|double|char|bool)\s+)?([a-zA-Z_]\w*)\s*\([^)]*\)\s*\{.*?\n?\s*\}', code, re.DOTALL)
    return functions

def generate_ast(code):
    code = re.sub(r'#include.*\n', '', code)

    # Retrieving AST corresponding to the code if present in cache
    if code in ast_cache:
        return ast_cache[code]

    index = clang.cindex.Index.create()
    tu = index.parse('code.cpp', args=['-std=c++11'], unsaved_files=[('code.cpp', code)])

    # Storing AST in cache
    ast_cache[code] = tu.cursor
    return tu.cursor

def build_tree(node, depth=0):
    result = '  ' * depth + str(node.kind) + '\n'
    for child in node.get_children():
        result += build_tree(child, depth + 1)
    return result

def calculate_tree_size(node):
    size = 1
    for child in node.get_children():
        size += calculate_tree_size(child)
    return size

def count_changes(ast_str1, ast_str2):
    differ = difflib.Differ()
    diff = list(differ.compare(ast_str1.splitlines(keepends=True), ast_str2.splitlines(keepends=True)))

    additions = sum(1 for line in diff if line.startswith('+ '))
    removals = sum(1 for line in diff if line.startswith('- '))

    return additions, removals

def compare_functions(file_name1, func1, file_name2, func2):
    # Retrieve similarity if calculated earlier
    if (file_name1, func1, file_name2, func2) in similarity_cache:
        return similarity_cache[(file_name1, func1, file_name2, func2)]

    code1 = extract_function_code(file_name1, func1)
    code2 = extract_function_code(file_name2, func2)

    tree1 = build_tree(generate_ast(code1))
    tree2 = build_tree(generate_ast(code2))

    distance = simple_distance(tree1, tree2)
    max_possible_distance = max(calculate_tree_size(tree1), calculate_tree_size(tree2))
    similarity = 1 - (distance / max_possible_distance)

    #Storing simailrity in cache
    similarity_cache[(file_name1, func1, file_name2, func2)] = similarity

    return similarity

def extract_function_code(file_name, function_name):
    with open(file_name, 'r') as file:
        code = file.read()

    func_start = code.find(function_name)
    func_end = code.find('}', func_start)
    function_code = code[func_start:func_end+1]

    return function_code

def calculate_similarity(cpp_file1, cpp_file2):

    with open(cpp_file1, 'r') as file1:
        code1 = file1.read()

    with open(cpp_file2, 'r') as file2:
        code2 = file2.read()

    ast_root1 = generate_ast(code1)
    ast_root2 = generate_ast(code2)

    # Calculate tree size for both ASTs
    tree_size1 = calculate_tree_size(ast_root1)
    tree_size2 = calculate_tree_size(ast_root2)

    # Convert ASTs to string representations
    ast_str1 = build_tree(ast_root1)
    ast_str2 = build_tree(ast_root2)

    # Perform comparison based on ASTs
    additions, removals = count_changes(ast_str1, ast_str2)
    edit_op = max(additions, removals)

    # Print tree size
    max_tree_size = max(tree_size1,tree_size2)
    similarity = (1 - (edit_op/max_tree_size))

    """
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        code1 = f1.read()
        code2 = f2.read()

    #Retrieve AST if already in cache
    if code1 in ast_cache:
        ast1 = ast_cache[code1]
    else:
        ast1 = generate_ast(code1)

    if code2 in ast_cache:
        ast2 = ast_cache[code2]
    else:
        ast2 = generate_ast(code2)

    tree1 = create_tree(ast1)
    tree2 = create_tree(ast2)

    distance = simple_distance(tree1, tree2)
    max_possible_distance = max(calculate_tree_size(tree1), calculate_tree_size(tree2))
    similarity = 1 - (distance / max_possible_distance) """

    functions1 = extract_functions(code1)
    functions2 = extract_functions(code2) 

    if 0.3 <= similarity < 0.8:
        filtered_functions1 = [func for func in functions1 if len(func) > 3]
        filtered_functions2 = [func for func in functions2 if len(func) > 3]
        return similarity, filtered_functions1, filtered_functions2
    else:
        return similarity, [], []

def get_conclusion(similarity):
    #Setting thresholds for conclusion and further computation
    if similarity < 0.3:
        return "No matches were found in your submission."
    elif similarity < 0.8:
        return "Plagiarism might be present."
    else:
        return "Plagiarism found."


def generate_html_diff_link(file_name1, file_name2):
    if os.path.isdir(file_name1) and os.path.isdir(file_name2):
        directory_name1 = os.path.basename(file_name1)
        directory_name2 = os.path.basename(file_name2)
        output_html = f"{directory_name1}_vs_{directory_name2}.html"
    else:
        output_html = f"{file_name1}_vs_{file_name2}.html"

    subprocess.run(['gumtree', 'htmldiff', file_name1, file_name2, '-o', output_html])
    return f"file://wsl.localhost/Ubuntu/root/{output_html}"


def combine_cpp_files(directory_name):
    directory = os.path.join(os.getcwd(), directory_name)
    new_file_path = os.path.join(directory, "fin_ent.cpp")

    # Checking if directory already contains fin_ent.cpp
    if os.path.exists(new_file_path):
        return new_file_path

    combined_code = ""
    include_statements = set()
    header_contents = ""
    function_definitions = ""

    # Finding all C++ source code files (both .cpp and .h) in the directory
    files = [file for file in os.listdir(directory) if file.endswith(".cpp") or file.endswith(".h")]

    # Integrating code from each file
    for file in files:
        with open(os.path.join(directory, file), "r") as f:
            code = f.read()

            # Extracting all the include statements
            file_include_statements = get_include_statements(code)
            include_statements.update(file_include_statements)

            if file.endswith(".h"):
                # Removing the preprocessing directives from header files
                code = remove_preprocessing_directives(code)

                # Combining header files content
                header_contents += code + "\n\n"
            else:
                # Combining function definitions from .cpp files without #include statements
                code = remove_include_directives(code)
                function_definitions += code + "\n\n"

    # Generating include statements block
    include_block = "\n".join(include_statements)

    # Combining the blocks to make the final code
    final_code = include_block + "\n\n" + header_contents + function_definitions

    # Writing the combined code to the file "fin_ent.cpp"
    with open(new_file_path, "w") as f:
        f.write(final_code)
    return new_file_path

def get_include_statements(code):
    lines = code.split("\n")
    include_statements = []

    for line in lines:
        line = line.strip()
        if line.startswith("#include <") and line.endswith(">"):
            include_statements.append(line)

    return include_statements

def remove_preprocessing_directives(code):
    lines = code.split("\n")
    new_lines = []

    for line in lines:
        if not line.strip().startswith("#"):
            new_lines.append(line)

    return "\n".join(new_lines)

def remove_include_directives(code):
    lines = code.split("\n")
    new_lines = []

    for line in lines:
        if not line.strip().startswith("#include"):
            new_lines.append(line)

    return "\n".join(new_lines)

def preprocess_cpp_code(input_code):
    # Making sure that start.cpp and preprocessed.cpp are empty before proceeding
    open("start.cpp", "w").close()
    open("preprocessed.cpp", "w").close()

    # Removing #include statements from input code
    input_code = "\n".join(line for line in input_code.splitlines() if not line.startswith("#include"))

    # Writing modified input code to start.cpp
    with open("start.cpp", "w") as start_file:
        start_file.write(input_code)

    # Extracting preprocessed code with # statments
    subprocess.run(["g++", "-E", "start.cpp", "-o", "preprocessed.cpp"])

    # Removing # code lines from code obtained above
    with open("preprocessed.cpp", "r") as preprocessed_file:
        lines = preprocessed_file.readlines()
        processed_lines = [line for line in lines if not line.startswith("#")]

    # Writing processed lines back to preprocessed.cpp
    with open("preprocessed.cpp", "w") as preprocessed_file:
        preprocessed_file.writelines(processed_lines)

    # Reading and returning preprocessed code
    with open("preprocessed.cpp", "r") as preprocessed_file:
        preprocessed_code = preprocessed_file.read()

    return preprocessed_code

def main():
    alias_command = "alias spdt='python3'"
    subprocess.run(alias_command, shell=True)

    try :
        file_names = []
        import sys

        if len(sys.argv) > 1:
            input_names = sys.argv[1:]

            all_directories = all(os.path.isdir(os.path.abspath(name)) for name in input_names)

            all_files = all(not os.path.isdir(os.path.abspath(name)) for name in input_names)

            if all_files:
                # Preprocessing codes if input is all file names for computation and saving preprocessed code in file_name_p.cpp form
                for file_name in input_names:
                    abs_file_path = os.path.abspath(file_name)
                    if os.path.exists(abs_file_path):
                        preprocessed_code = preprocess_cpp_code(open(abs_file_path, 'r').read())
                        preprocessed_file_path = abs_file_path.replace(".cpp", "_p.cpp")
                        with open(preprocessed_file_path, 'w') as file:
                            file.write(preprocessed_code)
                        file_names.append(preprocessed_file_path)
                    else:
                        print(f"Error: {file_name} is not present.")
                        files_present = False
                        return

            if all_directories:
                for name in input_names:
                    # Creating fin_ent.cpp if not present
                    new_file_path = combine_cpp_files(name)
                    if new_file_path:
                        print(f"Processing directory: {name}")
                        file_names.append(new_file_path)
            else:
                file_names = input_names

            validated_file_paths = []
            for file_name in file_names:
                abs_file_path = os.path.abspath(file_name)
                if os.path.exists(abs_file_path):
                    validated_file_paths.append(abs_file_path)
                else:
                    print(f"Error: {file_name} is not present.")
                    files_present = False
                    return

            print("Checking files . . . .")
            files_present = True
            # For storing the number of nodes for each file
            file_node_counts = {}

            for file_path in validated_file_paths:
                file_name = os.path.basename(file_path)
                if (all_directories == False):
                    print(f"Processing {file_name} ...")

                # Generating the AST and creating the tree         |----------------------------FIX------------------------------|
                ast = generate_ast(open(file_path, 'r').read())
                num_nodes = calculate_tree_size(ast)
                file_node_counts[file_name] = num_nodes

            if files_present:
                total_nodes = 0
                for file_name, num_nodes in file_node_counts.items():
                    total_nodes += num_nodes

                # Algorithm to decide threshold
                average_nodes = total_nodes // len(file_node_counts)
                nearest_factor_of_10 = (average_nodes // 10) * 10

                for pair in itertools.combinations(file_node_counts.keys(), 2):
                    file_name1, file_name2 = pair
                    nodes_diff = abs(file_node_counts[file_name1] - file_node_counts[file_name2])

                print("\nWaiting for response . . . .")
                start_time = time.time()

                file_pairs = list(itertools.combinations(file_names, 2))
                similarities = []
                similar_pairs = []
                excluded_pairs = []

                for pair in file_pairs:
                    file_name1, file_name2 = pair
                    nodes_diff = abs(
                        file_node_counts[os.path.basename(file_name1)] - file_node_counts[os.path.basename(file_name2)])

                    if nodes_diff > nearest_factor_of_10:
                        excluded_pairs.append(pair)
                    else:
                        similarity, functions1, functions2 = calculate_similarity(file_name1, file_name2)
                        similarities.append((pair, similarity))
                        if functions1 and functions2 and 0.3 <= similarity < 0.8:
                            similar_pairs.append((file_name1, file_name2, functions1, functions2))

                main_table = PrettyTable()

                if all_directories:
                    main_table.field_names = ["Dir 1", "Dir 2", "Percentage Similarity", "Conclusion", "HTML Diff Link"]
                else:
                    main_table.field_names = ["File 1", "File 2", "Percentage Similarity", "Conclusion",
                                              "HTML Diff Link"]

                similarities = [(pair, similarity * 100) for pair, similarity in similarities if
                                pair not in excluded_pairs]
                similarities.sort(key=lambda x: (-x[1], x[0]))

                for pair, similarity in similarities:
                    file_name1, file_name2 = pair
                    conclusion = get_conclusion(similarity / 100)

                    if similarity < 0:
                        similarity_entry = f"{abs(similarity):.2f}%(*)"
                    else:
                        similarity_entry = f"{similarity:.2f}%"

                    if all_directories:
                        output_html_file = f"{os.path.basename(os.path.dirname(file_name1))}_vs_{os.path.basename(os.path.dirname(file_name2))}.html"
                    else:
                        output_html_file = f"{os.path.basename(file_name1)}_vs_{os.path.basename(file_name2)}.html"
                    subprocess.run(['gumtree', 'htmldiff', file_name1, file_name2, '-o', output_html_file])

                    # Adjust the HTML link generation to use the absolute file path
                    html_link = f"file://wsl.localhost/Ubuntu{os.path.abspath(output_html_file)}"

                    if all_directories:
                        main_table.add_row([os.path.basename(os.path.dirname(file_name1)),
                                            os.path.basename(os.path.dirname(file_name2)), similarity_entry, conclusion,
                                            html_link])
                    else:
                        main_table.add_row([file_name1, file_name2, similarity_entry, conclusion, html_link])

                for pair in excluded_pairs:
                    file_name1, file_name2 = pair
                    html_link = generate_html_diff_link(file_name1, file_name2)
                    main_table.add_row(
                        [file_name1, file_name2, "--", "No matches were found in your submission.", html_link])

                print(main_table)

                for file_name1, file_name2, functions1, functions2 in similar_pairs:
                    print(f"\n* Function comparison for {file_name1} and {file_name2}:")
                    print(f"\nTotal number of functions in {file_name1}: {len(functions1)}")
                    print("Function names:")
                    for func in sorted(functions1):
                        print(func)

                    print(f"\nTotal number of functions in {file_name2}: {len(functions2)}")
                    print("Function names:")
                    for func in sorted(functions2):
                        print(func)

                    func_table = PrettyTable()
                    func_table.field_names = [file_name1, file_name2, "Percentage Similarity"]

                    func_similarity_list = []
                    for func1, func2 in itertools.product(functions1, functions2):
                        func_similarity = compare_functions(file_name1, func1, file_name2, func2)
                        func_similarity_list.append((func1, func2, f"{func_similarity * 100:.2f}%"))

                    func_similarity_list.sort(key=lambda x: float(x[2].rstrip('%')), reverse=True)

                    for func1, func2, func_similarity in func_similarity_list:
                        func_table.add_row([func1, func2, func_similarity])
                    print("\n* Function based percentage similarity")
                    print(func_table)

                end_time = time.time()
                execution_time = end_time - start_time
                print("\nExecution time:", execution_time, "seconds.")

    except Exception as e:
        print("Oops! An error occurred:", e)
        return

if __name__ == "__main__":
    main()

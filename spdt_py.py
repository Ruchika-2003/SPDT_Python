import itertools
import sys
import os
import ast
from zss import simple_distance
from prettytable import PrettyTable
import time
import subprocess
import re

class CustomNode:
    def __init__(self, label, children):
        self.label = label
        self.children = children

def get_unique_pairs(names):
    print("\n\nWaiting for response. . . .")
    pairs = list(itertools.combinations(names, 2))
    return pairs

def read_content(name):
    with open(name, "r") as file:
        content = file.read()
    return content

def get_ast(content):
    return ast.parse(content)

# Cache to store generated ASTs
ast_cache = {}

def get_cached_ast(name):
    if name in ast_cache:
        return ast_cache[name]
    else:
        content = read_content(name)
        ast_content = get_ast(content)
        ast_cache[name] = ast_content
        return ast_content
    
def convert_ast_to_custom(node):
    children = [convert_ast_to_custom(child) for child in ast.iter_child_nodes(node)]
    return CustomNode(node.__class__.__name__, children)

def calculate_tree_size(node):
    if not node.children:
        return 1
    else:
        return 1 + sum(calculate_tree_size(child) for child in node.children)

def calculate_similarity(ast1, ast2):
    ast1_custom = convert_ast_to_custom(ast1)
    ast2_custom = convert_ast_to_custom(ast2)

    tree_size1 = calculate_tree_size(ast1_custom)
    tree_size2 = calculate_tree_size(ast2_custom)
    if abs(tree_size1-tree_size2)>threshold :
        return 0
    
    else :
        return 1 - (simple_distance(ast1_custom, ast2_custom, lambda n: n.children) /max(tree_size1, tree_size2))
    
def calculate_threshold(input_items):
    total_nodes = 0
    total_files = 0

    for item in input_items:
        if os.path.isdir(item):
            python_files = get_python_files_in_directory(item)
            for file in python_files:
                ast_tree = get_cached_ast(file)
                total_nodes += calculate_tree_size(convert_ast_to_custom(ast_tree))
                total_files += 1
        else:
            ast_tree = get_cached_ast(item)
            total_nodes += calculate_tree_size(convert_ast_to_custom(ast_tree))
            total_files += 1

    if total_files == 0:
        print("Error: No files found for calculating the threshold.")
        sys.exit(1)

    average_nodes = total_nodes // total_files
    threshold = (average_nodes // 10) * 10
    return threshold

def generate_html_diff_link(name1, name2, use_directory_name=False):
    if use_directory_name:
        parent_directory1 = os.path.basename(os.path.dirname(name1))
        parent_directory2 = os.path.basename(os.path.dirname(name2))
        output_html_file = f"{parent_directory1}_vs_{parent_directory2}.html"
    else:
        file1_name = os.path.basename(name1)
        file2_name = os.path.basename(name2)
        output_html_file = f"{file1_name}_vs_{file2_name}.html"

    subprocess.run(['gumtree', 'htmldiff', name1, name2, '-o', output_html_file])   

    return f"http://localhost:8080/{output_html_file}"

def get_conclusion(similarity):
    if similarity < 0.3:
        return "No matches found in your submission"
    elif similarity < 0.8:
        return "Plagiarism might be present"
    else:
        return "Plagiarism found"

def compare_items(item1, item2):
    if os.path.isdir(item1) and os.path.isdir(item2):
        fin_ent1 = find_fin_ent_py(item1)
        fin_ent2 = find_fin_ent_py(item2)

        if fin_ent1 is None or fin_ent2 is None:
            return None, 0.0

        file1_ast = get_cached_ast(fin_ent1)
        file2_ast = get_cached_ast(fin_ent2)

        print(f"Tree size 1 :{calculate_tree_size(convert_ast_to_custom(file1_ast))}")
        print(f"Tree size 2 :{calculate_tree_size(convert_ast_to_custom(file2_ast))}")
        print(f"Threshold : {threshold}")

        if (calculate_tree_size(convert_ast_to_custom(file1_ast)) - calculate_tree_size(convert_ast_to_custom(file2_ast))) <= threshold:
            similarity = calculate_similarity(file1_ast, file2_ast)
        else:
            similarity = 0

        return item1, item2, similarity, generate_html_diff_link(fin_ent1, fin_ent2, use_directory_name=True)
    else:
        file1_ast = get_cached_ast(item1)
        file2_ast = get_cached_ast(item2)

        if (calculate_tree_size(convert_ast_to_custom(file1_ast)) - calculate_tree_size(convert_ast_to_custom(file2_ast))) <= threshold:
            similarity = calculate_similarity(file1_ast, file2_ast)
        else:
            similarity = 0

        return item1, item2, similarity, generate_html_diff_link(item1, item2)


def find_fin_ent_py(directory):
    for root, _, files in os.walk(directory):
        if 'fin_ent.py' in files:
            return os.path.join(root, 'fin_ent.py')
    return None


def get_python_files_in_directory(directory):
    python_files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(".py")]

    new_files = []

    for file in python_files:
        if file.endswith("_p.py"):
            continue  # Skip existing _p.py files

        input_file_path = os.path.join(directory, file)
        output_file_path = os.path.join(directory, f"{os.path.splitext(file)[0]}_p.py")

        with open(input_file_path, 'r') as file:
            file_content = file.read()

            # Use regex to find content between #TODO and # END TODO
            pattern = r'(#\s*TODO:.*?# END TODO)'
            matches = re.findall(pattern, file_content, re.DOTALL)

            if matches:
                new_content = matches[0].strip()

                # Write or overwrite the content to the new file
                with open(output_file_path, "w") as output_file:
                    output_file.write(new_content)

                new_files.append(output_file_path)

    return new_files




if __name__ == "__main__":
    try:
        # Try to connect to the server using curl
        subprocess.run(["curl", f"http://localhost:{8080}", "--silent", "--output", os.devnull], check=True)
    except subprocess.CalledProcessError:
        # The server is not running
        subprocess.Popen(["python3", "-m", "http.server","8080"],stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if len(sys.argv) < 2:
        print("Usage: python script_name.py item1 item2 ...")
        sys.exit(1)

    input_item = sys.argv[1]

    if os.path.isdir(input_item) or len(sys.argv) > 2:
        # If the input is a directory or there are multiple inputs, proceed as before
        input_items = get_python_files_in_directory(input_item) if os.path.isdir(input_item) else sys.argv[1:]
    else:
        # If only one input is provided and it's not a directory, throw an error
        print("Error : For single input only directory is accepted")
        sys.exit(1)

    print("Checking input...")
    for item in input_items:
        if not os.path.exists(item):
            print(f"The item '{item}' does not exist.")
            sys.exit(1)
        else:
            print(f"{item} present....")

    start_time = time.time()
        
    threshold = calculate_threshold(input_items)
    use_directory_name = all(os.path.isdir(item) for item in input_items)

    # Call the function to get unique pairs (implementation not provided)
    unique_pairs = get_unique_pairs(input_items)

    table = PrettyTable()
    table.field_names = ["Submission1", "Submission2", "Percentage Similarity", "Conclusion", "HTML Diff Link"]

    rows = []

    for pair in unique_pairs:
        item1, item2, similarity, html_diff_link = compare_items(pair[0], pair[1])
        if similarity is not None:
            conclusion = get_conclusion(similarity)
            rows.append((item1, item2, similarity, conclusion, html_diff_link))

    sorted_rows = sorted(rows, key=lambda x: x[2], reverse=True)  # Sort rows by similarity in reverse order

for row in sorted_rows:
    percentage_similarity = f"{row[2] * 100:.2f}%" if row[2] is not None and row[2] != 0 else "--"
    table.add_row([row[0], row[1], percentage_similarity, row[3], row[4]])

        
print(table)

end_time = time.time()
execution_time = end_time - start_time
print("Note : -- indicates exclusion due to node difference exceeding the threshold. ")
print("\nExecution time:", execution_time, "seconds.")
# Software Plagiarism Detection Tool - For python

## Overview
The Software Plagiarism Detection Tool (SPDT) is designed to aid in the detection of plagiarism within C++ programming language code by employing advanced techniques to analyze the structural similarity of code snippets and provides insightful results, including a percentage similarity score and a conclusion regarding the presence of plagiarism. Additionally, the tool offers a visual representation of the code differences using the Gumtree Diff Tool, enhancing the comprehensibility of the analysis

#
## Features
- Accurate Plagiarism Detection :
Software Plagiarism Detection Tool leverages the concept of abstract syntax trees (ASTs) to assess the structural resemblance between code samples. It employs the Zhang-Shasha algorithm to compute the minimum number of edit operations required to transform one AST into another. This value is then utilized to calculate the percentage similarity between the input code snippets.

- User-Friendly Input :
Users can input either the names of individual files or directories containing multiple files for analysis. The tool processes these inputs and generates comprehensive reports.

- Detailed Output :
The tool produces a structured report for every code comparison, featuring essential information such as file/directory names, percentage similarity, and a decisive verdict. It goes beyond by presenting visual renderings of the code and, when warranted by similarity falling within a specified range, conducts a function-oriented analysis to detect potential plagiarism strategies like reordering. This holistic methodology delivers precise and actionable insights into the genuineness of the examined code.

- Visual Comparison :
The tool enhances its analysis by visually presenting the differences between code snippets. The Gumtree Diff Tool highlights the exact modifications made to the code, making it easier for users to identify potential instances of plagiarism as a manual check in addition to the reult provided by the tool.

# 
## Methodology
-  Input and Preprocessing :
    - Collect file names or directories from the main code directory.
    -  Preprocess individual files for optimization.

-  AST Generation and Analysis :
    - Use clang.cindex to build abstract syntax trees (ASTs) for files or directories, capturing essential structural elements.

-  Zhang-Shasha Algorithm:
    -  Apply the Zhang-Shasha algorithm to calculate minimum edit operations for AST transformation, measuring structural similarity.

-  Percentage Similarity Computation :
    - Utilize the algorithm for percentage similarity calculation, objectively assessing structural congruence.

-  Visual Representation and Reporting: 
    - Employ the Gumtree Diff Tool for visual discrepancies.
    - Generate comprehensive reports with similarity scores and plagiarism verdicts.

#
## Requirements

Presence of gumtree diff tool ready for use

#


## Run Locally
For installing the project dependancies make use of the following command

```bash
  pip install requirements.txt
```


Go to the project directory which contains the required files or directories which are supposed to be tested with the tool

```bash
  cd my-project
```

Clone the project into the same directory that has your files and directories that are supposed to be verified for plagiarism

```bash
  git clone https://github.com/Ruchika-2003/Software_Plagiarism_Detection_Tool.git
```

Run this command to use the code present in Software_Plagiarism_Detection_Tool into the parent directory containing the files and directories on which tool is to be tested

```bash
  cp Software_Plagiarism_Detection_Tool/dt.py .
```


Enter the below as a command

```bash
  alias spdt='python3'
```

Run the code with below command

```bash
  spdt dt.py file_names/directory_names
```

For visual comparison - If gumtree is not already present refer this for installation

[https://github.com/GumTreeDiff/gumtree/wiki/Getting-Started](url)



## Addressing Diverse Plagiarism Cases


The tool tackles a spectrum of plagiarism instances, including:

  1. Variable Renaming : 
    Detects cases where variables or identifiers are altered to obfuscate code similarities.

  2. Code Reordering: 
    Identifies rearrangements of code blocks within the codes being analysed

  3. Preprocessing Diversity: 
    Cognizant of randomly inserted preprocessing directives that aim to confound detection.

  4. Redundant Comments : 
    Recognizes superfluous comments added in attempts to disguise plagiarized content.

  5. Algorithmic Variations: 
    Captures alterations in iterative loops or computation approaches while achieving comparable outputs.

# 
## Manual Verification and Limitations

While the tool comprehensively addresses numerous plagiarism scenarios, it is important to acknowledge its limitations. In cases where redundant variables are introduced and updated intermittently throughout the codebase, the tool's reliance on AST structure analysis might lead to false positives. Addressing this concern involves a transition towards semantic analysis, which is an avenue for future enhancement.
# 

## Prudent Strategies and Reflective Considerations

This Software Plagiarism Detection Tool presents a potent solution for automating code plagiarism detection. However, to ensure utmost accuracy, combining the tool's outcomes with manual scrutiny is recommended. Combining computer analysis and human insight helps us effectively prevent plagiarism.








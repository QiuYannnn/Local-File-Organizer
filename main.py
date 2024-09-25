import os
import time

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_text_file,
    read_pdf_file,
    read_docx_file,
    check_hard_link_support
)

from data_processing import (
    initialize_models,
    process_image_files,
    process_text_files,
    copy_and_rename_files
)

def simulate_directory_tree(operations, base_path):
    """Simulate the directory tree based on the proposed operations."""
    tree = {}
    for op in operations:
        rel_path = os.path.relpath(op['destination'], base_path)
        parts = rel_path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]
    return tree

def print_simulated_tree(tree, prefix=''):
    """Print the simulated directory tree."""
    pointers = ['├── '] * (len(tree) - 1) + ['└── '] if tree else []
    for pointer, key in zip(pointers, tree):
        print(prefix + pointer + key)
        if tree[key]:  # If there are subdirectories or files
            extension = '│   ' if pointer == '├── ' else '    '
            print_simulated_tree(tree[key], prefix + extension)

def main():
    # Paths configuration
    print("-" * 50)
    print("Checking if the model is already downloaded. If not, downloading it now.")

    # Initialize models once
    initialize_models()

    input_path = input("Enter the path of the directory you want to organize: ").strip()
    if not os.path.exists(input_path):
        print(f"Input path {input_path} does not exist. Please create it and add the necessary files.")
        return

    # Confirm successful input path
    print(f"Input path successfully uploaded: {input_path}")
    print("-" * 50)

    # Default output path is a folder named "organized_folder" in the same directory as the input path
    output_path = input("Enter the path to store organized files and folders (press Enter to use 'organized_folder' in the input directory): ").strip()
    if not output_path:
        # Get the parent directory of the input path and append 'organized_folder'
        output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Confirm successful output path
    print(f"Output path successfully uploaded: {output_path}")
    print("-" * 50)

    # Start processing files
    start_time = time.time()
    file_paths = collect_file_paths(input_path)
    end_time = time.time()

    print(f"Time taken to load file paths: {end_time - start_time:.2f} seconds")
    print("-" * 50)
    print("Directory tree before organizing:")
    display_directory_tree(input_path)

    print("*" * 50)
    print("The file upload was successful. Processing may take a few minutes.")
    print("*" * 50)

    # Check for hard link support
    hard_link_supported = check_hard_link_support()
    if hard_link_supported:
        print("Your filesystem supports hard links. The script will use hard links instead of copying files.")
    else:
        print("Your filesystem does not support hard links. The script will copy files instead.")
    print("-" * 50)

    # Always perform a dry run first
    dry_run = True

    # Separate files by type
    image_files, text_files = separate_files_by_type(file_paths)

    # Prepare text tuples for processing
    text_tuples = []
    for fp in text_files:
        ext = os.path.splitext(fp.lower())[1]
        if ext == '.txt':
            text_content = read_text_file(fp)
        elif ext == '.docx':
            text_content = read_docx_file(fp)
        elif ext == '.pdf':
            text_content = read_pdf_file(fp)
        else:
            print(f"Unsupported text file format: {fp}")
            continue  # Skip unsupported file formats
        text_tuples.append((fp, text_content))

    # Process files sequentially
    data_images = process_image_files(image_files)
    data_texts = process_text_files(text_tuples)

    # Prepare for copying and renaming
    renamed_files = set()
    processed_files = set()

    # Combine all data
    all_data = data_images + data_texts

    # Copy and rename files (perform dry run)
    operations = copy_and_rename_files(
        all_data,
        output_path,
        renamed_files,
        processed_files,
        use_hard_links=hard_link_supported,
        dry_run=True  # Always perform dry run first
    )

    # Simulate and display the proposed directory tree
    print("Proposed directory structure:")
    simulated_tree = simulate_directory_tree(operations, output_path)
    print(os.path.abspath(output_path))
    print_simulated_tree(simulated_tree)
    print("-" * 50)

    # Ask user if they want to proceed
    proceed = input("Would you like to proceed with these changes? (yes/no): ").strip().lower()
    if proceed not in ('yes', 'y'):
        print("Operation canceled by the user.")
        return

    # Perform the actual file operations
    print("Performing file operations...")
    renamed_files = set()  # Reset renamed files
    processed_files = set()  # Reset processed files

    copy_and_rename_files(
        all_data,
        output_path,
        renamed_files,
        processed_files,
        use_hard_links=hard_link_supported,
        dry_run=False  # Now perform the operations
    )

    print("-" * 50)
    print("The folder contents have been renamed and organized successfully.")
    print("-" * 50)
    print("Directory tree after organizing:")
    # display_directory_tree(output_path)

if __name__ == '__main__':
    main()

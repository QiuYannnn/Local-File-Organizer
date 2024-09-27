import os
import time

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_text_file,
    read_pdf_file,
    read_docx_file
)

from data_processing import (
    initialize_models,
    process_image_files,
    process_text_files,
    compute_operations,
    execute_operations
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
    # Start with dry run set to True
    dry_run = True

    # Ask the user if they want to enable silent mode at the beginning
    silent_mode_input = input("Would you like to enable silent mode? (yes/no): ").strip().lower()
    silent_mode = silent_mode_input in ('yes', 'y')
    log_file = 'operation_log.txt' if silent_mode else None

    # Paths configuration
    if not silent_mode:
        print("-" * 50)
        print("Checking if the model is already downloaded. If not, downloading it now.")

    # Initialize models once
    initialize_models()

    input_path = input("Enter the path of the directory you want to organize: ").strip()
    if not os.path.exists(input_path):
        message = f"Input path {input_path} does not exist. Please create it and add the necessary files."
        if silent_mode:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
        return

    # Confirm successful input path
    message = f"Input path successfully uploaded: {input_path}"
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    else:
        print(message)
    if not silent_mode:
        print("-" * 50)

    # Default output path is a folder named "organized_folder" in the same directory as the input path
    output_path = input("Enter the path to store organized files and folders (press Enter to use 'organized_folder' in the input directory): ").strip()
    if not output_path:
        # Get the parent directory of the input path and append 'organized_folder'
        output_path = os.path.join(os.path.dirname(input_path), 'organized_folder')

    # Do not create the output directory yet
    # os.makedirs(output_path, exist_ok=True)

    # Confirm successful output path
    message = f"Output path successfully set to: {output_path}"
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    else:
        print(message)
    if not silent_mode:
        print("-" * 50)

    # Start processing files
    start_time = time.time()
    file_paths = collect_file_paths(input_path)
    end_time = time.time()

    message = f"Time taken to load file paths: {end_time - start_time:.2f} seconds"
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    else:
        print(message)
    if not silent_mode:
        print("-" * 50)
        print("Directory tree before organizing:")
        display_directory_tree(input_path)

        print("*" * 50)
        print("The file upload was successful. Processing may take a few minutes.")
        print("*" * 50)

    # Prepare to collect link type statistics
    link_type_counts = {'hardlink': 0, 'symlink': 0}

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
            message = f"Unsupported text file format: {fp}"
            if silent_mode:
                with open(log_file, 'a') as f:
                    f.write(message + '\n')
            else:
                print(message)
            continue  # Skip unsupported file formats
        text_tuples.append((fp, text_content))

    # Process files sequentially
    data_images = process_image_files(image_files, silent=silent_mode, log_file=log_file)
    data_texts = process_text_files(text_tuples, silent=silent_mode, log_file=log_file)

    # Prepare for copying and renaming
    renamed_files = set()
    processed_files = set()

    # Combine all data
    all_data = data_images + data_texts

    # Compute the operations
    operations = compute_operations(
        all_data,
        output_path,
        renamed_files,
        processed_files
    )

    # Count link types
    for op in operations:
        link_type_counts[op['link_type']] += 1

    # Inform the user about link types being used
    if not silent_mode:
        print("-" * 50)
        print("Link types to be used for organizing files:")
        print(f"Hardlinks: {link_type_counts['hardlink']}")
        print(f"Symlinks: {link_type_counts['symlink']}")
        print("-" * 50)

    # Simulate and display the proposed directory tree
    message = "Proposed directory structure:"
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    else:
        print(message)
        print(os.path.abspath(output_path))
        simulated_tree = simulate_directory_tree(operations, output_path)
        print_simulated_tree(simulated_tree)
        print("-" * 50)

    # Ask user if they want to proceed
    proceed = input("Would you like to proceed with these changes? (yes/no): ").strip().lower()
    if proceed not in ('yes', 'y'):
        message = "Operation canceled by the user."
        if silent_mode:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
        else:
            print(message)
        return

    # Create the output directory now
    os.makedirs(output_path, exist_ok=True)

    # Perform the actual file operations
    message = "Performing file operations..."
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write(message + '\n')
    else:
        print(message)
    execute_operations(
        operations,
        dry_run=False,
        silent=silent_mode,
        log_file=log_file
    )

    message = "The files have been organized successfully."
    if silent_mode:
        with open(log_file, 'a') as f:
            f.write("-" * 50 + '\n' + message + '\n' + "-" * 50 + '\n')
    else:
        print("-" * 50)
        print(message)
        print("-" * 50)

if __name__ == '__main__':
    main()

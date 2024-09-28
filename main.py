import os
import time

from file_utils import (
    display_directory_tree,
    collect_file_paths,
    separate_files_by_type,
    read_file_data  # Import read_file_data
)

from data_processing_common import (
    compute_operations,
    execute_operations,
    process_files_by_date,
    process_files_by_type,
)

from text_data_processing import (
    process_text_files
)

from image_data_processing import (
    process_image_files
)

from output_filter import filter_specific_output  # Import the context manager
from nexa.gguf import NexaVLMInference, NexaTextInference  # Import model classes

# Initialize models
image_inference = None
text_inference = None

def initialize_models():
    """Initialize the models if they haven't been initialized yet."""
    global image_inference, text_inference
    if image_inference is None or text_inference is None:
        # Initialize the models
        model_path = "llava-v1.6-vicuna-7b:q4_0"
        model_path_text = "gemma-2-2b-instruct:q4_0"

        # Use the filter_specific_output context manager
        with filter_specific_output():
            # Initialize the image inference model
            image_inference = NexaVLMInference(
                model_path=model_path,
                local_path=None,
                stop_words=[],
                temperature=0.3,
                max_new_tokens=3000, 
                top_k=3,
                top_p=0.2,
                profiling=False
            )

            # Initialize the text inference model
            text_inference = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=3000,  # Adjust as needed
                top_k=3,
                top_p=0.3,
                profiling=False
            )
        print("**----------------------------------------------**")
        print("**       Image inference model initialized      **")
        print("**       Text inference model initialized       **")
        print("**----------------------------------------------**")

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

    # Ask the user to choose the mode
    print("Please choose the mode to organize your files:")
    print("1. By Content")
    print("2. By Date")
    print("3. By Type")
    mode_input = input("Enter 1, 2, or 3: ").strip()

    if mode_input == '1':
        mode = 'content'
    elif mode_input == '2':
        mode = 'date'
    elif mode_input == '3':
        mode = 'type'
    else:
        print("Invalid selection. Defaulting to Content mode.")
        mode = 'content'



    if mode == 'content':
        # Proceed with content mode
        # Initialize models once
        if not silent_mode:
            print("Checking if the model is already downloaded. If not, downloading it now.")
        initialize_models()

        if not silent_mode:
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
            # Use read_file_data to read the file content
            text_content = read_file_data(fp)
            if text_content is None:
                message = f"Unsupported or unreadable text file format: {fp}"
                if silent_mode:
                    with open(log_file, 'a') as f:
                        f.write(message + '\n')
                else:
                    print(message)
                continue  # Skip unsupported or unreadable files
            text_tuples.append((fp, text_content))

        # Process files sequentially
        data_images = process_image_files(image_files, image_inference, text_inference, silent=silent_mode, log_file=log_file)
        data_texts = process_text_files(text_tuples, text_inference, silent=silent_mode, log_file=log_file)


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

    elif mode == 'date':
        # Process files by date
        operations = process_files_by_date(file_paths, output_path, dry_run=False, silent=silent_mode, log_file=log_file)
    elif mode == 'type':
        # Process files by type
        operations = process_files_by_type(file_paths, output_path, dry_run=False, silent=silent_mode, log_file=log_file)
    else:
        print("Invalid mode selected.")
        return

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

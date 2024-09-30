import os
import shutil

import yaml
from nexa.gguf import NexaTextInference, NexaVLMInference

from file_utils import create_folder, sanitize_filename
from output_filter import filter_specific_output  # Import the context manager

# Global variables to hold the models
image_inference = None
text_inference = None


def load_prompts(yaml_file="prompts/prompts.yaml"):
    """Load prompts from a YAML file."""
    with open(yaml_file, "r") as file:
        prompts = yaml.safe_load(file)
    return prompts


# Load the prompts once globally
PROMPTS = load_prompts()


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
                max_new_tokens=256,  # Reduced to speed up processing
                top_k=3,
                top_p=0.2,
                profiling=False,
            )

            # Initialize the text inference model
            text_inference = NexaTextInference(
                model_path=model_path_text,
                local_path=None,
                stop_words=[],
                temperature=0.5,
                max_new_tokens=256,  # Reduced to speed up processing
                top_k=3,
                top_p=0.3,
                profiling=False,
            )
        print("**----------------------------------------------**")
        print("**       Image inference model initialized      **")
        print("**       Text inference model initialized       **")
        print("**----------------------------------------------**")


def get_text_from_generator(generator):
    """Extract text from the generator response."""
    response_text = ""
    try:
        while True:
            response = next(generator)
            choices = response.get("choices", [])
            for choice in choices:
                delta = choice.get("delta", {})
                if "content" in delta:
                    response_text += delta["content"]
    except StopIteration:
        pass
    return response_text


def generate_image_metadata(image_path):
    """Generate description, folder name, and filename for an image file."""
    initialize_models()

    # Get the description prompt from the loaded YAML prompts
    description_prompt = PROMPTS["image_prompts"]["description_prompt"]

    description_generator = image_inference._chat(description_prompt, image_path)
    description = get_text_from_generator(description_generator).strip()

    # Get and format the filename prompt
    filename_prompt = PROMPTS["image_prompts"]["filename_prompt"].replace(
        "{{ description }}", description
    )

    filename_response = text_inference.create_completion(filename_prompt)
    filename = filename_response["choices"][0]["text"].strip()
    filename = filename.replace("Filename:", "").strip()
    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename:
        sanitized_filename = "untitled_image"

    # Get and format the folder name prompt
    foldername_prompt = PROMPTS["image_prompts"]["foldername_prompt"].replace(
        "{{ description }}", description
    )

    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername = foldername_response["choices"][0]["text"].strip()
    foldername = foldername.replace("Category:", "").strip()
    sanitized_foldername = sanitize_filename(foldername)

    if not sanitized_foldername:
        sanitized_foldername = "images"

    return sanitized_foldername, sanitized_filename, description


def process_single_image(image_path):
    """Process a single image file to generate metadata."""
    foldername, filename, description = generate_image_metadata(image_path)
    print(f"File: {image_path}")
    print(f"Description: {description}")
    print(f"Folder name: {foldername}")
    print(f"Generated filename: {filename}")
    print("-" * 50)
    return {
        "file_path": image_path,
        "foldername": foldername,
        "filename": filename,
        "description": description,
    }


def process_image_files(image_paths):
    """Process image files sequentially."""
    data_list = []
    for image_path in image_paths:
        data = process_single_image(image_path)
        data_list.append(data)
    return data_list


def summarize_text_content(text):
    """Summarize the given text content."""
    initialize_models()

    prompt = f"""Provide a concise and accurate summary of the following text, focusing on the main ideas and key details.
Limit your summary to a maximum of 150 words.

Text: {text}

Summary:"""

    response = text_inference.create_completion(prompt)
    summary = response["choices"][0]["text"].strip()
    return summary


def generate_text_metadata(input_text):
    """Generate description, folder name, and filename for a text document."""
    initialize_models()

    # Get the summary prompt from the loaded YAML prompts
    summary_prompt = PROMPTS["text_prompts"]["summary_prompt"].replace(
        "{{ text }}", input_text
    )

    response = text_inference.create_completion(summary_prompt)
    summary = response["choices"][0]["text"].strip()

    # Get and format the filename prompt
    filename_prompt = PROMPTS["text_prompts"]["filename_prompt"].replace(
        "{{ summary }}", summary
    )

    filename_response = text_inference.create_completion(filename_prompt)
    filename = filename_response["choices"][0]["text"].strip()
    filename = filename.replace("Filename:", "").strip()
    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename:
        sanitized_filename = "untitled_document"

    # Get and format the folder name prompt
    foldername_prompt = PROMPTS["text_prompts"]["foldername_prompt"].replace(
        "{{ summary }}", summary
    )

    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername = foldername_response["choices"][0]["text"].strip()
    foldername = foldername.replace("Category:", "").strip()
    sanitized_foldername = sanitize_filename(foldername)

    if not sanitized_foldername:
        sanitized_foldername = "documents"

    return sanitized_foldername, sanitized_filename, summary


def process_single_text_file(args):
    """Process a single text file to generate metadata."""
    file_path, text = args
    foldername, filename, description = generate_text_metadata(text)
    print(f"File: {file_path}")
    print(f"Description: {description}")
    print(f"Folder name: {foldername}")
    print(f"Generated filename: {filename}")
    print("-" * 50)
    return {
        "file_path": file_path,
        "foldername": foldername,
        "filename": filename,
        "description": description,
    }


def process_text_files(text_tuples):
    """Process text files sequentially."""
    results = []
    for args in text_tuples:
        data = process_single_text_file(args)
        results.append(data)
    return results


def copy_and_rename_files(data_list, new_path, renamed_files, processed_files):
    """Copy and rename files based on generated metadata."""
    for data in data_list:
        file_path = data["file_path"]
        if file_path in processed_files:
            continue
        processed_files.add(file_path)

        # Use folder name which generated from the description
        dir_path = create_folder(new_path, data["foldername"])

        # Use filename which generated from the description
        new_file_name = data["filename"] + os.path.splitext(file_path)[1]
        new_file_path = os.path.join(dir_path, new_file_name)

        # Handle duplicates
        counter = 1
        while new_file_path in renamed_files or os.path.exists(new_file_path):
            new_file_name = (
                f"{data['filename']}_{counter}" + os.path.splitext(file_path)[1]
            )
            new_file_path = os.path.join(dir_path, new_file_name)
            counter += 1

        shutil.copy2(file_path, new_file_path)
        renamed_files.add(new_file_path)
        print(f"Copied and renamed to: {new_file_path}")
        print("-" * 50)

import re
import os
import shutil
from nexa.gguf import NexaVLMInference, NexaTextInference
from file_utils import sanitize_filename, create_folder
from output_filter import filter_specific_output  # Import the context manager
# import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist

# # Ensure NLTK resources are downloaded
# nltk.download('punkt', quiet=True)
# nltk.download('stopwords', quiet=True)
# nltk.download('punkt_tab')

# Global variables to hold the models
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
                max_new_tokens=256,  # Reduced to speed up processing
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
                max_new_tokens=256,  # Reduced to speed up processing
                top_k=3,
                top_p=0.3,
                profiling=False
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
            choices = response.get('choices', [])
            for choice in choices:
                delta = choice.get('delta', {})
                if 'content' in delta:
                    response_text += delta['content']
    except StopIteration:
        pass
    return response_text

def generate_image_metadata(image_path):
    """Generate description, folder name, and filename for an image file."""
    initialize_models()

    # Generate description
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description_generator = image_inference._chat(description_prompt, image_path)
    description = get_text_from_generator(description_generator).strip()

    # Generate filename
    filename_prompt = f"""Based on the description below, generate a specific and descriptive filename (2-4 words) for the image.
Do not include any data type words like 'image', 'jpg', 'png', etc. Use only letters and connect words with underscores.
Avoid using any special characters, symbols, markdown, or code formatting.

Description: {description}

Example:
Description: A photo of a sunset over the mountains.
Filename: sunset_over_mountains

Now generate the filename.

Filename:"""
    filename_response = text_inference.create_completion(filename_prompt)
    filename = filename_response['choices'][0]['text'].strip()
    filename = filename.replace('Filename:', '').strip()

    # Remove markdown, code blocks, and special characters
    filename = re.sub(r'[\*\`\n]', '', filename)
    filename = filename.strip()

    # Check if the AI returned a generic or empty filename
    if not filename or filename.lower() in ('untitled', 'unknown', '', 'describes'):
        # Use the first few words of the description as the filename
        filename = '_'.join(description.split()[:3])

    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename or sanitized_filename.lower() in ('untitled', ''):
        sanitized_filename = 'image_' + os.path.splitext(os.path.basename(image_path))[0]

    # Generate folder name from description
    foldername_prompt = f"""Based on the description below, generate a general category or theme (1-2 words) that best represents the main subject of this image.
This will be used as the folder name. Do not include specific details, words from the filename, any generic terms like 'untitled' or 'unknown', or any special characters, symbols, numbers, markdown, or code formatting.

Description: {description}

Examples:
1. Description: A photo of a sunset over the mountains.
   Category: landscapes

2. Description: An image of a smartphone displaying a storage app with various icons and information.
   Category: technology

3. Description: A close-up of a blooming red rose with dew drops.
   Category: nature

Now generate the category.

Category:"""
    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername = foldername_response['choices'][0]['text'].strip()
    foldername = foldername.replace('Category:', '').strip()

    # Remove markdown, code blocks, and special characters
    foldername = re.sub(r'[\*\`\n]', '', foldername)
    foldername = foldername.strip()

    # Check if the AI returned a generic or empty category
    if not foldername or foldername.lower() in ('untitled', 'unknown', ''):
        # Attempt to extract a keyword from the description


        words = word_tokenize(description.lower())
        words = [word for word in words if word.isalpha()]
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word not in stop_words]
        fdist = FreqDist(filtered_words)
        most_common = fdist.most_common(1)
        if most_common:
            foldername = most_common[0][0]
        else:
            foldername = 'images'

    sanitized_foldername = sanitize_filename(foldername)

    if not sanitized_foldername:
        sanitized_foldername = 'images'

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
        'file_path': image_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
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
    summary = response['choices'][0]['text'].strip()
    return summary

def generate_text_metadata(input_text, file_path):
    """Generate description, folder name, and filename for a text document."""
    initialize_models()

    # Generate description
    description = summarize_text_content(input_text)

    # Generate filename
    filename_prompt =  f"""Based on the summary below, generate a specific and descriptive filename (2-4 words) that captures the essence of the document.
Do not include any data type words like 'text', 'document', 'pdf', etc. Use only letters and connect words with underscores. Avoid generic terms like 'describes'.

Summary: {description}

Examples:
1. Summary: A research paper on the fundamentals of string theory.
   Filename: fundamentals_of_string_theory

2. Summary: An article discussing the effects of climate change on polar bears.
   Filename: climate_change_polar_bears

Now generate the filename.

Filename:"""
    filename_response = text_inference.create_completion(filename_prompt)
    filename = filename_response['choices'][0]['text'].strip()
    filename = filename.replace('Filename:', '').strip()

    # Remove markdown, code blocks, and special characters
    filename = re.sub(r'[\*\`\n]', '', filename)
    filename = filename.strip()

    # Check if the AI returned a generic or empty filename
    if not filename or filename.lower() in ('untitled', 'unknown', '', 'describes'):
        # Use the first few words of the summary as the filename
        filename = '_'.join(description.split()[:3])

    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename or sanitized_filename.lower() in ('untitled', ''):
        sanitized_filename = 'document_' + os.path.splitext(os.path.basename(file_path))[0]

    # Generate folder name from summary
    foldername_prompt = f"""Based on the summary below, generate a general category or theme (1-2 words) that best represents the main subject of this document.
This will be used as the folder name. Do not include specific details, words from the filename, or any generic terms like 'untitled' or 'unknown'.

Summary: {description}

Examples:
1. Summary: A research paper on the fundamentals of string theory.
   Category: physics

2. Summary: An article discussing the effects of climate change on polar bears.
   Category: environment

Now generate the category.

Category:"""
    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername = foldername_response['choices'][0]['text'].strip()
    foldername = foldername.replace('Category:', '').strip()

    # Remove markdown, code blocks, and special characters
    foldername = re.sub(r'[\*\`\n]', '', foldername)
    foldername = foldername.strip()

    # Check if the AI returned a generic or empty category
    if not foldername or foldername.lower() in ('untitled', 'unknown', ''):
        # Attempt to extract a keyword from the summary
        from nltk.tokenize import word_tokenize
        from nltk.corpus import stopwords
        from nltk.probability import FreqDist

        words = word_tokenize(description.lower())
        words = [word for word in words if word.isalpha()]
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word not in stop_words]
        fdist = FreqDist(filtered_words)
        most_common = fdist.most_common(1)
        if most_common:
            foldername = most_common[0][0]
        else:
            foldername = 'documents'

    sanitized_foldername = sanitize_filename(foldername)

    if not sanitized_foldername:
        sanitized_foldername = 'documents'

    return sanitized_foldername, sanitized_filename, description

def process_single_text_file(args):
    """Process a single text file to generate metadata."""
    file_path, text = args
    foldername, filename, description = generate_text_metadata(text, file_path)
    print(f"File: {file_path}")
    print(f"Description: {description}")
    print(f"Folder name: {foldername}")
    print(f"Generated filename: {filename}")
    print("-" * 50)
    return {
        'file_path': file_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
    }

def process_text_files(text_tuples):
    """Process text files sequentially."""
    results = []
    for args in text_tuples:
        data = process_single_text_file(args)
        results.append(data)
    return results

def copy_and_rename_files(data_list, new_path, renamed_files, processed_files, use_hard_links=False, dry_run=False):
    """Copy and rename files based on generated metadata."""
    operations = []
    for data in data_list:
        file_path = data['file_path']
        if file_path in processed_files:
            continue
        processed_files.add(file_path)

        # Prepare folder name and file name
        folder_name = data['foldername']
        new_file_name = data['filename'] + os.path.splitext(file_path)[1]

        # Prepare new file path
        dir_path = os.path.join(new_path, folder_name)
        new_file_path = os.path.join(dir_path, new_file_name)

        # Handle duplicates
        counter = 1
        original_new_file_name = new_file_name
        while new_file_path in renamed_files or (not dry_run and os.path.exists(new_file_path)):
            new_file_name = f"{data['filename']}_{counter}" + os.path.splitext(file_path)[1]
            new_file_path = os.path.join(dir_path, new_file_name)
            counter += 1

        # Record the operation
        operation = {
            'source': file_path,
            'destination': new_file_path,
            'action': 'copy' if not use_hard_links else 'hardlink'
        }
        operations.append(operation)

        if not dry_run:
            # Create directory
            dir_path = create_folder(new_path, folder_name)
            new_file_path = os.path.join(dir_path, new_file_name)
            # Perform the file operation
            try:
                if use_hard_links:
                    os.link(file_path, new_file_path)
                else:
                    shutil.copy2(file_path, new_file_path)
                renamed_files.add(new_file_path)
                print(f"{operation['action'].capitalize()}d to: {new_file_path}")
            except Exception as e:
                print(f"Error {operation['action']}ing file '{file_path}' to '{new_file_path}': {e}")
            print("-" * 50)

    return operations  # Return the list of operations for display or further processing

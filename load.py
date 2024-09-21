import os
import re
import time
import shutil
import subprocess
from multiprocessing import Pool, cpu_count

from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import docx

from nexa.gguf import NexaVLMInference, NexaTextInference

# Initialize the models
model_path = "llava-v1.6-vicuna-7b:q4_0"
model_path_text = "gemma-2b:q2_K"

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

def sanitize_filename(name, max_length=50, max_words=5):
    """Sanitize the filename by removing unwanted words and characters."""
    # Remove file extension if present
    name = os.path.splitext(name)[0]
    # Remove unwanted words and data type words
    name = re.sub(
        r'\b(jpg|jpeg|png|gif|bmp|txt|pdf|docx|image|picture|photo|this|that|these|those|here|there|'
        r'please|note|additional|notes|folder|name|sure|heres|a|an|the|and|of|in|'
        r'to|for|on|with|your|answer|should|be|only|summary|summarize|text|category)\b',
        '',
        name,
        flags=re.IGNORECASE
    )
    # Remove non-word characters except underscores
    sanitized = re.sub(r'[^\w\s]', '', name).strip()
    # Replace multiple underscores or spaces with a single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)
    # Convert to lowercase
    sanitized = sanitized.lower()
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    # Split into words and limit the number of words
    words = sanitized.split('_')
    limited_words = [word for word in words if word]  # Remove empty strings
    limited_words = limited_words[:max_words]
    limited_name = '_'.join(limited_words)
    # Limit length
    return limited_name[:max_length] if limited_name else 'untitled'

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

def read_docx_file(file_path):
    """Read text content from a .docx file."""
    doc = docx.Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return '\n'.join(full_text)

def read_pdf_file(file_path):
    """Read text content from a PDF file."""
    try:
        doc = fitz.open(file_path)
        # Read only the first few pages to speed up processing
        num_pages_to_read = 3  # Adjust as needed
        full_text = []
        for page_num in range(min(num_pages_to_read, len(doc))):
            page = doc.load_page(page_num)
            full_text.append(page.get_text())
        pdf_content = '\n'.join(full_text)
        return pdf_content
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
        return ""

def read_image_file(file_path):
    """Extract text from an image file using OCR."""
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error reading image file {file_path}: {e}")
        return ""

def read_text_file(file_path):
    """Read text content from a text file."""
    # Read only the first N characters to limit processing time
    max_chars = 3000  # Adjust as needed
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read(max_chars)
    return text

def display_directory_tree(path):
    """Display the directory tree using the 'tree' command."""
    result = subprocess.run(['tree', path], capture_output=True, text=True)
    print(result.stdout)

def generate_image_metadata(image_path):
    """Generate description, folder name, and filename for an image file."""
    # Generate description
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description_generator = image_inference._chat(description_prompt, image_path)
    description = get_text_from_generator(description_generator).strip()

    # Generate filename
    filename_prompt = f"""Based on the description below, generate a specific and descriptive filename (2-4 words) for the image.
Do not include any data type words like 'image', 'jpg', 'png', etc. Use only letters and connect words with underscores.

Description: {description}

Example:
Description: A photo of a sunset over the mountains.
Filename: sunset_over_mountains

Now generate the filename.

Filename:"""
    filename_response = text_inference.create_completion(filename_prompt)
    filename_text = filename_response['choices'][0]['text'].strip()
    filename = filename_text.replace('Filename:', '').strip()
    sanitized_filename = sanitize_filename(filename)

    # Check if sanitized filename is empty, provide default
    if not sanitized_filename:
        sanitized_filename = 'untitled_image'

    # Generate folder name from description (broader category)
    foldername_prompt = f"""Based on the description below, generate a general category or theme (1-2 words) for this image.
This will be used as the folder name. Do not include specific details or words from the filename.

Description: {description}

Example:
Description: A photo of a sunset over the mountains.
Category: landscapes

Now generate the category.

Category:"""
    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername_text = foldername_response['choices'][0]['text'].strip()
    foldername = foldername_text.replace('Category:', '').strip()
    sanitized_foldername = sanitize_filename(foldername)

    # Check if sanitized folder name is empty, provide default
    if not sanitized_foldername:
        sanitized_foldername = 'images'

    return sanitized_foldername, sanitized_filename, description

def process_image_files(image_paths):
    """Process a list of image files to generate metadata."""
    data_list = []
    for image_path in image_paths:
        foldername, filename, description = generate_image_metadata(image_path)
        print(f"File: {image_path}")
        print(f"Description: {description}")
        print(f"Folder name: {foldername}")
        print(f"Generated filename: {filename}")
        print("-" * 50)
        data_list.append({
            'file_path': image_path,
            'foldername': foldername,
            'filename': filename,
            'description': description
        })
    return data_list

def summarize_text_content(text):
    """Summarize the given text content."""
    prompt = f"""Provide a concise and accurate summary of the following text, focusing on the main ideas and key details.
Limit your summary to a maximum of 150 words.

Text: {text}

Summary:"""

    response = text_inference.create_completion(prompt)
    summary = response['choices'][0]['text'].strip()
    return summary

def generate_text_metadata(input_text):
    """Generate description, folder name, and filename for a text document."""
    # Generate description
    description = summarize_text_content(input_text)

    # Generate filename
    filename_prompt = f"""Based on the summary below, generate a specific and descriptive filename (2-4 words) for the document.
Do not include any data type words like 'text', 'document', 'pdf', etc. Use only letters and connect words with underscores.

Summary: {description}

Example:
Summary: A research paper on the fundamentals of string theory.
Filename: string_theory_fundamentals

Now generate the filename.

Filename:"""
    filename_response = text_inference.create_completion(filename_prompt)
    filename_text = filename_response['choices'][0]['text'].strip()
    filename = filename_text.replace('Filename:', '').strip()
    sanitized_filename = sanitize_filename(filename)

    # Check if sanitized filename is empty, provide default
    if not sanitized_filename:
        sanitized_filename = 'untitled_document'

    # Generate folder name from summary (broader category)
    foldername_prompt = f"""Based on the summary below, generate a general category or theme (1-2 words) for this document.
This will be used as the folder name. Do not include specific details or words from the filename.

Summary: {description}

Example:
Summary: A research paper on the fundamentals of string theory.
Category: physics

Now generate the category.

Category:"""
    foldername_response = text_inference.create_completion(foldername_prompt)
    foldername_text = foldername_response['choices'][0]['text'].strip()
    foldername = foldername_text.replace('Category:', '').strip()
    sanitized_foldername = sanitize_filename(foldername)

    # Check if sanitized folder name is empty, provide default
    if not sanitized_foldername:
        sanitized_foldername = 'documents'

    return sanitized_foldername, sanitized_filename, description

def process_text_files(text_tuples):
    """Process a list of text files to generate metadata."""
    results = []
    for file_path, text in text_tuples:
        foldername, filename, description = generate_text_metadata(text)
        print(f"File: {file_path}")
        print(f"Description: {description}")
        print(f"Folder name: {foldername}")
        print(f"Generated filename: {filename}")
        print("-" * 50)
        results.append({
            'file_path': file_path,
            'foldername': foldername,
            'filename': filename,
            'description': description
        })
    return results

def create_folder(base_path, foldername):
    """Create a directory for the given folder name."""
    sanitized_folder_name = sanitize_filename(foldername)
    dir_path = os.path.join(base_path, sanitized_folder_name)
    os.makedirs(dir_path, exist_ok=True)
    return dir_path

def collect_file_paths(base_path):
    """Collect all file paths from the base directory."""
    file_paths = [
        os.path.join(root, file)
        for root, _, files in os.walk(base_path)
        for file in files
    ]
    return file_paths

def separate_files_by_type(file_paths):
    """Separate files into images, text files, and PDF files based on their extensions."""
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
    text_extensions = ('.txt', '.docx')
    pdf_extension = '.pdf'

    image_files = [fp for fp in file_paths if os.path.splitext(fp.lower())[1] in image_extensions]
    text_files = [fp for fp in file_paths if os.path.splitext(fp.lower())[1] in text_extensions]
    pdf_files = [fp for fp in file_paths if os.path.splitext(fp.lower())[1] == pdf_extension]

    return image_files, text_files, pdf_files

def copy_and_rename_files(data_list, new_path, renamed_files, processed_files):
    """Copy and rename files based on generated metadata."""
    for data in data_list:
        file_path = data['file_path']
        if file_path in processed_files:
            continue
        processed_files.add(file_path)

        # Use AI-generated folder name
        dir_path = create_folder(new_path, data['foldername'])

        # Use AI-generated filename
        new_file_name = data['filename'] + os.path.splitext(file_path)[1]
        new_file_path = os.path.join(dir_path, new_file_name)

        # Handle duplicates
        counter = 1
        while new_file_path in renamed_files or os.path.exists(new_file_path):
            new_file_name = f"{data['filename']}_{counter}" + os.path.splitext(file_path)[1]
            new_file_path = os.path.join(dir_path, new_file_name)
            counter += 1

        shutil.copy2(file_path, new_file_path)
        renamed_files.add(new_file_path)
        print(f"Copied and renamed to: {new_file_path}")
        print("-" * 50)

def main():
    # Paths configuration
    base_path = "/Users/q/nexa/nexa_sdk_local_file_organization/nexa-sdk/examples/local_file_organization/yanhao ver/sample_data"
    new_path = "/Users/q/nexa/nexa_sdk_local_file_organization/nexa-sdk/examples/local_file_organization/yanhao ver/renamed_files"

    if not os.path.exists(base_path):
        print(f"Directory {base_path} does not exist. Please create it and add the necessary files.")
        return

    start_time = time.time()
    file_paths = collect_file_paths(base_path)
    end_time = time.time()

    print(f"Time taken to load file paths: {end_time - start_time:.2f} seconds")
    print("-" * 50)
    print("Directory tree before renaming:")
    display_directory_tree(base_path)

    # Separate files by type
    image_files, text_files, pdf_files = separate_files_by_type(file_paths)

    # Process image files
    data_images = process_image_files(image_files)

    # Process text files
    text_tuples = [(fp, read_text_file(fp)) for fp in text_files]
    data_texts = process_text_files(text_tuples)

    # Process PDF files
    pdf_tuples = [(fp, read_pdf_file(fp)) for fp in pdf_files]
    data_pdfs = process_text_files(pdf_tuples)

    # Combine text and PDF data
    data_texts.extend(data_pdfs)

    # Prepare for copying and renaming
    renamed_files = set()
    processed_files = set()
    os.makedirs(new_path, exist_ok=True)

    # Copy and rename image files
    copy_and_rename_files(data_images, new_path, renamed_files, processed_files)

    # Copy and rename text and PDF files
    copy_and_rename_files(data_texts, new_path, renamed_files, processed_files)

    print("Directory tree after copying and renaming:")
    display_directory_tree(new_path)

if __name__ == '__main__':
    main()

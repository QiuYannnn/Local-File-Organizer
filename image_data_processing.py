import re
import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename  # Import sanitize_filename

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

def process_single_image(image_path, image_inference, text_inference, silent=False, log_file=None):
    """Process a single image file to generate metadata."""
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(image_path)}", total=1.0)
        foldername, filename, description = generate_image_metadata(image_path, progress, task_id, image_inference, text_inference)
    
    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {image_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {description}\nFolder name: {foldername}\nGenerated filename: {filename}\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': image_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
    }

def process_image_files(image_paths, image_inference, text_inference, silent=False, log_file=None):
    """Process image files sequentially."""
    data_list = []
    for image_path in image_paths:
        data = process_single_image(image_path, image_inference, text_inference, silent=silent, log_file=log_file)
        data_list.append(data)
    return data_list

def generate_image_metadata(image_path, progress, task_id, image_inference, text_inference):
    """Generate description, folder name, and filename for an image file."""

    # Total steps in processing an image
    total_steps = 3

    # Step 1: Generate description using image_inference
    description_prompt = "Please provide a detailed description of this image, focusing on the main subject and any important details."
    description_generator = image_inference._chat(description_prompt, image_path)
    description = get_text_from_generator(description_generator).strip()
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Generate filename using text_inference
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
    progress.update(task_id, advance=1 / total_steps)

    # Step 3: Generate folder name from description using text_inference
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
    progress.update(task_id, advance=1 / total_steps)

    # Remove markdown, code blocks, and special characters from filename and foldername
    filename = re.sub(r'[\*\`\n]', '', filename).strip()
    foldername = re.sub(r'[\*\`\n]', '', foldername).strip()

    # Check if the AI returned a generic or empty filename
    if not filename or filename.lower() in ('untitled', 'unknown', '', 'describes'):
        # Use the first few words of the description as the filename
        filename = '_'.join(description.split()[:3])

    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename or sanitized_filename.lower() in ('untitled', ''):
        sanitized_filename = 'image_' + os.path.splitext(os.path.basename(image_path))[0]

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
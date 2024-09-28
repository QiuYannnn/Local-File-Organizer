import re
import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
from data_processing_common import sanitize_filename

def summarize_text_content(text, text_inference):
    """Summarize the given text content."""
    prompt = f"""Provide a concise and accurate summary of the following text, focusing on the main ideas and key details.
Limit your summary to a maximum of 150 words.

Text: {text}

Summary:"""

    response = text_inference.create_completion(prompt)
    summary = response['choices'][0]['text'].strip()
    return summary

def process_single_text_file(args, text_inference, silent=False, log_file=None):
    """Process a single text file to generate metadata."""
    file_path, text = args
    start_time = time.time()

    # Create a Progress instance for this file
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn()
    ) as progress:
        task_id = progress.add_task(f"Processing {os.path.basename(file_path)}", total=1.0)
        foldername, filename, description = generate_text_metadata(text, file_path, progress, task_id, text_inference)

    end_time = time.time()
    time_taken = end_time - start_time

    message = f"File: {file_path}\nTime taken: {time_taken:.2f} seconds\nDescription: {description}\nFolder name: {foldername}\nGenerated filename: {filename}\n"
    if silent:
        if log_file:
            with open(log_file, 'a') as f:
                f.write(message + '\n')
    else:
        print(message)
    return {
        'file_path': file_path,
        'foldername': foldername,
        'filename': filename,
        'description': description
    }

def process_text_files(text_tuples, text_inference, silent=False, log_file=None):
    """Process text files sequentially."""
    results = []
    for args in text_tuples:
        data = process_single_text_file(args, text_inference, silent=silent, log_file=log_file)
        results.append(data)
    return results

def generate_text_metadata(input_text, file_path, progress, task_id, text_inference):
    """Generate description, folder name, and filename for a text document."""

    # Total steps in processing a text file
    total_steps = 3

    # Step 1: Generate description
    description = summarize_text_content(input_text, text_inference)
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Generate filename
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
    progress.update(task_id, advance=1 / total_steps)

    # Check if the AI returned a generic or empty filename
    if not filename or filename.lower() in ('untitled', 'unknown', '', 'describes'):
        # Use the first few words of the summary as the filename
        filename = '_'.join(description.split()[:3])

    sanitized_filename = sanitize_filename(filename)

    if not sanitized_filename or sanitized_filename.lower() in ('untitled', ''):
        sanitized_filename = 'document_' + os.path.splitext(os.path.basename(file_path))[0]

    # Step 3: Generate folder name from summary
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
    progress.update(task_id, advance=1 / total_steps)

    # Check if the AI returned a generic or empty category
    if not foldername or foldername.lower() in ('untitled', 'unknown', ''):

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

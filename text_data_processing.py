def generate_text_metadata(input_text, file_path, progress, task_id, text_inference):
    """Generate description, folder name, and filename for a text document."""
    max_token_limit = 2048  # Adjust based on model's limit

    # Total steps in processing a text file
    total_steps = 3

    # Step 1: Generate description
    description = summarize_text_content(input_text, text_inference)
    progress.update(task_id, advance=1 / total_steps)

    # Step 2: Generate filename
    filename_prompt =  f"""Based on the summary below, generate a specific and descriptive filename that captures the essence of the document.
Limit the filename to a maximum of 3 words. Use nouns and avoid starting with verbs like 'depicts', 'shows', 'presents', etc.
Do not include any data type words like 'text', 'document', 'pdf', etc. Use only letters and connect words with underscores.

Summary: {description}

Examples:
1. Summary: A research paper on the fundamentals of string theory.
   Filename: fundamentals_of_string_theory

2. Summary: An article discussing the effects of climate change on polar bears.
   Filename: climate_change_polar_bears

Now generate the filename.

Output only the filename, without any additional text.

Filename:"""

    # Token limit check (Optional: If you have a tokenizer for exact token count)
    # input_tokens = len(text_inference.tokenizer.encode(filename_prompt))
    # if input_tokens >= max_token_limit:
    #    filename_prompt = filename_prompt[:max_token_limit - 1]

    # Simple character count-based truncation (if tokenizer is not available)
    if len(filename_prompt) > max_token_limit:
        filename_prompt = filename_prompt[:max_token_limit - 1]

    filename_response = text_inference.create_completion(filename_prompt)
    filename = filename_response['choices'][0]['text'].strip()
    # Remove 'Filename:' prefix if present
    filename = re.sub(r'^Filename:\s*', '', filename, flags=re.IGNORECASE).strip()
    progress.update(task_id, advance=1 / total_steps)

    # Step 3: Generate folder name from summary
    foldername_prompt = f"""Based on the summary below, generate a general category or theme that best represents the main subject of this document.
This will be used as the folder name. Limit the category to a maximum of 2 words. Use nouns and avoid verbs.

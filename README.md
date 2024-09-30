# Local File Organizer: AI File Management Run Entirely on Your Device, Privacy Assured

Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - all while respecting your privacy.

## A Glimpse of How It Works


# Local File Organizer: AI File Management Run Entirely on Your Device, Privacy Assured
Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - all while respecting your privacy.
## How It Works 💡

```
--------------------------------------------------
**NOTE: Silent mode suppresses output messages and logs them to a file instead.
Would you like to enable silent mode? (yes/no): no
--------------------------------------------------
Enter the path of the directory you want to organize: /home/user/documents/mass_folder
Input path successfully uploaded: /home/user/documents/mass_folder
--------------------------------------------------
Enter the path to store organized files and folders (press Enter to use 'organized_folder' in the input directory)
Output path successfully upload: /home/user/documents/organzied_folder
--------------------------------------------------
Time taken to load file paths: 0.00 seconds
--------------------------------------------------
Directory tree before renaming:
Path/to/your/input/files/or/folder
├── image.jpg
├── document.pdf
├── notes.txt
└── sub_directory
    └── picture.png

1 directory, 4 files
**************************************************
Please choose the mode to organize your files:
1. By Content
2. By Date
3. By Type
Checking if the model is already downloaded. If not, downloading it now.
**----------------------------------------------**
**       Image inference model initialized      **
**       Text inference model initialized       **
**----------------------------------------------**
**************************************************
The files have been uploaded successfully. Processing will take a few minutes.
**************************************************
Processing image1.jpg ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:30
File: Path/to/your/input/files/or/folder/image1.jpg
Description: [Generated description]
Folder name: [Generated folder name]
Generated filename: [Generated filename]
--------------------------------------------------
Processing document.pdf ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0:00:30
File: Path/to/your/input/files/or/folder/document.pdf
Description: [Generated description]
Folder name: [Generated folder name]
Generated filename: [Generated filename]
--------------------------------------------------
... [Additional files processed]
Directory tree after copying and renaming:
Path/to/your/output/files/or/folder
├── category1
│   └── generated_filename.jpg
├── category2
│   └── generated_filename.pdf
└── category3
    └── generated_filename.png

3 directories, 3 files

Would you like to proceed with these changes? (yes/no): no
Would you like to choose another sorting method? (yes/no): no
Would you like to organize a new directory? (yes/no): no
Operation canceled by the user.
```

## Updates 🚀
**[2024/09] v0.0.2**:
* Featured by [Nexa Gallery](https://nexaai.com/gallery) and [Nexa SDK Cookbook](https://github.com/NexaAI/nexa-sdk/tree/main/examples)!
* Dry Run Mode: check sorting results before committing changes
* Silent Mode: save all logs to a txt file for quieter operation
* Added file support:  `.md`, .`excel`, `.ppt`, and `.csv` 
* Three sorting options: by content, by date, and by type
* The default text model is now [Llama3.2 3B](https://nexaai.com/meta/Llama3.2-1B-Instruct/gguf-q4_K_M/file)
* Improved CLI interaction experience
* Added real-time progress bar for file analysis
Please update the project by deleting the original project folder and reinstalling the requirements. Refer to the installation guide from Step 4.
## Roadmap 📅
- [ ] Copilot Mode: chat with AI to tell AI how you want to sort the file (ie. read and rename all the PDFs)
- [ ] Change models with CLI 
- [ ] ebook format support
- [ ] audio file support
- [ ] video file support
- [ ] Implement best practices like Johnny Decimal
- [ ] Check file duplication
- [ ] Dockerfile for easier installation
- [ ] People from [Nexa](https://github.com/NexaAI/nexa-sdk) is helping me to make executables for macOS, Linux and Windows
## What It Does 🔍
This intelligent file organizer harnesses the power of advanced AI models, including language models (LMs) and vision-language models (VLMs), to automate the process of organizing files by:
* Scanning a specified input directory for files.
* Content Understanding: 
  - **Textual Analysis**: Uses the [Llama3.2 3B](https://nexaai.com/meta/Llama3.2-1B-Instruct/gguf-q4_K_M/file) to analyze and summarize text-based content, generating relevant descriptions and filenames.
  - **Visual Content Analysis**: Uses the [LLaVA-v1.6](https://nexaai.com/liuhaotian/llava-v1.6-vicuna-7b/gguf-q4_0/file) , based on Vicuna-7B, to interpret visual files such as images, providing context-aware categorization and descriptions.
* Understanding the content of your files (text, images, and more) to generate relevant descriptions, folder names, and filenames.
* Organizing the files into a new directory structure based on the generated metadata.
The best part? All AI processing happens 100% on your local device using the [Nexa SDK](https://github.com/NexaAI/nexa-sdk). No internet connection required, no data leaves your computer, and no AI API is needed - keeping your files completely private and secure.
## Supported File Types 📁
- **Images:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`
- **Text Files:** `.txt`, `.docx`, `.md`
- **Spreadsheets:** `.xlsx`, `.csv`
- **Presentations:** `.ppt`, `.pptx`
- **PDFs:** `.pdf`
## Prerequisites 💻
- **Operating System:** Compatible with Windows, macOS, and Linux.
- **Python Version:** Python 3.12
- **Conda:** Anaconda or Miniconda installed.
- **Git:** For cloning the repository (or you can download the code as a ZIP file).
## Installation 🛠
> For SDK installation and model-related issues, please post on [here](https://github.com/NexaAI/nexa-sdk/issues).
### 1. Install Python
Before installing the Local File Organizer, make sure you have Python installed on your system. We recommend using Python 3.12 or later.
You can download Python from [the official website]((https://www.python.org/downloads/)).
Follow the installation instructions for your operating system.
### 2. Clone the Repository
Clone this repository to your local machine using Git:
```zsh
git clone https://github.com/QiuYannnn/Local-File-Organizer.git
```
Or download the repository as a ZIP file and extract it to your desired location.
### 3. Set Up the Python Environment
Create a new Conda environment named `local_file_organizer` with Python 3.12:
```zsh
conda create --name local_file_organizer python=3.12
```
Activate the environment:
```zsh
conda activate local_file_organizer
```
### 4. Install Nexa SDK ️
#### CPU Installation
To install the CPU version of Nexa SDK, run:
```bash
pip install nexaai --prefer-binary --index-url https://nexaai.github.io/nexa-sdk/whl/cpu --extra-index-url https://pypi.org/simple --no-cache-dir
```
#### GPU Installation (Metal - macOS)
For the GPU version supporting Metal (macOS), run:
```bash
CMAKE_ARGS="-DGGML_METAL=ON -DSD_METAL=ON" pip install nexaai --prefer-binary --index-url https://nexaai.github.io/nexa-sdk/whl/metal --extra-index-url https://pypi.org/simple --no-cache-dir
```
For detailed installation instructions of Nexa SDK for **CUDA** and **AMD GPU** support, please refer to the [Installation section](https://github.com/NexaAI/nexa-sdk?tab=readme-ov-file#installation) in the main README.
### 5. Install Dependencies 
1. Ensure you are in the project directory:
   ```zsh
   cd path/to/Local-File-Organizer
   ```
   Replace `path/to/Local-File-Organizer` with the actual path where you cloned or extracted the project.
2. Install the required dependencies:
   ```zsh
   pip install -r requirements.txt
   ```
**Note:** If you encounter issues with any packages, install them individually:
```zsh
pip install nexa Pillow pytesseract PyMuPDF python-docx
```
With the environment activated and dependencies installed, run the script using:
### 6. Running the Script🎉
```zsh
python main.py
```
## Notes
- **SDK Models:**
  - The script uses `NexaVLMInference` and `NexaTextInference` models [usage](https://docs.nexaai.com/sdk/python-interface/gguf).
  - Ensure you have access to these models and they are correctly set up.
  - You may need to download model files or configure paths.
- **Dependencies:**
  - **pytesseract:** Requires Tesseract OCR installed on your system.
    - **macOS:** `brew install tesseract`
    - **Ubuntu/Linux:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download from [Tesseract OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - **PyMuPDF (fitz):** Used for reading PDFs.
- **Processing Time:**
  - Processing may take time depending on the number and size of files.
  - The script uses multiprocessing to improve performance.
- **Customizing Prompts:**
  - You can adjust prompts in `data_processing.py` to change how metadata is generated.
## License
This project is licensed under the MIT License.
- See the [MIT License](LICENSE-MIT) for more details.
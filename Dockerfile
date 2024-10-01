# Use the NVIDIA CUDA base image
FROM nvidia/cuda:12.2.0-devel-ubuntu20.04

# Set environment variables to avoid interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Add PPA for Python 3.12 and install dependencies
RUN apt-get update && apt-get install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    curl \
    build-essential \
    cmake \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 \
    && update-alternatives --install /usr/bin/pip3 pip3 /usr/local/bin/pip3 1

# Set the working directory
WORKDIR /app

# Copy the project files into the container's /app directory
COPY . /app

# Install Python dependencies from requirements.txt in one step
RUN pip3 install --no-cache-dir -r /app/requirements.txt \
    && CMAKE_ARGS="-DGGML_CUDA=ON -DSD_CUBLAS=ON" pip3 install nexaai --prefer-binary --index-url https://nexaai.github.io/nexa-sdk/whl/cu124 --extra-index-url https://pypi.org/simple --no-cache-dir

# Set the default command to run the main.py script
CMD ["python3", "main.py"]

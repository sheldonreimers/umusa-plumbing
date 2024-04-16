FROM python:3.9

# Set the working directory
WORKDIR /workspace

# Copy the requirements file into the container
COPY config/requirements.txt .

# Install common packages
RUN pip install -r requirements.txt

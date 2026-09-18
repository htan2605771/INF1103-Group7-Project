# Use a slim official Python base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy dependency list first (better layer caching — only re-installs
# packages if requirements.txt actually changes)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files (main.py, io_manager.py, ai_manager.py,
# logic_manager.py, data_manager.py, and any data files)
COPY . .

# Run the application
CMD ["python", "main.py"]
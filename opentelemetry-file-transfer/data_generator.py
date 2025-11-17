import os
import random

def generate_random_file(file_path, size):
    """Generates a file with random binary data."""
    with open(file_path, 'wb') as f:
        f.write(os.urandom(size))

def create_client_files_directory():
    """Ensures the client_files directory exists."""
    directory = './client_files'
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def populate_client_files(directory):
    """Generates a guaranteed mix of small, medium, and large files."""
    # Clear existing files to ensure a fresh start
    for f in os.listdir(directory):
        os.remove(os.path.join(directory, f))

    # Define size ranges in bytes
    KB = 1024
    MB = 1024 * KB
    
    # We are creaing 20 files in total: 8 small, 8 medium, 4 large
    file_definitions = [
        # 8 small files (5KB - 1MB)
        *[(f'small_file_{i+1}.bin', random.randint(5 * KB, 1 * MB)) for i in range(8)],
        # 8 medium files (1MB - 25MB)
        *[(f'medium_file_{i+1}.bin', random.randint(1 * MB, 25 * MB)) for i in range(8)],
        # 4 large files (25MB - 100MB)
        *[(f'large_file_{i+1}.bin', random.randint(25 * MB, 100 * MB)) for i in range(4)]
    ]

    for file_name, file_size in file_definitions:
        file_path = os.path.join(directory, file_name)
        generate_random_file(file_path, file_size)
        print(f"Created {file_path} ({file_size / KB:.2f} KB)")


if __name__ == '__main__':
    client_files_directory = create_client_files_directory()
    populate_client_files(client_files_directory)
    print(f'\nFinished populating {client_files_directory} with 20 mixed-size binary files.')
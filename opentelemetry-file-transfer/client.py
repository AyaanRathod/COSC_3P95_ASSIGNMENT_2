import os
import requests
import hashlib
import gzip
import time
import logging
from opentelemetry import trace, metrics

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- OpenTelemetry Manual Instrumentation Setup ---
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom Metric: A histogram for file transfer duration
file_transfer_duration = meter.create_histogram(
    "file.transfer.duration",
    description="Duration of file transfer in seconds",
    unit="s"
)

# --- Main Client Logic ---
def stream_and_compress_file(file_path, chunk_size=4096):
    """
    A generator that reads a file, compresses it, and yields the compressed content.
    This is memory-efficient for large files.
    """
    with open(file_path, 'rb') as f:
        # Read the entire file content
        content = f.read()
        # Compress the content in one go
        compressed_content = gzip.compress(content)
        # Yield the compresed content as a single chunk
        yield compressed_content


def run_client():
   # """Scans for fles and sends them to the server."""
    client_files_dir = './client_files'
    server_url = 'http://127.0.0.1:8080/upload'
    
    if not os.path.isdir(client_files_dir):
        log.error(f"Client files directory not found: {client_files_dir}")
        log.error("Please run data_generator.py first.")
        return

    log.info("Starting file transfer...")
    files_to_send = sorted(os.listdir(client_files_dir))

    for filename in files_to_send:
        file_path = os.path.join(client_files_dir, filename)
        
        # Custom Span 1: Wraps reading, hashing, and preparing the file
        with tracer.start_as_current_span("file-read-and-prepare") as prep_span:
            prep_span.set_attribute("file.name", filename)
            
            try:
                # Calclate checksum (Data Integrity)
                hasher = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        hasher.update(chunk)
                checksum = hasher.hexdigest()
                
                prep_span.add_event("checksum.calculated", {"checksum": checksum})

                headers = {
                    'X-Filename': filename,
                    'X-File-Checksum': checksum,
                    'Content-Encoding': 'gzip'
                }

                # Custom Span 2: Wraps the actual file transfer
                with tracer.start_as_current_span("file-transfer") as transfer_span:
                    start_time = time.time()
                    
                    compressed_data_stream = stream_and_compress_file(file_path)

                    response = requests.post(
                        server_url,
                        data=compressed_data_stream,
                        headers=headers,
                        stream=True
                    )
                    
                    duration = time.time() - start_time
                    file_transfer_duration.record(duration, {"file.name": filename})

                    if response.ok:
                        log.info(f"Successfully uploaded {filename}")
                    else:
                        log.error(f"Failed to upload {filename}: {response.status_code} - {response.text}")

            except Exception as e:
                log.error(f"An error occurred with file {filename}: {e}")
                if 'prep_span' in locals() and prep_span.is_recording():
                    prep_span.record_exception(e)
                    prep_span.set_status(trace.Status(trace.StatusCode.ERROR))
                if 'transfer_span' in locals() and transfer_span.is_recording():
                    transfer_span.record_exception(e)
                    transfer_span.set_status(trace.Status(trace.StatusCode.ERROR))

    log.info("File transfer complete.")

if __name__ == '__main__':
    run_client()
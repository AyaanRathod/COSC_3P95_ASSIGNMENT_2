import os
import hashlib
import gzip
import logging
from flask import Flask, request
from opentelemetry import trace, metrics

# --- Basic Configuration ---
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# The directory where uploaded files will be saved
output_dir = "./server_output"
os.makedirs(output_dir, exist_ok=True)


# --- OpenTelemetry Manual Instrentation Setup ---
tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

# Custom Metric 1: A counter for the number of files successfully processed
files_processed = meter.create_counter(
    "files.processed",
    description="The number of files processed by the server"
)


# --- Flask App ---
app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload():
    """Receives a file, saves it, and verifies its checksum."""
    with tracer.start_as_current_span("file-save-and-verify") as span:
        try:
            # Get filename and checksum from headers
            filename = request.headers.get('X-Filename')
            if not filename:
                log.error("Filename header 'X-Filename' not found.")
                return "Filename header missing", 400
                
            client_checksum = request.headers.get('X-File-Checksum', '')
            output_path = os.path.join(output_dir, filename)

            span.set_attribute("file.name", filename)
            log.info(f"Receiving file: {filename}")

            # Stream the request body directly to a file, decompressing on the fly.
            hasher = hashlib.sha256()
            with open(output_path, 'wb') as f:
                with gzip.GzipFile(fileobj=request.stream, mode='rb') as gz:
                    while True:
                        chunk = gz.read(4096)
                        if not chunk:
                            break
                        hasher.update(chunk)
                        f.write(chunk)

            span.add_event("file.write.complete", {"path": output_path})
            log.info(f"Finished writing file: {output_path}")

            # Verify checksum for data integrity
            server_checksum = hasher.hexdigest()
            checksum_match = (server_checksum == client_checksum)
            span.set_attribute("file.checksum.match", checksum_match)

            if checksum_match:
                log.info(f"Checksum verified for {filename}")
                files_processed.add(1, {"file.name": filename})
                return "File uploaded and verified successfully.", 200
            else:
                log.error(f"Checksum mismatch for {filename}")
                return "File corrupted during transfer.", 400

        except Exception as e:
            log.error(f"An error occurred: {e}")
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, "An error occurred during file upload"))
            return "Internal Server Error", 500

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
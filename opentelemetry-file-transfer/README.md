# OpenTelemetry File Transfer Project

This project demonstrates a client-server file transfer application instrumented with OpenTelemetry for comprehensive observability, fulfilling the requirements of the COSC 3P95 assignment.

## Project Structure

-   `client.py`: Sends files from the `./client_files` directory to the server.
-   `server.py`: A Flask server that receives files and saves them to `./server_output`.
-   `data_generator.py`: A script to create the test files.
-   `requirements.txt`: Python dependencies.
-   `docker-compose.yml`: Starts the observability backend (Collector and jaeger)
-   `otel-collector-config.yml`: Configures the OpenTelemetry Collector.
-   `report.md`: A template for the final project report.
-   `screenshots/`: A directory to save your Jaeger and Grafana screenshots.

## Final Setup and Execution Instructions

Follow these steps precisely in order to run the application and collect telemetry data.

### Step 1: Initial Setup

1.  **Install Dependencies**: If you haven't already, create a virtual environment and install the required Python packages.
    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    ```

2.  **Generate Test Files**: Run the data generator script once to create the test files.
    ```powershell
    python data_generator.py
    ```

3.  **Start the Observability Stack**: Use Docker Compose to run the OTel Collector and jaeger.
    ```powershell
    docker-compose up -d
    ```
    You can check that they are running with `docker ps`.

### Step 2: Run the Application (AlwaysOn Sampler)

This is the default mode, which captures 100% of traces. You will need **two separate terminals**, both with the virtual environment activated (`.\venv\Scripts\Activate.ps1`).

1.  **In Terminal 1 (Start the Server)**:
    ```powershell
    # Set environment variables for the server
    $env:OTEL_SERVICE_NAME="server-app"
    $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
    $env:OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"

    # Run the server with auto-instrumentation
    opentelemetry-instrument waitress-serve --host 127.0.0.1 --port 8080 server:app
    ```

2.  **In Terminal 2 (Run the Client)**:
    ```powershell
    # Set environment variables for the client
    $env:OTEL_SERVICE_NAME="client-app"
    $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
    $env:OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"

    # Run the client with auto-instrumentation
    opentelemetry-instrument python client.py
    ```

### Step 3: Run the Application (Probability Sampler)

To evaluate the second sampling strategy, stop the server (`Ctrl+C`) and run the application again using the following commands. This will configure the application to sample approximately 30% of traces.

1.  **In Terminal 1 (Start the Server with Sampling)**:
    ```powershell
    # Set environment variables for the server with SAMPLING
    $env:OTEL_SERVICE_NAME="server-app"
    $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
    $env:OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
    $env:OTEL_TRACES_SAMPLER="traceidratio"
    $env:OTEL_TRACES_SAMPLER_ARG="0.3"

    # Run the server
    opentelemetry-instrument waitress-serve --host 127.0.0.1 --port 8080 server:app
    ```

2.  **In Terminal 2 (Run the Client with Sampling)**:
    ```powershell
    # Set environment variables for the client with SAMPLING
    $env:OTEL_SERVICE_NAME="client-app"
    $env:OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
    $env:OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
    $env:OTEL_TRACES_SAMPLER="traceidratio"
    $env:OTEL_TRACES_SAMPLER_ARG="0.3"

    # Run the client
    opentelemetry-instrument python client.py
    ```

### Step 4: View the Results

-   **Jaeger Traces**: Open your web browser to `http://localhost:16686`
-   **Saved Files**: Check the `./server_output` directory to see all 20 correctly named files.
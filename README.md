# Go API Builder

A tool that converts and transforms API specifications and implementations between different languages and frameworks, focused on Go APIs.

## Overview

Go API Builder is a Streamlit-based application that helps developers convert API specifications and implementations. The tool provides an interactive chat interface for working with API transformations.

## Features

- Interactive chat interface for API transformation
- Support for building Go API implementations
- LangGraph-powered workflow for API analysis and generation
- Docker support for containerized deployment

## Installation

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/mlhelpx/goapi2api.git
   cd goapi2api
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env  # Create from example if available, otherwise create .env file
   ```
   Add your API keys and configuration settings to the .env file.

## Usage

Start the Streamlit application:

```bash
streamlit run ui.py
```

The application will be available at http://localhost:8501 by default.

## Docker Deployment

Build and run using Docker:

```bash
# Build the Docker image
docker build -t goapi2api .

# Run the container
docker run -p 8501:8501 goapi2api
```

## Development

This project uses:

- Streamlit for the user interface
- LangGraph for workflow orchestration
- Pydantic AI for AI-assisted code generation

## Project Structure

- `src/` - Core application code
  - `chat.py` - Chat interface implementation
  - `graph.py` - LangGraph workflow definition
  - `pydantic_ai_coder.py` - AI code generation utilities
  - `styles.py` - UI styling
- `ui.py` - Main Streamlit application entry point
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
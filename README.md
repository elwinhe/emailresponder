# Automated Email Response System

This system automatically fetches, processes, and responds to emails while respecting dependencies and deadlines.

## Features

- Fetches emails from a REST API endpoint
- Processes emails in parallel using thread pools
- Respects email dependencies and enforces minimum gaps between responses
- Simulates LLM response generation with configurable delays
- Handles errors gracefully with retries and proper logging
- Supports test mode for debugging

## Requirements

- Python 3.8+
- Required packages (see requirements.txt):
  - requests
  - numpy
  - python-dotenv
  - urllib3

## Usage

1. Install dependencies:
```

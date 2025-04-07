from __future__ import annotations
from dotenv import load_dotenv
import streamlit as st
import logfire
import asyncio

# Set page config - must be the first Streamlit command
st.set_page_config(
    page_title="Go API Builder",
    layout="wide",
)

# Utilities and styles
from src.styles import load_css

# Streamlit pages - only import chat page
from src.chat import chat_ui

# Load environment variables from .env file
load_dotenv()

# Initialize clients

# Load custom CSS styles
load_css()

# Configure logfire to suppress warnings (optional)
logfire.configure(send_to_logfire='never')

async def main():
    st.title("Go API Builder")
    await chat_ui()

if __name__ == "__main__":
    asyncio.run(main())

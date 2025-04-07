from langgraph.types import Command
import streamlit as st
import uuid
import sys
import os
import html2text
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph import agentic_flow

@st.cache_resource
def get_thread_id():
    return str(uuid.uuid4())

thread_id = get_thread_id()

async def extract_webpage_content(url: str) -> str:
    """
    Extract content from a webpage using Playwright and html2text.
    
    Args:
        url (str): The URL of the webpage to extract content from
        
    Returns:
        str: The extracted content in markdown format
    """
    try:
        async with async_playwright() as p:
            # Launch browser with JavaScript enabled
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Navigate to the URL and wait for network to be idle
            await page.goto(url, wait_until='networkidle')
            
            # Get the page content after JavaScript execution
            html_content = await page.content()
            
            # Close browser
            await browser.close()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Convert to markdown using html2text
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True  # Ignore images in the content
            h.ignore_tables = False
            markdown_content = h.handle(str(soup))
            return markdown_content
            
    except Exception as e:
        st.error(f"Error extracting webpage content: {str(e)}")
        return ""

async def run_agent_with_streaming(user_input: str, api_reference: str = ""):
    """
    Run the agent with streaming text for the user_input prompt,
    while maintaining the entire conversation in `st.session_state.messages`.
    """
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    # Extract webpage content if URL is provided
    webpage_content = ""
    if api_reference and (api_reference.startswith('http://') or api_reference.startswith('https://')):
        webpage_content = await extract_webpage_content(api_reference)

    # First message from user
    if len(st.session_state.messages) == 1:
        async for msg in agentic_flow.astream(
                {
                    "latest_user_message": user_input, 
                    "api_reference": api_reference,
                    "webpage_content": webpage_content
                }, 
                config, 
                stream_mode="custom"
            ):
                yield msg
    # Continue the conversation
    else:
        async for msg in agentic_flow.astream(
            Command(resume=user_input), config, stream_mode="custom"
        ):
            yield msg

async def chat_ui():
    """Display the chat interface for talking to Go API Builder"""
    st.write("Add the link to the API documentation and describe what you want to build.")
    st.write("Example: Build me an API that can search the web with the Brave API.")

    # Initialize chat history in session state if not present
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        message_type = message["type"]
        if message_type in ["human", "ai", "system"]:
            with st.chat_message(message_type):
                st.markdown(message["content"])    

    # Add API reference input
    api_reference = st.text_input("API Reference (optional)", placeholder="Enter API documentation URL or reference")

    # Chat input for the user
    user_input = st.chat_input("What do you want to build today?")

    if user_input:
        # We append a new request to the conversation explicitly
        # If this is the first message and we have API reference, append the crawled content
        webpage_content = ""
        if len(st.session_state.messages) == 0 and api_reference and (api_reference.startswith('http://') or api_reference.startswith('https://')):
            webpage_content = await extract_webpage_content(api_reference)
        
        # Store the original user input for display
        display_input = user_input
        
        # Append API content to user input for the agent
        if webpage_content:
            user_input += f"\n\nThe information for the API might be found in:\n{webpage_content}"
        
        st.session_state.messages.append({"type": "human", "content": display_input})
        
        # Display user prompt in the UI
        with st.chat_message("user"):
            st.markdown(display_input)

        # Display assistant response in chat message container
        response_content = ""
        with st.chat_message("assistant"):
            message_placeholder = st.empty()  # Placeholder for updating the message
            # Run the async generator to fetch responses
            async for chunk in run_agent_with_streaming(user_input, api_reference):
                response_content += chunk
                # Update the placeholder with the current response content
                message_placeholder.markdown(response_content)
        
        st.session_state.messages.append({"type": "ai", "content": response_content})
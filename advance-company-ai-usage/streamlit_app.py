import os
import json
import asyncio
import streamlit as st

from dotenv import load_dotenv
from mighty_sdk_core.auth.types import OAuthTokenParam
from mighty_sdk_core.auth.oauth import exchange_code_for_biscuit_token
from mighty_sdk_core.mighty.application_client import MightyApplicationClient
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

application_api_key = os.getenv("MIGHTY_OAUTH_APPLICATION_API_KEY")
application_private_key = os.getenv("MIGHTY_OAUTH_APPLICATION_PRIVATE_KEY")
application_id = os.getenv("MIGHTY_OAUTH_APPLICATION_ID")

# Mighty application client
application_client = MightyApplicationClient(
    api_key=application_api_key,            # Loaded from .env
    app_private_key=application_private_key  # Loaded from .env
)

async def process_oauth_code(code: str):
    """Process the OAuth code and return user info."""
    # Read the code verifier from the file
    with open("code_verifier.txt", "r") as file:
        code_verifier = file.read().strip()

    # Prepare token request parameters
    token_param = OAuthTokenParam(
        client_id=application_id,
        code_verifier=code_verifier,  # From the previous step
        redirect_uri="http://localhost:8501",
    )

    # Exchange authorization code for token
    token = await exchange_code_for_biscuit_token(
        code=code, 
        expiration=3600, 
        usage_once=True, 
        application_api_key=application_api_key,
        oauth_config=token_param
    )
    
    # Fetch user data
    user_info = await application_client.get_user_data_biscuit(token.biscuit_token)
    
    return token.biscuit_token, user_info

async def refresh_user_data(token: str):
    """Refresh user data using the stored token."""
    user_info = await application_client.get_user_data_biscuit(token)
    return user_info

def display_success_message():
    """Display success message after data submission."""
    st.success("✅ Agent has successfully submitted your information to the system!")

def display_user_data(user_info):
    """Display user data in a formatted way."""
    st.write("---")
    st.subheader("Your Information")
    st.json(user_info)

def display_biscuit_token(token):
    """Display the biscuit token in a secure way."""
    if token:
        st.write("---")
        st.subheader("Your Biscuit Token")
        st.code(token, language="text")
        st.info("🔒 This token is sensitive information. Keep it secure!")

def display_private_data_qa_agent():
    """Display the private data QA agent."""
    st.write("---")
    st.subheader("Private Data QA Agent")

    llm = ChatOpenAI(
        model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        base_url="http://localhost:8080/api/v1/app/ai",
        api_key=os.getenv("MIGHTY_OAUTH_APPLICATION_API_KEY")
    )

    def answer_private_data_question(user_question: str, user_data: dict) -> str:
        prompt = (
            "You are an AI assistant that answers questions about the user's private data. "
            "Here is the user's data in JSON format:\n"
            f"{json.dumps(user_data, indent=2)}\n"
            f"User question: {user_question}\n"
            "Answer the question as accurately as possible using only the provided data. "
            "If the answer is not present in the data, make an educated guess based on the context or say 'I do not have that information.' "
            "Always provide a response to the user's question."
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    user_question = st.text_area("Ask a question about your private data (e.g., 'What is my passport number?')", key="private_data_qa")
    if st.button("Ask QA Agent"):
        user_data = st.session_state.user_info or {}
        if not user_question.strip():
            st.warning("Please enter a question.")
        elif not user_data:
            st.warning("No user data available.")
        else:
            answer = answer_private_data_question(user_question, user_data)
            st.success(f"Answer:\n{answer}")

# Streamlit app
st.title("Mighty Private Data QA Agent Example")

# Initialize session state for token if not exists
if 'biscuit_token' not in st.session_state:
    st.session_state.biscuit_token = None
if 'user_info' not in st.session_state:
    st.session_state.user_info = None
if 'submission_complete' not in st.session_state:
    st.session_state.submission_complete = False

# Get query parameters from URL
query_params = st.query_params
code = query_params.get("code")

# If we have a token and submission is complete, show success message and data
if st.session_state.biscuit_token and st.session_state.submission_complete:
    display_success_message()
    display_user_data(st.session_state.user_info)
    display_biscuit_token(st.session_state.biscuit_token)
    display_private_data_qa_agent()

# If we have user data but haven't submitted yet
elif st.session_state.user_info and not st.session_state.submission_complete:
    display_user_data(st.session_state.user_info)
    display_biscuit_token(st.session_state.biscuit_token)
    with st.spinner("Submitting your information to the system..."):
        # Simulate processing time
        # asyncio.run(asyncio.sleep(10))
        st.session_state.submission_complete = True
        st.rerun()

# If we don't have a token but have a code, process the authorization
elif code:
    try:
        with st.spinner("Exchanging authorization code for token..."):
            # Run the async function
            token, user_info = asyncio.run(process_oauth_code(code))
            st.session_state.biscuit_token = token
            st.session_state.user_info = user_info
            st.rerun()
            
    except Exception as e:
        st.error(f"Error during token exchange: {e}")

# If we don't have either, show the authorization message
else:
    st.warning("Please authorize the application to access your data.")
    st.info("Run the following command to get the authorization URL:")
    st.code("poetry run python generate_url.py")
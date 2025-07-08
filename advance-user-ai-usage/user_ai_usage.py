import streamlit as st
import json
from mighty_sdk_core.mighty.user_data_client import MightyUserDataClient
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

# Replace with your actual credentials
api_key = os.getenv("MIGHTY_DATA_API_KEY")
public_key = os.getenv("MIGHTY_DATA_PUBLIC_KEY")
private_key = os.getenv("MIGHTY_DATA_PRIVATE_KEY")

client = MightyUserDataClient(
    api_key=api_key,
    api_public_key=public_key,
    api_private_key=private_key
)

def get_user_data():
    try:
        data = asyncio.run(client.get_data())
        return data
    except Exception as e:
        st.error(f"Error fetching user data: {e}")
        return None

def answer_private_data_question(user_question: str, user_data: dict) -> str:
    llm = ChatOpenAI(
        model_name="deepseek-ai/DeepSeek-R1-Distill-Qwen-14B",
        base_url="https://service-platform.prod.mightynetwork.ai/api/v1/app/ai",
        api_key=os.getenv("MIGHTY_DATA_API_KEY")
    )
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

def main():
    st.title("Private Data QA Agent")
    st.write("---")
    st.subheader("Step 1: Fetch your private data")
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if st.button("Fetch My Private Data"):
        user_data = get_user_data()
        if user_data:
            st.session_state.user_data = user_data
            st.success("User data fetched successfully!")
        else:
            st.session_state.user_data = None
    if st.session_state.user_data:
        st.write("#### Your Private Data (JSON):")
        st.json(st.session_state.user_data)
        st.write("---")
        st.subheader("Step 2: Ask a question about your private data")
        user_question = st.text_area(
            "Ask a question (e.g., 'What is my passport number?')",
            key="private_data_qa"
        )
        if st.button("Ask QA Agent"):
            if not user_question.strip():
                st.warning("Please enter a question.")
            else:
                answer = answer_private_data_question(user_question, st.session_state.user_data)
                st.success(f"Answer:\n{answer}")
    else:
        st.info("Please fetch your private data first.")

if __name__ == "__main__":
    main()
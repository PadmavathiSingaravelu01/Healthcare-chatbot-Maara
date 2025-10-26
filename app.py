import streamlit as st
from maara_ai import *
import uuid
import maara 
import io, tempfile, base64
from PIL import Image

doc_path = 'icons/docter.png'
user_path = 'icons/user-icon.png'
github_icon_path = 'icons/git.png'
linkedin_icon_path = 'icons/linkedin.png'

doc_base64 = maara.get_image_as_base64(doc_path)
user_base64 = maara.get_image_as_base64(user_path)
github_base64 = maara.get_image_as_base64(github_icon_path)
linkedin_base64 = maara.get_image_as_base64(linkedin_icon_path)

languages = {
    'English': 'en',
    'Tamil': 'ta',
    'Malayalam': 'ml',
    'Kannada': 'kn',
    'Telugu': 'te'
}

def user_message(message):
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="margin-right: 10px;">
                <img src="data:image/png;base64,{user_base64}" width="34" height="34" />
            </div>
            <div style="background-color: #4CAF50; color: white; padding: 10px; border-radius: 10px; font-size:18px;">
                {message}
            </div>
        </div>
        """, unsafe_allow_html=True)

def bot_message(message):
    st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 10px;">
            <div style="margin-right: 10px;">
                <img src="data:image/png;base64,{doc_base64}" width="34" height="34" />
            </div>
            <div style="background-color: #2196F3; color: white; padding: 10px; border-radius: 10px; font-size:18px;">
                {message}
            </div>
        </div>
        """, unsafe_allow_html=True)


def generate_new_conversation_id():
    """Generate a new, unique conversation ID."""
    return str(uuid.uuid4())

def start_new_conversation(update_language=False):
    """Start a new conversation by resetting the chat history and generating a new conversation ID.
       Optionally updates the last language to avoid immediate rerun loop when changing languages."""
    st.session_state.chat_history = []
    st.session_state.conversation_id = generate_new_conversation_id()
    if update_language:
        pass  
    else:
        st.rerun()

def main():
    # Start New Conversation button
    if st.sidebar.button("Start New Conversation"):
        start_new_conversation()

    st.sidebar.title("Preferred language")

    # Initialize conversation_id in session state if it doesn't exist
    if "conversation_id" not in st.session_state:
        st.session_state.conversation_id = generate_new_conversation_id()

    # Initialize last_uploaded_file in session state if it doesn't exist
    if "last_uploaded_file" not in st.session_state:
        st.session_state.last_uploaded_file = None

    # Language selection
    if "last_language" not in st.session_state:
        st.session_state.last_language = 'en'
    
    selected_language_name = st.sidebar.selectbox('Choose your language:', list(languages.keys()), index=0)
    selected_language_code = languages[selected_language_name]

    # Check for language change
    if selected_language_code != st.session_state.last_language:
        start_new_conversation(True)  
        st.session_state.last_language = selected_language_code

    #Document uploading
    st.sidebar.title("Upload Document")
    uploaded_file = st.sidebar.file_uploader("Upload your Medical reports or images here", type=['pdf', 'png', 'jpg'])

    if uploaded_file is not None:
        if "last_uploaded_file" not in st.session_state or uploaded_file.name != st.session_state.last_uploaded_file:
            st.session_state.last_uploaded_file = uploaded_file.name
            # Process the uploaded file
            if uploaded_file.type == 'application/pdf':
                extracted_pdf_data = maara.pdf_text_extracter(uploaded_file)
                extracted_pdf_data = f"User uploaded pdf report :\n {extracted_pdf_data}"
            elif uploaded_file.type.startswith('image/'):
                file_content = uploaded_file.read()
                base_64_content = base64.b64encode(file_content).decode()
                extracted_pdf_data = maara.gpt_vision(prompt=None, file_path=base_64_content)
                extracted_pdf_data = f"User uploaded Image :\n {extracted_pdf_data}"
            else:
                extracted_pdf_data = None
                st.warning("Unsupported file format. Please upload a PDF or an image.")

            st.session_state.processed_data = extracted_pdf_data
            st.sidebar.write("File processed successfully!")
        else:
            extracted_pdf_data = st.session_state.processed_data 
    else:
        extracted_pdf_data = None

    st.title("Maara AI Doctor👨🏻‍⚕️")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    user_input = st.chat_input("Prompt here")

    if user_input:
        for message, is_bot_response in st.session_state.chat_history:
            if is_bot_response:
                bot_message(message)
            else:
                user_message(message)

        st.session_state.chat_history.append((user_input, False))
        user_message(user_input)

        # Pass the conversation_id to the assistant functions
        if selected_language_code == 'en':
            bot_response = maara_ai_assistant(user_input, st.session_state.conversation_id, extracted_pdf_data)
        else:
            bot_response = maara_ai_mulitlang_assistant(user_input, st.session_state.conversation_id, selected_language_code, extracted_pdf_data)

        bot_message(bot_response)
        st.session_state.chat_history.append((bot_response, True))

if __name__ == "__main__":
    main()
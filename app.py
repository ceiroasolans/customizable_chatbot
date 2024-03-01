import openai
import streamlit as st
from datetime import datetime
import mysql.connector
import uuid

# Initialize session state for message tracking and other variables
if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Set your OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# Database connection
conn = mysql.connector.connect(
    user=st.secrets['sql_user'],
    password=st.secrets['sql_password'],
    database=st.secrets['sql_database'],
    host=st.secrets['sql_host'],
    port=st.secrets['sql_port']
)

# Function to create table if it doesn't exist
def create_conversations_table():
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
        conversation_id VARCHAR(255),
        user_id VARCHAR(255),
        date VARCHAR(255),
        hour VARCHAR(255),
        content MEDIUMTEXT
    )
    ''')
    conn.commit()
    cursor.close()

create_conversations_table()

# Function to save conversations to the database
def save_conversation(conversation_id, user_id, content):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (conversation_id, user_id, date, hour, content) VALUES (%s, %s, %s, %s, %s)",
                   (conversation_id, user_id, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
    conn.commit()
    cursor.close()

# Custom CSS for styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
    }
    .message {
        margin: 10px 0;
        padding: 10px;
        border-radius: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        width: 70%;
        position: relative;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        margin-left: auto;
        border-top-right-radius: 0;
        text-align: left;
    }
    .bot-message {
        background-color: #f1f1f1;
        color: #333;
        margin-right: auto;
        border-top-left-radius: 0;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# Chat header with logo and name
st.markdown("""
<style>
    .chat-header {
        display: flex;
        align-items: center;
        padding: 10px;
        background-color: #f1f1f1; /* Light grey background */
        border-top-left-radius: 10px; /* Rounded corners at the top to match the chat container */
        border-top-right-radius: 10px;
    }
    
    .circle-logo {
        height: 40px;
        width: 40px;
        background-color: #4CAF50; /* Green background */
        border-radius: 50%; /* Makes the div circular */
        margin-right: 10px;
    }
    
    .chat-header h4 {
        margin: 0;
        font-weight: normal;
    }
            
    .chat-container {
        display: grid;
        flex-direction: column-reverse;
        justify-content: flex-start;
        height: 90vh;
        overflow-y: auto;
        margin-bottom: 10vh;
    }

    .input-container {
        display: flex;
        justify-content: space-between;
        height: 8vh;
        padding: 10px;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        z-index: 2;
    }

    .stTextInput>div>div>input {
        flex-grow: 1;
        margin-top: 0px;
        margin-right: 10px; /* Adjust space between input and button */
        border-radius: 20px !important; /* Keep your rounded corners */
        padding: 10px !important; /* Keep your padding */
    }
    

    .stButton>button {
        white-space: nowrap; /* Ensure button text does not wrap */
        border-radius: 20px; /* Match your input's rounded corners */
        border: 1px solid #007bff;
        color: #ffffff;
        background-color: #007bff;
        padding: 10px;
        margin-top: 10px;
        font-size: 16px;
    }
</style>

<div class="chat-header">
    <div class="circle-logo"></div> 
    <h4>Alex</h4>
</div>
""", unsafe_allow_html=True)


# Display messages using markdown to apply custom styles
for message in st.session_state["messages"]:
    message_class = "user-message" if message["role"] == "user" else "bot-message"
    st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Input field for new messages
if prompt := st.chat_input("Please type your entire response in one message."):
    st.session_state["last_submission"] = prompt
    save_conversation(st.session_state["conversation_id"], "user_id_placeholder", f"You: {prompt}")
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Immediately display the participant's message using the new style
    message_class = "user-message"
    st.markdown(f"<div class='message {message_class}'>{prompt}</div>", unsafe_allow_html=True)

    # Prepare the conversation history for OpenAI API
    conversation_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    # Call OpenAI API and display bot's response 
    response = openai.ChatCompletion.create(model="gpt-4-turbo-preview", messages=conversation_history)

    bot_response = response.choices[0].message.content
    save_conversation(st.session_state["conversation_id"], "user_id_placeholder", f"Alex: {bot_response}")
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    # Display the bot's response using the new style
    message_class = "bot-message"
    st.markdown(f"<div class='message {message_class}'>{bot_response}</div>", unsafe_allow_html=True)

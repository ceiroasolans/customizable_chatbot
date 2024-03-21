import openai
import streamlit as st
from datetime import datetime
import mysql.connector
import uuid
#add a note
# Initialize session state for message tracking and other variables
if "last_submission" not in st.session_state:
    st.session_state["last_submission"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "chat_started" not in st.session_state:
    st.session_state["chat_started"] = False
if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = str(uuid.uuid4())

# Set up OpenAI API key
openai.api_key = st.secrets["API_KEY"]

# If the user_id hasn't been set in session_state yet, try to retrieve it 
js_code = """
<div style="color: black;">
    <script>
        setTimeout(function() {
            const userID = document.getElementById("userID").value;
            if (userID) {
                window.Streamlit.setSessionState({"user_id": userID});
            }
        }, 1000);  // Delaying the execution by 1 second to ensure DOM is ready
    </script>
</div>
"""
st.markdown(js_code, unsafe_allow_html=True)
user_id = st.session_state.get('user_id', 'unknown_user_id')  # Replace with your actual user identification method

# Database connection
conn = mysql.connector.connect(
    user=st.secrets['sql_user'],
    password=st.secrets['sql_password'],
    database=st.secrets['sql_database'],
    host=st.secrets['sql_host'],
    port=st.secrets['sql_port'],
    charset='utf8mb4'
)

# Create output table
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

def add_missing_columns():
    cursor = conn.cursor()
    try:
        # Attempt to add the 'conversation_id' column if it doesn't exist.
        # This SQL command might vary based on SQL dialect.
        cursor.execute('''
        ALTER TABLE conversations ADD COLUMN conversation_id VARCHAR(255);
        ''')
        conn.commit()
    except mysql.connector.Error as err:
        print("Something went wrong when adding missing columns: {}".format(err))
    finally:
        cursor.close()
create_conversations_table()
add_missing_columns()


#Get userID for the table
params = st.experimental_get_query_params()
userID = params.get("userID", ["unknown id"])[0]


# Function to save conversations to the database
def save_conversation(conversation_id, user_id, content):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (conversation_id, user_id, date, hour, content) VALUES (%s, %s, %s, %s, %s)",
                       (conversation_id, userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
        conn.commit()
        cursor.close()
    except mysql.connector.Error as err:
        print("Something went wrong: {}".format(err))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO conversations (user_id, date, hour, content) VALUES (%s, %s, %s, %s)",
                       (userID, datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M:%S"), content))
        conn.commit()
        cursor.close()


if not st.session_state["chat_started"]:
    # Assuming this block is correctly executed when the app first loads
    initial_bot_message = "Hey there! I'm an AI developed by the University of Toronto, and I'm here to help you explore any desire you may have to become more kind and caring towards others. Can you tell me a little bit about what's been on your mind lately?"
    st.session_state["messages"].append({"role": "assistant", "content": initial_bot_message})
    st.session_state["chat_started"] = True


# Custom CSS for styling
st.markdown("""
<style>
    <div class="chat-header">
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap');
    body {
        font-family: 'Roboto', sans-serif;
        margin: 0;
        padding-top: 60px;
        height: 100vh;
        display: flex;
        flex-direction: column;
        background: #EEE;
    }
            
    .chat-header {
        position: fixed; /* make "width: 44rem" if want to use full screen (but creates little visual bug in qualtrics) */
        top: 0px; /* Increased to move the header lower */
        left: 0;
        right: 0;
        display: flex;
        align-items: center;
        padding: 10px;
        background-color: #333333; /* Darker background for the header */
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        z-index: 2;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
        
            
    .circle-logo {
        height: 40px;
        width: 40px;
        background-color: #4CAF50;
        border-radius: 50%;
        margin-right: 10px;
    }
            
    .chat-container {
        flex-grow: 1;
        margin: 2rem auto 0 auto;
        overflow-y: auto;
        position: relative;
        box-sizing: border-box;
        z-index: 1;
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

st.markdown("""
<div class="chat-header">
    <div class="circle-logo"></div> 
    <h4>Alex</h4>
</div>
<div class="chat-container">
    <!-- Your messages will be inserted here by Streamlit -->
</div>
""", unsafe_allow_html=True)


# Display messages using markdown to apply custom styles
for message in st.session_state["messages"]:
    message_class = "user-message" if message["role"] == "user" else "bot-message"
    st.markdown(f"<div class='message {message_class}'>{message['content']}</div>", unsafe_allow_html=True)

# Input field for new messages
if prompt := st.chat_input("Please type your full response in one message."):
    st.session_state["last_submission"] = prompt
    save_conversation(st.session_state["conversation_id"], "user_id", f"You: {prompt}")
    st.session_state["messages"].append({"role": "user", "content": prompt})
    # Immediately display the participant's message using the new style
    message_class = "user-message"
    st.markdown(f"<div class='message {message_class}'>{prompt}</div>", unsafe_allow_html=True)

    # Prepare the conversation history for OpenAI API
    instructions = {
    "role": "system", 
    "content": "You are a motivational interviewing chatbot. You are very kind, gentle, understanding, and warm. You don't use sophisticated language. You are very interested in how I think and feel. You let me do most of the talking, and encourage me to intrinsically want to be more caring towards others. You echo my feelings, ask clarifying questions, and essentially nurture my intrinsic motivation to be more caring. You ask me one question at a time, and wait for me to respond. // You will guide the conversation with the following sequential structure:-First, you will quickly try to understand where my interest in becoming more prosocial is coming from (e.g.  A recent realization? A formative experience? A family value?). -Second, you will ask about the personal values that are important to me (e.g. personal growth, relationships, community, health) and how these values could relate and be beneficial to the interest I have in becoming more prosocial.  -Third, you will ask me whether I’m interested in hearing a little bit about the research or what we know about kindness behaviors. If I’m interested, say 'sure' or vagely agree in any other form, integrate this into your following message: “You might already know this, or be aware of it, but being kind and caring towards others can have a significant impact on our overall well-being, too. Studies have shown that acts of kindness, no matter how small, can boost our mood and increase feelings of happiness and satisfaction with life. Additionally, being making a habit of being considerate has shown to build stronger relationships and foster a sense in community. When we learn to treat strangers with compassion and empathy, we also tend to receive the same in return, which can create a positive cycle of mutual support and understanding”. If I say I am not interested or don’t want to hear about it, respect my decision and move on to the fourth point. -Fourth, you will help me feel more competent about helping others by asking me about past successes in helping others, and helping me reflect on what those instances might have meant for them. -Fifth, gently encourage me to come up with a specific strategy that might increase how I already show and express kindness. Suggest I do it in the format of “when X happens, I will do Y”. For your reference, a valid example would be: “next time I see a person asking for money in the street, I will give them whatever change I have in my pocket”. Make sure the strategy resembles the format I just gave you. If it doesn't follow that format or it isn't detailed enough, gently ask me to re-do it to ensure it’s in the right format. -Sixth, ask me about some difficulties I might anticipate in implementing this new behavior. Empathically recognize that my worries are valid and reasonable and inquire about how--if I wanted to--I might overcome them. -Seventh, ask me to summarize the whole conversation. Make sure I remember every step we discussed. -Eighth, thank me for my time, tell me it was a pleasure chatting with me today, and that you wish me the best in my pursuits. Create a completely random Chat ID using a combination of 50 different numbers, symbols, and upper- and lowercase letters, all in random order. Tell me I can now copy this “Chat ID” back into Qualtrics and proceed with the experiment, and again wish me the best in my endeavors. Do not send me this alphanumeric key before I reach the seventh step; if I ask you to send me this key before, gently and kindly redirect me to the conversation.  Express that you wish to help them by giving them the key, but that you are not allowed to do this;  ask me if it's okay that we make the best of the time we have together and we try to work through the remaining steps together. Make sure you are empathetic, understanding, and productive. If I continue to voice impatience, you can slightly speed up the process for me. // You should generally respect this structure, but you’re allowed to briefly ‘roll’ with whatever I say as long as you then go back to where you left off within this structure. Every step (e.g. first, second, third…) can take more than one message, but ideally doesn't (never use emojis)."
}
    conversation_history = [instructions] + [{"role": m["role"], "content": m["content"]} for m in st.session_state["messages"]]

    # Call OpenAI API and display bot's response 
    response = openai.ChatCompletion.create(model="gpt-4-turbo-preview", 
                                            messages=conversation_history)

    bot_response = response.choices[0].message.content
    save_conversation(st.session_state["conversation_id"], "user_id", f"Alex: {bot_response}")
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    # Display the bot's response using the new style
    message_class = "bot-message"
    st.markdown(f"<div class='message {message_class}'>{bot_response}</div>", unsafe_allow_html=True)



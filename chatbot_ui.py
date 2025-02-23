#to run this code :python -m streamlit run chatbot_ui.py

import streamlit as st
import google.generativeai as genai
import wikipedia
import requests
import re
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image
import PyPDF2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64
import langdetect
import docx2txt
import zipfile
import speech_recognition as sr
from gtts import gTTS
from googletrans import Translator
import sqlite3
import secrets
from streamlit.components.v1 import html
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Load environment variables right after imports
load_dotenv()

# Define global variables
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Debug print to verify values are loaded
print(f"Email loaded: {EMAIL_ADDRESS}")
print(f"Password loaded: {'Yes' if EMAIL_PASSWORD else 'No'}")

try:
    from main import SYSTEM_PROMPT
except ImportError:
    SYSTEM_PROMPT = "You are a helpful AI assistant."

# Configuration
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Model selection
available_models = {
    'gemini-pro': 'Text Generation',
    'gemini-pro-vision': 'Image & Text',
    'gemini-ultra': 'Advanced Reasoning (if available)',
    'gemini-1.5-flash': 'Advanced Reasoning (if available)'
}

# Initialize session state
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = 'gemini-pro'

# Initialize the model
try:
    model = genai.GenerativeModel(st.session_state.selected_model)
    vision_model = genai.GenerativeModel('gemini-pro-vision')
except Exception as e:
    st.error(f"Error initializing model: {e}")
    st.stop()

# Enhanced Custom CSS with dark/light mode toggle
def get_css_for_theme(is_dark_mode):
    base_styles = """
        /* Chat message container */
        .chat-message-container {
            display: flex;
            margin: 1rem 0;
            padding: 0 1rem;
            animation: fadeIn 0.3s ease-in-out;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Message bubbles */
        [data-testid="chat-message"] {
            background: transparent !important;
            padding: 1rem !important;
            width: 80% !important;
            border-radius: 15px !important;
            position: relative;
            line-height: 1.5 !important;
        }

        /* User message styling */
        [data-testid="chat-message-user"] {
            background: rgba(46, 126, 248, 0.1) !important;
            margin-left: auto !important;
            border-right: 3px solid #2E7EF8 !important;
            color: #FFFFFF !important;
        }

        /* Assistant message styling */
        [data-testid="chat-message-assistant"] {
            background: rgba(255, 255, 255, 0.05) !important;
            margin-right: auto !important;
            border-left: 3px solid #00CF65 !important;
            color: #FFFFFF !important;
        }

        /* Code blocks in messages */
        .chat-message pre {
            background: rgba(0, 0, 0, 0.2) !important;
            border-radius: 10px !important;
            padding: 15px !important;
            margin: 10px 0 !important;
            overflow-x: auto !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        .chat-message code {
            color: #E0E0E0 !important;
            font-family: 'Consolas', 'Monaco', monospace !important;
        }

        /* Message timestamp */
        .message-timestamp {
            font-size: 0.7rem;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 5px;
            text-align: right;
        }

        /* Chat input container */
        .stChatInputContainer {
            padding: 1rem !important;
            background: rgba(255, 255, 255, 0.05) !important;
            border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
            position: fixed !important;
            bottom: 0 !important;
            width: 100% !important;
            z-index: 100 !important;
        }

        /* Chat input field */
        .stChatInput {
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 10px 20px !important;
            color: white !important;
            transition: all 0.3s ease !important;
        }

        .stChatInput:focus {
            border-color: #2E7EF8 !important;
            box-shadow: 0 0 0 1px #2E7EF8 !important;
            background: rgba(46, 126, 248, 0.1) !important;
        }

        /* Markdown content styling */
        .chat-message p {
            margin: 0 0 10px 0 !important;
        }

        .chat-message ul, .chat-message ol {
            margin: 10px 0 !important;
            padding-left: 20px !important;
        }

        .chat-message h1, .chat-message h2, .chat-message h3 {
            margin: 15px 0 10px 0 !important;
            color: #2E7EF8 !important;
        }

        /* Links in messages */
        .chat-message a {
            color: #2E7EF8 !important;
            text-decoration: none !important;
            border-bottom: 1px dashed #2E7EF8 !important;
        }

        .chat-message a:hover {
            border-bottom-style: solid !important;
        }

        /* Tables in messages */
        .chat-message table {
            border-collapse: collapse !important;
            width: 100% !important;
            margin: 10px 0 !important;
            background: rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }

        .chat-message th, .chat-message td {
            padding: 8px 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }

        .chat-message th {
            background: rgba(46, 126, 248, 0.1) !important;
            color: #2E7EF8 !important;
        }

        /* Blockquotes in messages */
        .chat-message blockquote {
            border-left: 3px solid #2E7EF8 !important;
            margin: 10px 0 !important;
            padding: 10px 20px !important;
            background: rgba(46, 126, 248, 0.1) !important;
            border-radius: 0 10px 10px 0 !important;
        }
    """

    # Dark mode specific styles
    dark_theme = """
        /* Dark mode adjustments */
        [data-testid="chat-message"] {
            color: #E0E0E0 !important;
        }
        
        .chat-message pre {
            background: rgba(0, 0, 0, 0.3) !important;
        }
    """

    # Light mode specific styles
    light_theme = """
        /* Light mode adjustments */
        [data-testid="chat-message"] {
            color: #2C3E50 !important;
        }
        
        [data-testid="chat-message-user"] {
            background: rgba(46, 126, 248, 0.1) !important;
            border-right: 3px solid #2E7EF8 !important;
        }
        
        [data-testid="chat-message-assistant"] {
            background: rgba(0, 207, 101, 0.1) !important;
            border-left: 3px solid #00CF65 !important;
        }
        
        .chat-message pre {
            background: rgba(0, 0, 0, 0.05) !important;
        }
    """

    return f"""
        <style>
            {base_styles}
            {dark_theme if is_dark_mode else light_theme}
        </style>
    """

# Initialize more session state variables
if 'chat' not in st.session_state:
    try:
        st.session_state.chat = model.start_chat(history=[])
    except Exception as e:
        st.error(f"Error starting chat: {e}")
        st.stop()
if 'messages' not in st.session_state:
    st.session_state.messages = []
    welcome_message = {
        "role": "assistant",
        "content": """👋 Welcome to HyperAssist! I'm your AI assistant, ready to help you with:
        
        • Answering questions
        • Writing and analysis
        • Problem-solving
        • And much more!
        
        Note: To save your chat history and access all features, please sign in or create an account.
        
        How can I help you today?"""
    }
    st.session_state.messages.append(welcome_message)
if 'file_context' not in st.session_state:
    st.session_state.file_context = {}
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'conversation_title' not in st.session_state:
    st.session_state.conversation_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'api_usage' not in st.session_state:
    st.session_state.api_usage = {'tokens': 0, 'requests': 0, 'last_reset': datetime.now().isoformat()}
if 'saved_conversations' not in st.session_state:
    st.session_state.saved_conversations = {}
if 'translation_target' not in st.session_state:
    st.session_state.translation_target = None
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'analytics' not in st.session_state:
    st.session_state.analytics = {
        'chat_count': 0,
        'avg_response_time': 0,
        'total_response_time': 0,
        'file_uploads': {},
        'popular_topics': {},
        'message_lengths': []
    }
if 'language' not in st.session_state:
    st.session_state.language = 'en'  # Default language is English
if 'voice_output' not in st.session_state:
    st.session_state.voice_output = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Apply CSS based on theme
st.markdown(get_css_for_theme(st.session_state.dark_mode), unsafe_allow_html=True)

# Default settings for model parameters
DEFAULT_CONFIG = {
    'temperature': 0.7,
    'max_tokens': 1500,
    'code_execution': False,
    'web_search': False,
    'stream_output': True
}

# Model parameter presets
MODEL_PRESETS = {
    'Creative': {'temperature': 0.9, 'max_tokens': 2000},
    'Balanced': {'temperature': 0.7, 'max_tokens': 1500},
    'Precise': {'temperature': 0.5, 'max_tokens': 1000}
}

# Language options
LANGUAGE_OPTIONS = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ja': 'Japanese',
    'zh-cn': 'Simplified Chinese'
}

# Database initialization function
def init_db():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            profile_picture TEXT,
            bio TEXT,
            location TEXT
        )
    ''')
    
    # First drop the existing chat_history table if it exists
    c.execute('''DROP TABLE IF EXISTS chat_history''')
    
    # Create new chat_history table with is_hidden column
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            conversation_id TEXT NOT NULL,
            conversation_title TEXT NOT NULL,
            messages TEXT NOT NULL,
            is_hidden BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password, email, location, bio):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        # Check if username or email exists
        c.execute('SELECT username, email FROM users WHERE username = ? OR email = ?', 
                 (username, email))
        existing = c.fetchone()
        
        if existing:
            if existing[0] == username:
                return False, "Username already exists"
            else:
                return False, "Email already exists"
        
        # Create user
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute('''
            INSERT INTO users 
            (username, password, email, location, bio) 
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, email, location, bio))
        
        conn.commit()
        return True, "Account created successfully!"
            
    except Exception as e:
        print(f"Error creating user: {e}")
        return False, str(e)
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        c.execute('SELECT id FROM users WHERE username = ? AND password = ?', 
                 (username, password_hash))
        
        result = c.fetchone()
        return result[0] if result else None
    finally:
        conn.close()

def hide_chat_from_user(user_id, chat_id):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE chat_history 
            SET is_hidden = 1 
            WHERE user_id = ? AND conversation_id = ?
        ''', (user_id, chat_id))
        conn.commit()
    finally:
        conn.close()

def hide_all_chats(user_id):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE chat_history 
            SET is_hidden = 1 
            WHERE user_id = ?
        ''', (user_id,))
        conn.commit()
    finally:
        conn.close()

def load_user_chats(user_id):
    if user_id is None:
        return []
        
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        # Only load non-hidden chats
        c.execute('''
            SELECT conversation_id, conversation_title, messages, created_at
            FROM chat_history
            WHERE user_id = ? AND is_hidden = 0
            ORDER BY updated_at DESC
        ''', (user_id,))
        chats = c.fetchall()
        return chats
    except sqlite3.OperationalError as e:
        st.error(f"Database error: {e}")
        return []
    finally:
        conn.close()

def save_chat_to_db(user_id, title, messages):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    conversation_id = secrets.token_urlsafe(16)
    messages_json = json.dumps(messages)
    try:
        c.execute('''
            INSERT INTO chat_history (user_id, conversation_id, conversation_title, messages)
            VALUES (?, ?, ?, ?)
        ''', (user_id, conversation_id, title, messages_json))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# Add these new functions to handle contact form submissions
def save_contact_submission(name, email, subject, priority, message, attachment=None):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    
    try:
        # Save attachment if provided
        attachment_path = None
        if attachment:
            # Create uploads directory if it doesn't exist
            upload_dir = "uploads"
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
            
            # Save file with timestamp to prevent duplicates
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = re.sub(r'[^a-zA-Z0-9.]', '_', attachment.name)
            attachment_path = os.path.join(upload_dir, f"{timestamp}_{safe_filename}")
            
            with open(attachment_path, "wb") as f:
                f.write(attachment.getbuffer())

        # Insert submission into database
        c.execute('''
            INSERT INTO contact_submissions 
            (name, email, subject, priority, message, attachment_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, subject, priority, message, attachment_path))
        
        conn.commit()
        return True, "Submission saved successfully"
    
    except Exception as e:
        return False, f"Error saving submission: {str(e)}"
    
    finally:
        conn.close()

# Optional: Email notification function (requires smtp setup)
def send_notification_email(name, email, subject, priority, message):
    try:
        # Add your email sending logic here
        # Example using smtplib:
        """
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        sender_email = "your-email@example.com"
        sender_password = "your-password"
        receiver_email = "support@example.com"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f"New Contact Form Submission: {subject}"

        body = f'''
        New contact form submission received:
        
        Name: {name}
        Email: {email}
        Subject: {subject}
        Priority: {priority}
        
        Message:
        {message}
        '''

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        """
        return True, "Notification email sent"
    except Exception as e:
        return False, f"Error sending notification: {str(e)}"

# Enhanced welcome popup
def show_welcome_popup():
    st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1 style="color: #2E7EF8; font-size: 3rem; margin-bottom: 2rem;">
                Welcome to HyperAssist Pro
            </h1>
            <p style="color: #666; margin-bottom: 3rem; font-size: 1.2rem;">
                Your AI-powered assistant for smarter conversations
            </p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔐 Sign In", key="signin", use_container_width=True):
            st.session_state.auth_mode = "login"
            st.rerun()
    
    with col2:
        if st.button("✨ Create Account", key="signup", use_container_width=True):
            st.session_state.auth_mode = "signup"
            st.rerun()
    
    with col3:
        if st.button("👋 Continue as Guest", key="guest", use_container_width=True):
            st.session_state.auth_mode = "guest"
            st.rerun()

    # Add features section
    st.markdown("""
        <div style='margin-top: 3rem;'>
            <div class='card'>
                <h3>🚀 Key Features</h3>
                <ul>
                    <li>Advanced AI Conversations</li>
                    <li>Multi-language Support</li>
                    <li>File Analysis & Processing</li>
                    <li>Voice Interaction</li>
                </ul>
            </div>
            
            <div class='card'>
                <h3>🔒 Why Create an Account?</h3>
                <ul>
                    <li>Save conversation history</li>
                    <li>Personalized responses</li>
                    <li>Access advanced features</li>
                    <li>Cloud synchronization</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Authentication forms
def show_login_form():
    st.markdown("""
        <style>
        .form-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .login-title {
            color: #2E7EF8;
            margin-bottom: 2rem;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # Back button
    if st.button("← Back", key="back_login"):
        st.session_state.auth_mode = None
        st.rerun()

    # Login form in a container
    with st.container():
        st.markdown("<h1 class='login-title'>Welcome Back!</h1>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please fill all fields")
                    return
                    
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state.is_authenticated = True
                    st.session_state.user_id = user_id
                    st.success("Login successful!")
                    time.sleep(1)
                    st.session_state.auth_mode = "authenticated"
                    st.rerun()
                else:
                    st.error("Invalid username or password")

def show_signup_form():
    st.markdown("""
        <style>
        .signup-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .signup-title {
            color: #2E7EF8;
            margin-bottom: 2rem;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    # Back button
    if st.button("← Back", key="back_signup"):
        st.session_state.auth_mode = None
        st.rerun()

    # Signup form in a container
    with st.container():
        st.markdown("<h1 class='signup-title'>Create Your Account</h1>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username", placeholder="Choose a username")
            with col2:
                email = st.text_input("Email", placeholder="Enter your email")
            
            location = st.text_input("Location", placeholder="Where are you from? (Optional)")
            bio = st.text_area("Bio", placeholder="Tell us about yourself (Optional)")
            
            col3, col4 = st.columns(2)
            with col3:
                password = st.text_input("Password", type="password", 
                                       placeholder="Create a password")
            with col4:
                confirm_password = st.text_input("Confirm Password", type="password",
                                               placeholder="Confirm your password")
            
            agree = st.checkbox("I agree to the Terms of Service and Privacy Policy")
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                if not all([username, email, password, confirm_password]):
                    st.error("Please fill all required fields")
                elif not agree:
                    st.error("Please agree to the Terms of Service")
                elif password != confirm_password:
                    st.error("Passwords do not match")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    success, message = create_user(username, password, email, location, bio)
                    if success:
                        st.success("Account created successfully! Redirecting to login...")
                        time.sleep(2)
                        st.session_state.auth_mode = 'login'
                        st.rerun()
                    else:
                        st.error(message)

# Guest interface
def show_guest_interface():
    # Keep the existing button CSS and add enhanced UI styles
    st.markdown(
        """
        <style>
        /* Existing button styles remain the same */
        
        /* Enhanced chat interface */
        .chat-container {
            max-width: 800px;
            margin: 2rem auto;
            padding: 20px;
        }
        
        .welcome-header {
            text-align: center;
            margin: 3rem 0;
            animation: fadeIn 0.8s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 2rem 0;
        }
        
        .feature-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .feature-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .chat-message {
            padding: 15px;
            border-radius: 10px;
            margin: 10px 0;
            max-width: 80%;
        }
        
        .user-message {
            background: rgba(46, 126, 248, 0.1);
            margin-left: auto;
            border-right: 3px solid #2E7EF8;
        }
        
        .bot-message {
            background: rgba(255, 255, 255, 0.05);
            margin-right: auto;
            border-left: 3px solid #00FF00;
        }
        
        /* Enhanced input field */
        .stTextInput > div > div {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 20px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            padding: 8px 20px !important;
        }
        
        .stTextInput > div > div:focus-within {
            border-color: #2E7EF8 !important;
            box-shadow: 0 0 0 1px #2E7EF8 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Keep existing button container code
    _, _, _, col1, col2 = st.columns([1, 1, 1, 0.5, 0.5])
    with col1:
        if st.button("Log in", key="guest_signin"):
            st.session_state.auth_mode = "login"
            st.rerun()
    with col2:
        if st.button("Sign up", key="guest_signup"):
            st.session_state.auth_mode = "signup"
            st.rerun()

    # Enhanced welcome section
    st.markdown("""
        <div class="welcome-header">
            <h1 style="color: #2E7EF8; font-size: 2.5rem; margin-bottom: 1rem;">
                Welcome to HyperAssist AI
            </h1>
            <p style="color: #888; font-size: 1.1rem;">
                Your intelligent conversation partner for endless possibilities
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Feature grid
    st.markdown("""
        <div class="feature-grid">
            <div class="feature-card">
                <h3>🤖 AI-Powered Chat</h3>
                <p>Advanced language model for natural conversations</p>
            </div>
            <div class="feature-card">
                <h3>📚 Knowledge Base</h3>
                <p>Access to vast information across various topics</p>
            </div>
            <div class="feature-card">
                <h3>⚡ Quick Responses</h3>
                <p>Fast and accurate answers to your questions</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Secure Chat</h3>
                <p>Private and secure conversations</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Initialize messages if empty
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        welcome_message = {
            "role": "assistant",
            "content": """👋 Hello! I'm your AI assistant, ready to help you with:

            • Questions & Answers
            • Problem Solving
            • Creative Writing
            • Analysis & Research
            • And much more!

            How can I assist you today?"""
        }
        st.session_state.messages.append(welcome_message)

    # Display chat messages with enhanced styling
    for message in st.session_state.messages:
        message_class = "user-message" if message["role"] == "user" else "bot-message"
        st.markdown(f"""
            <div class="chat-message {message_class}">
                {message["content"]}
            </div>
        """, unsafe_allow_html=True)

    # Chat input with enhanced styling
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate AI response
        try:
            response = model.generate_content(prompt)
            bot_response = response.text
            st.session_state.messages.append({"role": "assistant", "content": bot_response})
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")

def clear_user_chat_view():
    # Clear all session state messages and chat history
    st.session_state.messages = []
    st.session_state.saved_conversations = {}  # Clear saved conversations
    
    # Add fresh welcome message
    welcome_message = {
        "role": "assistant",
        "content": """👋 Welcome to HyperAssist! I'm your AI assistant, ready to help you with:
        
        • Answering questions
        • Writing and analysis
        • Problem-solving
        • And much more!
        
        How can I help you today?"""
    }
    st.session_state.messages.append(welcome_message)
    st.session_state.conversation_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

def delete_chat_from_view(chat_id):
    # Remove specific chat from session state
    if 'saved_conversations' in st.session_state:
        if chat_id in st.session_state.saved_conversations:
            del st.session_state.saved_conversations[chat_id]
    
    # If current chat is being deleted, clear the messages
    if st.session_state.get('current_chat_id') == chat_id:
        st.session_state.messages = []
        st.session_state.conversation_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

def show_authenticated_interface():
    # Sidebar with all features
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h1 style='color: #2E7EF8; margin-bottom: 10px;'>🤖 HyperAssist</h1>
                <p style='color: #666; font-size: 0.9em;'>Your AI Assistant</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Chat History Section with enhanced styling
        st.markdown("""
            <div style='margin: 20px 0;'>
                <h2 style='color: #2E7EF8; font-size: 1.3em;'>💬 Chat History</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # New Chat and Clear History buttons with better styling
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Chat", 
                        key="new_chat", 
                        use_container_width=True,
                        help="Start a new conversation"):
                st.session_state.messages = []
                st.session_state.conversation_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear All", 
                        key="clear_history", 
                        use_container_width=True,
                        help="Clear chat history"):
                if st.session_state.messages:
                    if st.button("Confirm Clear?", key="confirm_clear"):
                        clear_user_chat_view()
                        st.rerun()
        
        # Recent Chats with enhanced styling
        st.markdown("<h3 style='color: #666; font-size: 1.1em; margin: 20px 0 10px;'>Recent Chats</h3>", 
                   unsafe_allow_html=True)
        
        # Show chat history
        chats = load_user_chats(st.session_state.user_id)
        for chat in chats:
            col3, col4 = st.columns([4, 1])
            with col3:
                if st.button(f"📄 {chat[1]}", 
                           key=f"chat_{chat[0]}", 
                           use_container_width=True):
                    st.session_state.messages = json.loads(chat[2])
                    st.session_state.conversation_title = chat[1]
                    st.session_state.current_chat_id = chat[0]
                    st.rerun()
            with col4:
                if st.button("🗑️", 
                           key=f"delete_{chat[0]}", 
                           help="Hide this chat"):
                    hide_chat_from_user(st.session_state.user_id, chat[0])
                    if st.session_state.get('current_chat_id') == chat[0]:
                        st.session_state.messages = []
                        st.session_state.conversation_title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    st.rerun()
        
        # Settings section with better organization
        st.markdown("""
            <div style='margin: 30px 0 10px;'>
                <h2 style='color: #2E7EF8; font-size: 1.3em;'>⚙️ Settings</h2>
            </div>
        """, unsafe_allow_html=True)
        
        # Model Selection
        st.markdown("<h3 style='color: #666; font-size: 1.1em;'>Model</h3>", unsafe_allow_html=True)
        model_choice = st.selectbox(
            "Select Model",
            options=list(available_models.keys()),
            format_func=lambda x: f"{x} - {available_models[x]}",
            key="model_select"
        )
        
        # Language Selection
        st.markdown("<h3 style='color: #666; font-size: 1.1em;'>Language</h3>", unsafe_allow_html=True)
        selected_language = st.selectbox(
            "Select Language",
            options=LANGUAGE_OPTIONS.keys(),
            format_func=lambda x: LANGUAGE_OPTIONS[x],
            key="language_select"
        )
        
        # Theme Toggle
        st.markdown("<h3 style='color: #666; font-size: 1.1em;'>Theme</h3>", unsafe_allow_html=True)
        dark_mode = st.toggle("Dark Mode", value=st.session_state.dark_mode)
        if dark_mode != st.session_state.dark_mode:
            st.session_state.dark_mode = dark_mode
            st.rerun()
        
        # Voice Settings
        st.markdown("<h3 style='color: #666; font-size: 1.1em;'>Voice</h3>", unsafe_allow_html=True)
        voice_enabled = st.toggle("Enable Voice", value=st.session_state.voice_output)
        if voice_enabled != st.session_state.voice_output:
            st.session_state.voice_output = voice_enabled
            st.rerun()
        
        # Profile section
        st.markdown("""
            <div style='margin: 30px 0 10px;'>
                <h2 style='color: #2E7EF8; font-size: 1.3em;'>👤 Profile</h2>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True):
            st.session_state.is_authenticated = False
            st.session_state.user_id = None
            st.session_state.auth_mode = None
            st.rerun()

    # Main chat interface
    st.markdown(f"""
        <div style='margin-bottom: 20px;'>
            <h1 style='color: #2E7EF8;'>💬 {st.session_state.conversation_title}</h1>
        </div>
    """, unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    st.markdown(bot_response)
                    
                    # Auto-save chat
                    if st.session_state.user_id:
                        save_chat_to_db(
                            st.session_state.user_id,
                            st.session_state.conversation_title,
                            st.session_state.messages
                        )
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Add this function to handle auto-saving when app closes
def auto_save_on_close():
    if st.session_state.get('is_authenticated') and st.session_state.get('user_id'):
        if st.session_state.get('messages'):
            save_chat_to_db(
                st.session_state.user_id,
                st.session_state.conversation_title,
                st.session_state.messages
            )

# Main function
def main():
    # Initialize database
    init_db()
    
    # Register auto-save function
    st.session_state['on_close'] = auto_save_on_close
    
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = None
    
    if st.session_state.auth_mode is None:
        show_welcome_popup()
    elif st.session_state.auth_mode == "login":
        show_login_form()
    elif st.session_state.auth_mode == "signup":
        show_signup_form()
    elif st.session_state.auth_mode == "authenticated":
        show_authenticated_interface()
    elif st.session_state.auth_mode == "guest":
        show_guest_interface()

if __name__ == "__main__":
    main()

def get_chat_message_styling():
    return """
        <style>
        /* Message styling */
        [data-testid="chat-message"] {
            padding: 15px !important;
            margin: 1rem 0 !important;
            border-radius: 12px !important;
            width: auto !important;
            max-width: 85% !important;
            display: flex !important;
            align-items: flex-start !important;
        }

        /* User message */
        [data-testid="chat-message-user"] {
            background: #1a2433 !important;
            margin-left: auto !important;
            border-right: 3px solid #2196f3 !important;
            position: relative !important;
        }

        /* Assistant message */
        [data-testid="chat-message-assistant"] {
            background: #1e1e1e !important;
            margin-right: auto !important;
            border-left: 3px solid #00e676 !important;
            position: relative !important;
        }

        /* Chat input styling */
        .stChatInput {
            background-color: #1a2433 !important;
            border-radius: 10px !important;
            border: 1px solid #2f3b4b !important;
            padding: 15px !important;
            color: white !important;
        }

        .stChatInput:focus {
            border-color: #2196f3 !important;
            box-shadow: none !important;
        }

        /* Message animation */
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .stChatMessage {
            animation: slideIn 0.3s ease forwards;
        }
        </style>
    """

def show_chat_interface():
    # Apply the chat styling
    st.markdown(get_chat_message_styling(), unsafe_allow_html=True)

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Message Gemini..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = model.generate_content(prompt)
                    bot_response = response.text
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    st.markdown(bot_response)
                except Exception as e:
                    st.error(f"Error: {str(e)}")

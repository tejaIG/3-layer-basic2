# app.py
import streamlit as st
import cv2
import numpy as np
import requests
from database import UserDatabase, FileManager
import os
import time

# Initialize database and file manager
db = UserDatabase()
file_manager = FileManager()

def signup_page():
    st.title("Sign Up")
    
    # Create form
    with st.form("signup_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign Up")
        
        if submit and email and password:
            # Create user in database
            user_id = db.add_user(email, password)
            
            if user_id:
                st.success("Account created! Let's capture your face data.")
                st.session_state.signup_phase = 'capture'
                st.session_state.current_user = user_id
                st.rerun()
            else:
                st.error("Email already exists!")

def capture_face_data():
    st.title("Face Data Collection")
    st.info("We'll capture 10 images of your face. Please move your head slightly between captures.")
    
    # Initialize state variables
    if 'image_counter' not in st.session_state:
        st.session_state.image_counter = 0
    if 'capturing' not in st.session_state:
        st.session_state.capturing = False
    
    # Create user directory
    user_path = file_manager.create_user_directory(st.session_state.current_user)
    
    # Initialize camera
    cap = cv2.VideoCapture(0)
    frame_placeholder = st.empty()
    
    try:
        while st.session_state.image_counter < 10:
            ret, frame = cap.read()
            if not ret:
                st.error("Error accessing camera!")
                break
            
            # Display frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB")
            
            # Create unique key for each capture button
            capture_key = f"capture_btn_{st.session_state.image_counter}_{int(time.time())}"
            
            # Capture image
            if st.button(f"Capture Image {st.session_state.image_counter + 1}/10", 
                        key=capture_key):
                
                # Save image
                img_path = os.path.join(user_path, f'face_{st.session_state.image_counter}.jpg')
                cv2.imwrite(img_path, frame)
                
                # Send to Colab for processing
                response = send_to_colab(img_path, 'register')
                
                if response.get('success'):
                    st.session_state.image_counter += 1
                    if st.session_state.image_counter == 10:
                        db.update_face_path(st.session_state.current_user, user_path)
                        st.success("Face data collection complete! You can now log in.")
                        st.session_state.signup_phase = 'complete'
                        st.rerun()
                else:
                    st.error("Failed to process image. Please try again.")
    
    finally:
        cap.release()

def login_page():
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit and email and password:
            user_data = db.verify_user(email, password)
            
            if user_data:
                user_id, face_path = user_data
                st.success("Credentials verified! Proceeding to face verification...")
                st.session_state.login_phase = 'face_verify'
                st.session_state.current_user = user_id
                st.rerun()
            else:
                st.error("Invalid credentials!")

def verify_face():
    st.title("Face Verification")
    st.info("Please look at the camera for face verification.")
    
    cap = cv2.VideoCapture(0)
    frame_placeholder = st.empty()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                st.error("Error accessing camera!")
                break
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB")
            
            if st.button("Verify Face"):
                # Save temporary image
                temp_path = "temp_verify.jpg"
                cv2.imwrite(temp_path, frame)
                
                # Send to Colab for verification
                response = send_to_colab(temp_path, 'verify', 
                                       user_id=st.session_state.current_user)
                
                os.remove(temp_path)
                
                if response.get('success'):
                    st.success("Face verified! Login successful!")
                    time.sleep(2)
                    st.session_state.login_phase = 'complete'
                    st.rerun()
                else:
                    st.error("Face verification failed! Please try again.")
    
    finally:
        cap.release()

def send_to_colab(image_path, action, user_id=None):
    """
    Send image to Colab backend for processing
    Replace COLAB_URL with your actual Colab notebook URL exposed via ngrok
    """
    COLAB_URL = "https://c81d-34-125-191-121.ngrok-free.app"
    
    files = {'image': open(image_path, 'rb')}
    data = {
        'action': action,
        'user_id': user_id
    }
    
    try:
        response = requests.post(f"{COLAB_URL}/process", files=files, data=data)
        return response.json()
    except:
        return {'success': False, 'error': 'Failed to connect to backend'}

def main():
    st.set_page_config(page_title="Face Auth System", layout="wide")
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'signup_phase' not in st.session_state:
        st.session_state.signup_phase = 'form'
    if 'login_phase' not in st.session_state:
        st.session_state.login_phase = 'form'
    
    # Sidebar navigation
    with st.sidebar:
        st.title("Navigation")
        if st.button("Home"):
            st.session_state.page = 'home'
            st.rerun()
    
    # Main page logic
    if st.session_state.page == 'home':
        st.title("Welcome to Face Auth System")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Sign Up"):
                st.session_state.page = 'signup'
                st.session_state.signup_phase = 'form'
                st.rerun()
        
        with col2:
            if st.button("Login"):
                st.session_state.page = 'login'
                st.session_state.login_phase = 'form'
                st.rerun()
    
    elif st.session_state.page == 'signup':
        if st.session_state.signup_phase == 'form':
            signup_page()
        elif st.session_state.signup_phase == 'capture':
            capture_face_data()
        elif st.session_state.signup_phase == 'complete':
            st.success("Registration complete! Please proceed to login.")
            if st.button("Go to Login"):
                st.session_state.page = 'login'
                st.session_state.login_phase = 'form'
                st.rerun()
    
    elif st.session_state.page == 'login':
        if st.session_state.login_phase == 'form':
            login_page()
        elif st.session_state.login_phase == 'face_verify':
            verify_face()
        elif st.session_state.login_phase == 'complete':
            st.success("You are logged in!")
            if st.button("Logout"):
                st.session_state.page = 'home'
                st.session_state.login_phase = 'form'
                st.rerun()

if __name__ == "__main__":
    main()
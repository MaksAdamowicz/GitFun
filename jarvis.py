# AIzaSyCrX1XrWYRw-ST0r3LsewUhih5ExB-yuZg
from google import genai
import os

import os
import speech_recognition as sr
import pyttsx3
from google import genai

# --- INITIALIZATION ---
API_KEY = "AIzaSyCrX1XrWYRw-ST0r3LsewUhih5ExB-yuZg"
client = genai.Client(api_key=API_KEY)

# JARVIS Voice Setup
engine = pyttsx3.init()
voices = engine.getProperty('voices')
# Setting a British/Formal voice if available
engine.setProperty('voice', voices[0].id) 
engine.setProperty('rate', 175)

def speak(text):
    print(f"JARVIS: {text}")
    engine.say(text)
    engine.runAndWait()

# --- THE TOOLS (Hands) ---
def execute_system_command(command):
    """Simple logic to open apps based on keywords"""
    if "notepad" in command:
        speak("Opening Notepad, Sir.")
        os.system("notepad.exe")
    elif "chrome" in command or "browser" in command:
        speak("Launching Chrome.")
        os.system("start chrome")
    elif "calculator" in command:
        speak("Starting the calculator.")
        os.system("calc.exe")
    else:
        speak("I understood the intent, but I don't have the permission to open that specific app yet.")

# --- THE MAIN LOOP ---
def jarvis_main():
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        speak("Systems online. How can I help you, Sir?")
        
        while True:
            try:
                print("Listening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                user_input = recognizer.recognize_google(audio).lower()
                print(f"You: {user_input}")

                if "goodbye" in user_input or "sleep" in user_input:
                    speak("Powering down. Have a productive day, Sir.")
                    break

                # The Brain: Use Gemini to decide if we should open an app
                # We ask Gemini to respond with a special keyword 'ACTION:' if it wants to open something
                prompt = f"The user said: '{user_input}'. If they want to open an app (Notepad, Chrome, or Calculator), reply with 'ACTION: [app_name]'. Otherwise, just reply like JARVIS."
                
                response = client.models.generate_content(
                    model="gemini-2.5-flash", 
                    contents=prompt
                )
                
                ai_text = response.text
                
                if "ACTION:" in ai_text:
                    execute_system_command(user_input)
                else:
                    speak(ai_text)

            except Exception as e:
                # Silently wait for the next command if no speech is detected
                continue

if __name__ == "__main__":
    jarvis_main()
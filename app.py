import streamlit as st
import openai
import json
from pypdf import PdfReader
from datetime import datetime
import os
from dotenv import load_dotenv
import re # Add regex import
import traceback # Add for detailed exception logging
import requests

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY", "").strip().strip("'").strip('"')
if not api_key:
    st.error("OpenAI API key not found in environment variables")
    st.stop()

# Debug output (first/last 4 chars only for security)
print(f"API Key loaded (first/last 4 chars): {api_key[:4]}...{api_key[-4:]}")

# Initialize the OpenAI client with base URL and default headers
client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.openai.com/v1",
    default_headers={
        "OpenAI-Project": "proj_iS6x3Kfdco6oQtaB4Ue4mHS2",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "PostmanRuntime/7.36.3",
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Connection": "keep-alive"
    }
)

# Load quiz history
def load_quiz_history():
    try:
        with open("quiz_history.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"history": []}

# Save new quiz to history
def save_quiz_to_history(quiz_content, topic, difficulty):
    history = load_quiz_history()
    history["history"].append({
        "timestamp": datetime.now().isoformat(),
        "topic": topic,
        "difficulty": difficulty,
        "quiz": quiz_content
    })
    with open("quiz_history.json", "w") as file:
        json.dump(history, file, indent=4)

# Extract text from uploaded textbook PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# --- Refined Quiz Parsing Function ---
def parse_quiz(quiz_text):
    questions = []
    # Use regex that matches Question: at start (^) OR after newline (\n)
    # Filter out any empty strings resulting from the split
    question_blocks = [block for block in re.split(r"(?:^|\n)Question:\s*(?:\d+\.\s*)?", quiz_text.strip()) if block.strip()]

    print(f"[Parser] Found {len(question_blocks)} potential question blocks.") # Debug print

    for i, block in enumerate(question_blocks):
        print(f"\n[Parser] Processing Block {i+1}") # Debug print
        try:
            # Use splitlines() and strip each line immediately
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
            if not lines:
                print("[Parser] Block empty after stripping/splitting lines.") # Debug print
                continue

            question_text = lines[0] # Already stripped
            print(f"[Parser] Question: '{question_text}'") # Debug print

            options_dict = {}
            options_start_index = -1
            answer_start_index = -1
            explanation_start_index = -1

            # Find marker indices
            for idx, line in enumerate(lines):
                # Check against already stripped lines
                if line.startswith("Options:"): options_start_index = idx + 1
                elif line.startswith("Answer:"): answer_start_index = idx
                elif line.startswith("Explanation:"): explanation_start_index = idx

            print(f"[Parser] Indices - Opts:{options_start_index}, Ans:{answer_start_index}, Expl:{explanation_start_index}") # Debug print

            # Extract Options
            if options_start_index != -1 and answer_start_index != -1 and options_start_index <= answer_start_index:
                option_lines = lines[options_start_index:answer_start_index]
                for line in option_lines:
                    match = re.match(r"^([A-D])\.\s*(.*)", line) # Match already stripped line
                    if match:
                        options_dict[match.group(1)] = match.group(2).strip() # Ensure value is stripped too
                print(f"[Parser] Options Found: {options_dict}") # Debug print
            else:
                 print("[Parser] Markers for options/answer not found correctly or in wrong order.") # Debug print

            # Extract Answer
            correct_answer = None
            if answer_start_index != -1:
                # Get the next line after "Answer:" if it exists
                if answer_start_index + 1 < len(lines):
                    answer_line = lines[answer_start_index + 1]
                    # Try matching Letter.Text or just Letter
                    match_letter_dot = re.match(r"^([A-D])\.", answer_line)
                    match_letter_only = re.match(r"^([A-D])$", answer_line)

                    if match_letter_dot:
                        correct_answer = match_letter_dot.group(1)
                    elif match_letter_only:
                        correct_answer = match_letter_only.group(1)
                    print(f"[Parser] Answer Line: '{answer_line}', Parsed: '{correct_answer}'") # Debug print
                else:
                    print("[Parser] No line found after Answer: marker.") # Debug print
            else:
                print("[Parser] Answer marker not found.") # Debug print

            # Extract Explanation
            explanation = ""
            if explanation_start_index != -1 and explanation_start_index < len(lines) - 1:
                # Join lines *after* the explanation marker (lines are already stripped)
                explanation = '\n'.join(lines[explanation_start_index+1:]).strip() # Re-join stripped lines
                print(f"[Parser] Explanation Found (len: {len(explanation)}): '{explanation[:50]}...'" )# Debug print
            elif explanation_start_index != -1:
                 print("[Parser] Explanation marker found, but no text after it.") # Debug print
            else:
                 print("[Parser] Explanation marker not found.") # Debug print

            # Final Validation
            valid_question = bool(question_text)
            valid_options = len(options_dict) == 4
            valid_answer = bool(correct_answer)
            valid_explanation = bool(explanation)

            if valid_question and valid_options and valid_answer and valid_explanation:
                questions.append({
                    "question": question_text,
                    "options": options_dict,
                    "answer": correct_answer,
                    "explanation": explanation
                })
                print(f"[Parser] -> Block {i+1} Added.") # Debug print
            else:
                # More detailed validation failure log (prints to terminal)
                fail_reasons = []
                if not valid_question: fail_reasons.append("Missing Question Text")
                if not valid_options: fail_reasons.append(f"Incorrect Option Count ({len(options_dict)}) ")
                if not valid_answer: fail_reasons.append("Missing Answer")
                if not valid_explanation: fail_reasons.append("Missing Explanation")
                print(f"[Parser] -> Block {i+1} Failed Validation: {', '.join(fail_reasons)}") # Debug print

        except Exception as e:
            print(f"[Parser] -> EXCEPTION parsing block {i+1}: {e}") # Debug print
            print(traceback.format_exc()) # Print full traceback to terminal
            continue

    print(f"[Parser] Finished. Total questions parsed successfully: {len(questions)}") #Debug print
    return questions
# --- End Refined Quiz Parsing Function ---

# Generate quiz questions using OpenAI
def generate_quiz(textbook_content, quiz_history, difficulty, topic):
    try:
        # Limit the size of the textbook content sent to the API
        max_chars = 15000
        truncated_textbook_content = textbook_content[:max_chars]
        if len(textbook_content) > max_chars:
            truncated_textbook_content += "\n... [Text truncated due to length]"

        # Filter history based on the *detected topic* and limit the number of items
        relevant_history = [
            item for item in quiz_history.get("history", [])
            if item.get("topic") == topic
        ]
        recent_relevant_history = relevant_history[-10:]

        history_text = "\n".join([
            f"Q: {item.get('quiz', '').splitlines()[0]} A: {item.get('quiz', '').split('Answer:')[-1].strip()}"
            for item in recent_relevant_history
        ])

        # Define difficulty characteristics
        difficulty_guidelines = {
            "Beginner": """
- Focus on basic concept recognition and definitions
- Questions should test understanding of fundamental terms and ideas
- Use straightforward language and avoid complex terminology
- Options should be clearly distinct from each other
- Explanations should be simple and educational
""",
            "Intermediate": """
- Test application of concepts and relationships between ideas
- Include some technical terminology appropriate to the subject
- Questions may require connecting multiple concepts
- Options can be more nuanced but still distinct
- Explanations should provide deeper insight into the topic
""",
            "Advanced": """
- Test deep understanding and analysis of complex concepts
- Include detailed technical terminology and advanced concepts
- Questions should require critical thinking and synthesis of information
- Options may include subtle differences that test thorough understanding
- Explanations should explore underlying principles and connections
"""
        }

        prompt = f"""
You are an AI tutor helping students prepare for exams. You're creating a {difficulty} level quiz.

For this {difficulty} level:
{difficulty_guidelines[difficulty]}

The student provided the following textbook content (potentially truncated):
{truncated_textbook_content}

The student's past quiz history for the topic '{topic}' includes (most recent):
{history_text if history_text else "No relevant history found."}

Please generate 5 questions that match the {difficulty} level guidelines above. For each question:
- Ensure the difficulty matches the specified guidelines
- Make questions clear and unambiguous
- Include four distinct options (A, B, C, D)
- Provide a correct answer
- Give a thorough explanation that helps the student learn

Format each question exactly as follows:
Question:
Options:
A. Option A
B. Option B
C. Option C
D. Option D
Answer:
Explanation:
"""
        
        # Direct API call with proper headers for project API keys
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "OpenAI-Project": "proj_iS6x3Kfdco6oQtaB4Ue4mHS2",
            "User-Agent": "PostmanRuntime/7.36.3",
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "Connection": "keep-alive"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are a helpful AI tutor specializing in creating educational assessments that match the student's skill level."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        
        # Debug print request details
        print("\n----------- REQUEST HEADERS -----------")
        print(headers)
        print("\n----------- REQUEST BODY -----------")
        print(json.dumps(data, indent=2))
        print("--------------------------------------\n")
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        # Debug print response details
        print("\n----------- RESPONSE STATUS -----------")
        print(f"Status Code: {response.status_code}")
        print("\n----------- RESPONSE BODY -----------")
        print(response.text)
        print("--------------------------------------\n")
        
        if response.status_code != 200:
            error_detail = response.json().get('error', {}).get('message', 'Unknown error')
            st.error(f"OpenAI API error ({response.status_code}): {error_detail}")
            return None
            
        response_data = response.json()
        return response_data['choices'][0]['message']['content']
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

# Main Streamlit app
def main():
    # Set page config for better appearance
    st.set_page_config(
        page_title="AI Tutor Agent",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            width: 100%;
            border-radius: 10px;
            height: auto;
            padding: 15px;
        }
        .stTextArea > div > div > textarea {
            background-color: #f0f2f6;
        }
        .css-1d391kg {
            padding: 2rem 1rem;
        }
        .stProgress > div > div > div > div {
            background-color: #00acb5;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title with emoji and subtitle
    st.title("📚 AI Tutor Agent: Exam Practice")
    st.markdown("*Your personalized AI-powered study companion*")
    st.write("Upload your textbook PDF, select difficulty, and get an interactive quiz!")

    # --- Initialize Session State --- (if keys don't exist)
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
    if 'quiz_complete' not in st.session_state:
        st.session_state.quiz_complete = False
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []
    if 'current_q_index' not in st.session_state:
        st.session_state.current_q_index = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'attempts_left' not in st.session_state:
        st.session_state.attempts_left = 3
    if 'current_q_answered' not in st.session_state:
        st.session_state.current_q_answered = False
    if 'feedback_given' not in st.session_state:
        st.session_state.feedback_given = False
    if 'raw_quiz_output' not in st.session_state:
        st.session_state.raw_quiz_output = ""
    if 'current_topic' not in st.session_state:
        st.session_state.current_topic = "General"
    if 'current_difficulty' not in st.session_state:
        st.session_state.current_difficulty = "Beginner"
    # --- End Session State Init ---

    # --- Sidebar for Controls ---
    with st.sidebar:
        st.header("📋 Quiz Setup")
        
        # File upload with better instructions
        st.markdown("### 1. Upload Your Material")
        uploaded_file = st.file_uploader(
            "Choose a PDF textbook",
            type=["pdf"],
            help="Upload a PDF file containing the study material",
            key="pdf_uploader"
        )

        # Difficulty selection with descriptions
        st.markdown("### 2. Select Difficulty")
        difficulty_descriptions = {
            "Beginner": "Basic concepts and definitions",
            "Intermediate": "Application and connections",
            "Advanced": "Deep analysis and synthesis"
        }
        
        difficulty = st.selectbox(
            "Choose your level",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.current_difficulty),
            help="Select the difficulty level that matches your current understanding",
            key="difficulty_selector"
        )
        
        st.caption(f"*{difficulty_descriptions[difficulty]}*")

        # Generate button with clear styling
        st.markdown("### 3. Generate Quiz")
        if st.button("🎯 Generate New Quiz", use_container_width=True):
            if uploaded_file:
                with st.spinner("Processing PDF..."):
                    textbook_text = extract_text_from_pdf(uploaded_file)

                    if textbook_text.strip():
                        topic = textbook_text.split("\n")[0][:50].strip() if textbook_text else "General"
                        st.session_state.current_topic = topic
                        st.session_state.current_difficulty = difficulty # Store selected difficulty
                        quiz_history = load_quiz_history()

                        with st.spinner("Generating quiz with AI..."):
                            quiz_output = generate_quiz(textbook_text, quiz_history, difficulty, topic)

                            if quiz_output:
                                st.session_state.raw_quiz_output = quiz_output # Save raw for history
                                parsed_questions = parse_quiz(quiz_output)
                                if parsed_questions:
                                    # --- Reset State for New Quiz ---
                                    st.session_state.quiz_questions = parsed_questions
                                    st.session_state.current_q_index = 0
                                    st.session_state.user_answers = {}
                                    st.session_state.attempts_left = 3
                                    st.session_state.current_q_answered = False
                                    st.session_state.quiz_started = True
                                    st.session_state.quiz_complete = False
                                    st.session_state.feedback_given = False
                                    st.rerun() # Rerun to display the first question
                                else:
                                    st.error("Failed to parse the generated quiz. The format might be unexpected. Please try again.")
                                    # --- Show the raw output for debugging ---
                                    st.subheader("Raw AI Output (for debugging):")
                                    st.text_area("Output", quiz_output, height=300)
                                    # --- End debug display ---
                                    st.session_state.quiz_started = False # Ensure quiz doesn't start
                            else:
                                st.error("AI failed to generate quiz. Please check logs or API key and try again.")
                                st.session_state.quiz_started = False
                    else:
                        st.warning("Uploaded PDF seems empty or unreadable.")
                        st.session_state.quiz_started = False
            else:
                st.warning("Please upload a PDF first.")

    # --- Main Quiz Area ---
    if not st.session_state.quiz_started:
        # Welcome screen with instructions
        st.markdown("""
        ### 👋 Welcome to AI Tutor!
        
        Follow these steps to get started:
        1. Upload your study material (PDF) using the sidebar
        2. Choose your preferred difficulty level
        3. Click 'Generate New Quiz' to begin
        
        Your quiz will be tailored to your chosen difficulty and the content of your material.
        """)
        
        # Display a sample question format
        with st.expander("ℹ️ See how questions will be presented"):
            st.markdown("""
            Questions will be presented in this format:
            
            **Question:** [Your question here]
            
            **Options:**
            - A) First option
            - B) Second option
            - C) Third option
            - D) Fourth option
            
            You'll get instant feedback and explanations for each answer!
            """)

    elif st.session_state.quiz_started and not st.session_state.quiz_complete:
        # Progress bar for quiz
        progress = (st.session_state.current_q_index + 1) / len(st.session_state.quiz_questions)
        st.progress(progress)
        
        # Question counter with emoji
        st.markdown(f"### 📝 Question {st.session_state.current_q_index + 1} of {len(st.session_state.quiz_questions)}")
        
        # Current topic display
        st.caption(f"Topic: {st.session_state.current_topic}")
        
        # Question display with better formatting
        q_idx = st.session_state.current_q_index
        q_data = st.session_state.quiz_questions[q_idx]
        
        st.markdown(f"**{q_data['question']}**")
        st.divider()

        # Add CSS to ensure uniform button sizes
        st.markdown("""
            <style>
            .stButton button {
                width: 100%;
                min-height: 80px;
                white-space: normal;
                height: auto;
                text-align: left;
                padding: 15px;
            }
            </style>
            """, unsafe_allow_html=True)

        # Create placeholder for feedback message
        feedback_placeholder = st.empty()

        # Display Options as Buttons
        option_cols = st.columns(2) # Arrange options in 2 columns
        option_keys = list(q_data["options"].keys())
        
        # Calculate max option length for consistent sizing
        max_option_length = max(len(str(opt)) for opt in q_data["options"].values())
        
        for i, option_key in enumerate(option_keys):
            col = option_cols[i % 2]
            button_disabled = st.session_state.current_q_answered
            
            # Format option text with consistent padding
            option_text = f"{option_key}. {q_data['options'][option_key]}"
            
            if col.button(option_text, key=f"q{q_idx}_opt{option_key}", disabled=button_disabled):
                # --- Answer Submitted --- 
                is_correct = (option_key == q_data["answer"])
                st.session_state.user_answers[q_idx] = {"selected": option_key, "correct": is_correct}

                if is_correct:
                    feedback_placeholder.success(f"✅ Correct! The answer is {q_data['answer']}.")
                    st.session_state.current_q_answered = True
                else:
                    st.session_state.attempts_left -= 1
                    if st.session_state.attempts_left > 0:
                        feedback_placeholder.warning(f"❌ Incorrect. You have {st.session_state.attempts_left} attempt{'s' if st.session_state.attempts_left > 1 else ''} remaining. Try again!")
                    else:
                        feedback_placeholder.error(f"❌ Incorrect. No attempts left. The correct answer was {q_data['answer']}.")
                        st.session_state.current_q_answered = True
                st.rerun()

        # --- Display Persistent Feedback Message ---
        if st.session_state.user_answers.get(q_idx):
            last_answer_info = st.session_state.user_answers[q_idx]
            if last_answer_info["correct"]:
                feedback_placeholder.success(f"✅ Correct! The answer is {q_data['answer']}.")
            elif st.session_state.attempts_left <= 0:
                feedback_placeholder.error(f"❌ Incorrect. No attempts left. The correct answer was {q_data['answer']}.")
            elif not st.session_state.current_q_answered:
                feedback_placeholder.warning(f"❌ Incorrect. You have {st.session_state.attempts_left} attempt{'s' if st.session_state.attempts_left > 1 else ''} remaining. Try again!")

        # --- Next Question Button --- 
        if st.session_state.current_q_answered:
            st.write("---")  # Add a separator
            if q_idx < len(st.session_state.quiz_questions) - 1:
                col1, col2 = st.columns([1, 5])
                if col1.button("Next Question →", key=f"next_q{q_idx}"):
                    st.session_state.current_q_index += 1
                    st.session_state.attempts_left = 3 # Reset attempts for next question
                    st.session_state.current_q_answered = False # Reset answered status
                    st.rerun()
                col2.write("") # Empty column for spacing
            else:
                col1, col2 = st.columns([1, 5])
                if col1.button("Show Results 🎯", key=f"finish_q{q_idx}"):
                    st.session_state.quiz_complete = True
                    # Save the successful quiz to history NOW, before showing report
                    if st.session_state.raw_quiz_output:
                        save_quiz_to_history(st.session_state.raw_quiz_output, st.session_state.current_topic, st.session_state.current_difficulty)
                        st.session_state.raw_quiz_output = "" # Clear after saving
                    st.rerun()
                col2.write("") # Empty column for spacing

    # --- Quiz Complete / Report Area --- 
    elif st.session_state.quiz_complete:
        st.subheader("📊 Quiz Report")
        correct_count = 0
        total_questions = len(st.session_state.quiz_questions)

        for idx, q_data in enumerate(st.session_state.quiz_questions):
            st.divider()
            st.write(f"**Question {idx + 1}:** {q_data['question']}")
            user_answer_info = st.session_state.user_answers.get(idx)

            if user_answer_info:
                user_selected = user_answer_info['selected']
                is_correct = user_answer_info['correct']

                # Display options with correct/incorrect indicators
                st.write("**Options:**")
                for key, value in q_data['options'].items():
                    prefix = f"{key}. {value}"
                    if key == q_data['answer'] and key == user_selected:
                        st.success(f"✅ {prefix} (Your correct answer)")
                    elif key == q_data['answer']:
                        st.success(f"✅ {prefix} (Correct answer)")
                    elif key == user_selected:
                        st.error(f"❌ {prefix} (Your answer)")
                    else:
                        st.write(f"   {prefix}")

                # Update score and show explanation
                if is_correct:
                    correct_count += 1
                
                # Always show explanation in report
                st.info(f"**Explanation:** {q_data['explanation']}")
            else:
                st.warning("Answer not recorded for this question.")

        # Display final score with percentage
        st.divider()
        score_percentage = (correct_count / total_questions) * 100
        st.header(f"Final Score: {correct_count} out of {total_questions} ({score_percentage:.1f}%)")

        # Add score-based feedback
        if score_percentage == 100:
            st.balloons()
            st.success("🌟 Perfect score! Outstanding work!")
        elif score_percentage >= 80:
            st.success("🎉 Great job! You've shown excellent understanding!")
        elif score_percentage >= 60:
            st.info("👍 Good effort! Keep practicing to improve further.")
        else:
            st.warning("📚 Keep studying! Review the explanations to better understand the topics.")

        # --- Feedback --- (Only if not already given)
        if not st.session_state.feedback_given:
            st.divider()
            st.subheader("Was this quiz helpful?")
            feedback = st.radio("Your feedback", ("👍 Yes", "👎 No"), key="final_feedback", index=None)
            if feedback == "👍 Yes":
                st.success("Glad it was helpful! The agent will continue learning.")
                st.session_state.feedback_given = True
            elif feedback == "👎 No":
                st.warning("Thank you for the feedback! We'll use this to improve future quizzes.")
                st.session_state.feedback_given = True
        else:
             st.write("Thank you for your feedback!")

        # Allow starting over
        st.divider()
        if st.button("Start New Quiz with Same PDF"): # Re-generate with same text
             st.session_state.quiz_started = False
             st.session_state.quiz_complete = False
             st.session_state.quiz_questions = []
             st.session_state.user_answers = {}
             st.warning("Quiz reset. Click 'Generate New Quiz' in the sidebar to start again with the current settings.")
             st.rerun()


if __name__ == "__main__":
    main()
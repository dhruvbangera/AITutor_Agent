# AI Tutor Exam Practice 📚

An intelligent tutoring system that generates personalized quizzes from PDF textbooks using OpenAI's GPT models. Built with Streamlit and designed for an enhanced learning experience.

## 🌟 Features

- **PDF Processing**
  - Upload and process any PDF textbook
  - Intelligent text extraction and processing
  - Support for various PDF formats and layouts

- **Smart Quiz Generation**
  - Dynamic question generation based on content
  - Multiple difficulty levels (Beginner, Intermediate, Advanced)
  - Customizable number of questions (5-10)
  - Multiple choice format with detailed explanations
  - AI-powered answer validation

- **User Experience**
  - Clean, modern interface built with Streamlit
  - Responsive design for all devices
  - Real-time feedback and scoring
  - Progress tracking and history
  - Intuitive navigation and controls

- **AI Integration**
  - Powered by OpenAI's GPT models
  - Context-aware question generation
  - Intelligent answer evaluation
  - Detailed explanations for each answer

## 🚀 Quick Start

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dhruvbangera/AITutor_Agent.git
   cd AITutor_Agent
   ```

2. **Set Up Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Create a `.env` file in the root directory
   - Add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

## 📋 Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`:
  - streamlit
  - openai
  - pypdf
  - python-dotenv
  - requests

## 🎯 Usage Guide

1. **Upload PDF**
   - Click the file uploader
   - Select your PDF textbook
   - Wait for processing confirmation

2. **Configure Quiz**
   - Select difficulty level
   - Choose number of questions
   - Set any additional parameters

3. **Generate & Take Quiz**
   - Click "Generate Quiz"
   - Answer multiple choice questions
   - Submit for immediate feedback
   - Review explanations and score

4. **Track Progress**
   - View quiz history
   - Track performance over time
   - Review past explanations

## 🛠️ Technical Details

- **Frontend**: Streamlit
- **Backend**: Python
- **AI Model**: OpenAI GPT-3.5-turbo
- **PDF Processing**: PyPDF
- **Data Storage**: Local JSON

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [GitHub Repository](https://github.com/dhruvbangera/AITutor_Agent)
- [Issue Tracker](https://github.com/dhruvbangera/AITutor_Agent/issues)
- [Documentation](https://github.com/dhruvbangera/AITutor_Agent/wiki)

## 👥 Author

**Dhruv Bangera**
- GitHub: [@dhruvbangera](https://github.com/dhruvbangera)

## 🙏 Acknowledgments

- OpenAI for their powerful GPT models
- Streamlit for the amazing web framework
- All contributors and users of this project 
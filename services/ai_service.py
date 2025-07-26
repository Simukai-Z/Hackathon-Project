"""
AI Service for Study Tools
Handles AI-powered content generation for flash cards and study guides
"""

import os
from openai import AzureOpenAI
import dotenv

dotenv.load_dotenv()

class AIService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-05-01-preview"
        )
        self.model_name = "gpt-35-turbo"

    def generate_flashcards(self, content, subject="General", num_cards=10, difficulty="Medium"):
        """Generate flash cards from content using AI"""
        try:
            prompt = f"""
            Create {num_cards} flash cards from the following content for the subject "{subject}" with {difficulty} difficulty level.
            
            Content:
            {content}
            
            Format your response as a JSON array where each flash card has:
            - "question": A clear, concise question
            - "answer": A comprehensive but concise answer
            - "difficulty": The difficulty level (Easy, Medium, Hard)
            - "category": A relevant category or topic
            
            Make sure the questions test understanding, not just memorization.
            Vary the question types (definition, application, analysis, etc.).
            
            Return only the JSON array, no other text.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who specializes in creating effective study materials."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            return {
                "success": True,
                "flashcards": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_study_guide(self, content, subject="General", style="comprehensive", include_questions=True):
        """Generate a study guide from content using AI"""
        try:
            style_instructions = {
                "comprehensive": "Create a detailed, comprehensive study guide that covers all major topics and concepts thoroughly.",
                "concise": "Create a concise study guide that focuses on the most important points and key takeaways.",
                "detailed": "Create a detailed study guide with in-depth explanations and examples for each concept.",
                "exam-prep": "Create an exam-focused study guide with key points, formulas, and likely test questions."
            }
            
            questions_instruction = "Include practice questions at the end of each major section." if include_questions else "Do not include practice questions."
            
            prompt = f"""
            Create a {style} study guide from the following content for the subject "{subject}".
            
            Content:
            {content}
            
            Instructions:
            - {style_instructions.get(style, style_instructions["comprehensive"])}
            - Use clear headings and subheadings
            - Include bullet points and numbered lists where appropriate
            - Highlight key terms and concepts
            - {questions_instruction}
            - Format using markdown-style headers and formatting
            
            Make the study guide well-organized, easy to read, and effective for learning.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who specializes in creating comprehensive study materials."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.6
            )
            
            return {
                "success": True,
                "study_guide": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def enhance_flashcard_content(self, question, answer, subject="General"):
        """Enhance existing flash card content using AI"""
        try:
            prompt = f"""
            Improve this flash card for the subject "{subject}":
            
            Current Question: {question}
            Current Answer: {answer}
            
            Please:
            1. Improve the question to be more clear and engaging
            2. Enhance the answer to be more comprehensive but still concise
            3. Ensure the content is accurate and educational
            
            Return the improved flash card in this format:
            Question: [improved question]
            Answer: [improved answer]
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who specializes in improving study materials."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.6
            )
            
            return {
                "success": True,
                "enhanced_content": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def analyze_study_progress(self, flashcard_data, study_data):
        """Analyze study progress and provide recommendations"""
        try:
            prompt = f"""
            Analyze this student's study progress and provide recommendations:
            
            Flash Card Performance:
            {flashcard_data}
            
            Study Guide Usage:
            {study_data}
            
            Please provide:
            1. Overall performance assessment
            2. Areas of strength
            3. Areas needing improvement
            4. Specific study recommendations
            5. Suggested focus areas for next study session
            
            Keep the analysis encouraging and constructive.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert learning analytics specialist who provides helpful study recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.6
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

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
            # Validate inputs
            if not content or len(content.strip()) < 10:
                return {
                    "success": False,
                    "error": "Content is too short or empty for flash card generation"
                }
            
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
            
            Example format:
            [
                {{
                    "question": "What is the main purpose of X?",
                    "answer": "X is used for...",
                    "difficulty": "Medium",
                    "category": "{subject}"
                }}
            ]
            
            Return only the JSON array, no markdown formatting or additional text.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who specializes in creating effective study materials. Always respond with valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Add debug logging
            print(f"AI Service - Raw response length: {len(ai_response) if ai_response else 0}")
            if ai_response:
                print(f"AI Service - Response preview: {ai_response[:100]}...")
            else:
                print("AI Service - Empty response received")
            
            return {
                "success": True,
                "flashcards": ai_response or "[]"  # Ensure we never return None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_study_guide(self, content, subject="General", style="comprehensive", include_questions=True):
        """Generate a study guide from content using AI"""
        try:
            # Validate inputs
            if not content or len(content.strip()) < 10:
                return {
                    "success": False,
                    "error": "Content is too short or empty for study guide generation"
                }
            
            style_instructions = {
                "comprehensive": "Create a detailed, comprehensive study guide that covers all major topics and concepts thoroughly with extensive explanations.",
                "concise": "Create a concise study guide that focuses on the most important points and key takeaways.",
                "detailed": "Create a detailed study guide with in-depth explanations and examples for each concept.",
                "exam-prep": "Create an exam-focused study guide with key points, formulas, and likely test questions."
            }
            
            questions_instruction = "Include 3-5 practice questions at the end of each major section." if include_questions else "Do not include practice questions."
            
            prompt = f"""
            Create a comprehensive study guide from the following content for the subject "{subject}".
            
            Content to analyze:
            {content}
            
            Create a detailed study guide with the following structure:
            
            # Study Guide: {subject}
            
            ## Overview
            - Provide a brief summary of the main topics
            
            ## Key Concepts and Topics
            - Break down the content into 5-8 major sections
            - For each section, provide:
              * Clear heading
              * Detailed explanation (2-3 paragraphs minimum)
              * Key terms and definitions
              * Important examples or applications
              * Connection to other concepts
            
            ## Important Details
            - List specific facts, formulas, or procedures
            - Include any technical information
            - Highlight critical points to remember
            
            ## Summary and Review
            - Summarize the most important takeaways
            - List key points for quick review
            
            {"## Practice Questions" if include_questions else ""}
            {questions_instruction if include_questions else ""}
            
            Requirements:
            - {style_instructions.get(style, style_instructions["comprehensive"])}
            - Use clear markdown formatting with headers (##, ###)
            - Include bullet points and numbered lists
            - Make it at least 800-1200 words
            - Extract specific information from the provided content
            - Don't use generic placeholders - use actual content from the material
            - Be thorough and educational
            
            Focus on creating substantial, useful study material that a student can actually learn from.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who specializes in creating comprehensive, detailed study materials. Create substantial, useful content that students can actually learn from."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,  # Increased for longer content
                temperature=0.5   # Lower temperature for more focused content
            )
            
            ai_response = response.choices[0].message.content
            
            # Add debug logging
            print(f"Study Guide - Raw response length: {len(ai_response) if ai_response else 0}")
            if ai_response:
                print(f"Study Guide - Response preview: {ai_response[:200]}...")
            
            return {
                "success": True,
                "study_guide": ai_response or "# Study Guide\n\nNo content generated."
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

    def create_flashcards_from_chat(self, topic, details="", num_cards=10, difficulty="Medium"):
        """Create flashcards directly from chat conversation"""
        try:
            prompt = f"""
            Create {num_cards} educational flashcards about: {topic}
            
            Additional details: {details}
            Difficulty level: {difficulty}
            
            Guidelines:
            - Create questions that test understanding, not just memorization
            - Include a mix of definition, application, and analysis questions
            - Make answers comprehensive but concise
            - Ensure questions are clear and unambiguous
            
            Return ONLY a valid JSON array with this exact format:
            [
                {{
                    "question": "Clear, specific question",
                    "answer": "Comprehensive but concise answer",
                    "difficulty": "{difficulty}",
                    "category": "{topic}"
                }}
            ]
            
            No markdown formatting, no additional text, just the JSON array.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator. You always respond with valid JSON format only, no markdown or additional text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Clean the response to ensure valid JSON
            ai_response = ai_response.strip()
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            return {
                "success": True,
                "flashcards": ai_response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def create_study_guide_from_chat(self, topic, details="", style="comprehensive"):
        """Create a study guide directly from chat conversation"""
        try:
            style_descriptions = {
                "comprehensive": "detailed and thorough with extensive explanations",
                "concise": "brief and to-the-point with key concepts only", 
                "outline": "structured outline format with main points and sub-points",
                "visual": "includes diagrams, charts, and visual elements where helpful"
            }
            
            style_instruction = style_descriptions.get(style, "comprehensive and well-organized")
            
            prompt = f"""
            Create a {style_instruction} study guide about: {topic}
            
            Additional details: {details}
            
            Structure the study guide with:
            1. Clear headings and subheadings
            2. Key concepts and definitions
            3. Important facts and details
            4. Examples where helpful
            5. Summary points
            6. Practice questions (3-5 questions)
            
            Make it engaging and educational for students to review and study from.
            Use markdown formatting for better readability.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator who creates comprehensive, well-structured study guides that help students learn effectively."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_response(self, prompt, max_tokens=1000, temperature=0.7):
        """Generate a general AI response for any prompt"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides accurate and detailed responses."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            raise e

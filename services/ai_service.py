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
        """Generate a detailed and structured study guide from content using AI"""
        try:
            # Validate inputs
            if not content or len(content.strip()) < 10:
                return {
                    "success": False,
                    "error": "Content is too short or empty for study guide generation"
                }
            
            from datetime import datetime
            
            style_instructions = {
                "comprehensive": "Create a detailed, comprehensive study guide that covers all major topics and concepts thoroughly with extensive explanations, practical examples, and real-world applications.",
                "concise": "Create a concise study guide that focuses on the most important points and key takeaways with clear, direct explanations.",
                "detailed": "Create a detailed study guide with in-depth explanations, multiple examples, and comprehensive coverage of each concept.",
                "exam-prep": "Create an exam-focused study guide with key points, formulas, likely test questions, and strategic study tips."
            }
            
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            prompt = f"""
            Create a comprehensive, well-structured study guide from the following content for the subject "{subject}".
            
            Content to analyze:
            {content}
            
            Create a detailed study guide with the following EXACT structure and formatting:
            
            # {subject}
            **Study Guide**
            
            *Created: {current_time}*
            
            ---
            
            ## Table of Contents
            1. [Overview](#overview)
            2. [Key Concepts](#key-concepts)
            3. [Important Details & Examples](#important-details--examples)
            4. [Real-World Applications](#real-world-applications)
            {"5. [Practice Questions](#practice-questions)" if include_questions else ""}
            {"6. [Summary & Review](#summary--review)" if include_questions else "5. [Summary & Review](#summary--review)"}
            
            ---
            
            ## Overview
            
            Provide a comprehensive introduction to the topic that includes:
            - **Main Purpose**: What this subject/topic is about and why it's important
            - **Core Themes**: 3-4 central themes or principles
            - **Learning Objectives**: What students should understand after studying this material
            - **Prerequisites**: Any background knowledge that would be helpful
            
            ---
            
            ## Key Concepts
            
            Break down the content into 5-8 major concepts. For each concept, provide:
            
            ### [Concept Name]
            
            **Definition**: Clear, precise definition
            
            **Explanation**: 2-3 paragraphs of detailed explanation that:
            - Explains the concept in accessible language
            - Describes how it works or functions
            - Explains its significance or importance
            - Connects it to other related concepts
            
            **Key Terms**:
            - **Term 1**: Definition
            - **Term 2**: Definition
            - **Term 3**: Definition
            
            **Example**: Provide a concrete, practical example that illustrates the concept
            
            ---
            
            ## Important Details & Examples
            
            ### Critical Facts
            - List 8-12 specific, important facts that students must remember
            - Include any formulas, procedures, or technical information
            - Highlight measurements, dates, or quantitative information
            
            ### Detailed Examples
            Provide 3-4 comprehensive examples that demonstrate:
            1. **Example 1**: [Title] - Detailed walkthrough of a practical application
            2. **Example 2**: [Title] - Step-by-step process or procedure
            3. **Example 3**: [Title] - Problem-solving scenario
            4. **Example 4**: [Title] - Comparative analysis or case study
            
            ---
            
            ## Real-World Applications
            
            ### Practical Uses
            Describe 4-5 ways this knowledge is applied in real situations:
            - **Application 1**: Professional/career context
            - **Application 2**: Daily life context
            - **Application 3**: Academic/research context
            - **Application 4**: Industry/business context
            - **Application 5**: Future implications or developments
            
            ### Case Studies
            Provide 2-3 brief case studies that show the concepts in action
            
            ---
            
            {"## Practice Questions" if include_questions else ""}
            
            {"""
            Test your understanding with these questions:
            
            ### Comprehension Questions
            1. **Question 1**: [Conceptual understanding question]
               - *Answer*: [Detailed answer with explanation]
            
            2. **Question 2**: [Application question]
               - *Answer*: [Detailed answer with explanation]
            
            3. **Question 3**: [Analysis question]
               - *Answer*: [Detailed answer with explanation]
            
            ### Application Questions
            4. **Question 4**: [Problem-solving question]
               - *Answer*: [Step-by-step solution]
            
            5. **Question 5**: [Synthesis question]
               - *Answer*: [Comprehensive answer]
            
            ### Critical Thinking Questions
            6. **Question 6**: [Evaluation question]
               - *Answer*: [Analytical response]
            
            ---
            """ if include_questions else ""}
            
            ## Summary & Review
            
            ### Key Takeaways
            - **Primary Learning Point 1**: [Most important concept]
            - **Primary Learning Point 2**: [Second most important concept]
            - **Primary Learning Point 3**: [Third most important concept]
            - **Primary Learning Point 4**: [Fourth most important concept]
            - **Primary Learning Point 5**: [Fifth most important concept]
            
            ### Quick Review Checklist
            Use this checklist to verify your understanding:
            - [ ] I can explain the main purpose and importance of {subject}
            - [ ] I understand all the key concepts and their definitions
            - [ ] I can provide examples for each major concept
            - [ ] I can identify real-world applications
            - [ ] I can answer practice questions confidently
            - [ ] I can explain connections between different concepts
            
            ### Study Tips
            - **For Review**: Focus on the Key Concepts section and practice explaining each concept in your own words
            - **For Application**: Work through the examples and try to create your own similar scenarios
            - **For Mastery**: Complete all practice questions without looking at answers first
            - **For Retention**: Review the Summary section regularly and test yourself with the checklist
            
            ---
            
            Requirements for content creation:
            - {style_instructions.get(style, style_instructions["comprehensive"])}
            - Use the EXACT markdown structure provided above
            - Make content substantial (1200-1800 words minimum)
            - Extract ALL specific information from the provided content
            - Create original examples that relate to the actual content
            - Ensure all information is accurate and educational
            - Use clear, engaging language appropriate for students
            - Include internal links using markdown anchor format
            - Make every section comprehensive and valuable for learning
            
            Focus on creating a professional, comprehensive study guide that students can actually use to master the material.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational content creator and instructional designer who specializes in creating comprehensive, well-structured study materials. Your study guides are known for their clarity, depth, and practical value to students."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,  # Increased for longer content
                temperature=0.3   # Lower temperature for more structured, consistent content
            )
            
            ai_response = response.choices[0].message.content
            
            # Add debug logging
            print(f"Study Guide - Raw response length: {len(ai_response) if ai_response else 0}")
            if ai_response:
                print(f"Study Guide - Response preview: {ai_response[:200]}...")
            
            return {
                "success": True,
                "study_guide": ai_response or f"# {subject}\n**Study Guide**\n\nNo content could be generated from the provided material."
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_flashcards_from_study_guide(self, study_guide_content, subject="General", num_cards=15):
        """Generate flashcards automatically from a study guide"""
        try:
            if not study_guide_content or len(study_guide_content.strip()) < 100:
                return {
                    "success": False,
                    "error": "Study guide content is too short for flashcard generation"
                }
            
            prompt = f"""
            Analyze the following study guide and create {num_cards} comprehensive flashcards that test understanding of the key concepts, definitions, examples, and applications.
            
            Study Guide Content:
            {study_guide_content}
            
            Create flashcards that cover:
            - Key definitions and concepts
            - Important facts and details
            - Real-world applications
            - Examples and case studies
            - Practice questions from the guide
            
            For each flashcard, create:
            - A clear, specific question that tests understanding (not just memorization)
            - A comprehensive answer that includes explanation and context
            - Link back to the relevant section of the study guide
            
            Format your response as a JSON array with this exact structure:
            [
                {{
                    "question": "What is [concept] and why is it important in {subject}?",
                    "answer": "Detailed answer with explanation and examples",
                    "study_guide_section": "Key Concepts",
                    "difficulty": "Medium",
                    "type": "definition"
                }},
                {{
                    "question": "How would you apply [concept] in a real-world scenario?",
                    "answer": "Practical application with specific examples",
                    "study_guide_section": "Real-World Applications", 
                    "difficulty": "Hard",
                    "type": "application"
                }}
            ]
            
            Types of flashcards to include:
            - "definition": Tests understanding of key terms and concepts
            - "application": Tests ability to apply concepts practically
            - "example": Tests understanding through specific examples
            - "comparison": Tests ability to compare/contrast concepts
            - "analysis": Tests critical thinking and analysis skills
            
            Difficulty levels:
            - "Easy": Basic recall and simple definitions
            - "Medium": Understanding and explanation
            - "Hard": Application, analysis, and synthesis
            
            Make sure each flashcard:
            1. Has a clear, engaging question
            2. Includes a comprehensive answer with context
            3. References the specific study guide section
            4. Is appropriately difficulty-tagged
            5. Tests real understanding, not just memorization
            
            Return only the JSON array, no additional text or formatting.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert educational assessment creator who specializes in creating effective flashcards that test deep understanding rather than memorization. Always respond with valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.4
            )
            
            ai_response = response.choices[0].message.content
            
            # Clean the response to ensure valid JSON
            ai_response = ai_response.strip()
            if ai_response.startswith('```json'):
                ai_response = ai_response.replace('```json', '').replace('```', '').strip()
            elif ai_response.startswith('```'):
                ai_response = ai_response.replace('```', '').strip()
            
            # Add debug logging
            print(f"Flashcard Generation - Raw response length: {len(ai_response) if ai_response else 0}")
            if ai_response:
                print(f"Flashcard Generation - Response preview: {ai_response[:200]}...")
            
            return {
                "success": True,
                "flashcards": ai_response or "[]"
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

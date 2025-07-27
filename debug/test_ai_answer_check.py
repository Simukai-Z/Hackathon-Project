#!/usr/bin/env python3
"""
Test script for AI answer checking functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ai_service import AIService
import json

def test_ai_answer_evaluation():
    """Test the AI answer evaluation with real examples from the game results"""
    
    print("🧪 Testing AI Answer Evaluation System")
    print("=" * 50)
    
    try:
        ai_service = AIService()
        print("✅ AI Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Service: {e}")
        return False
    
    # Test cases from actual game results
    test_cases = [
        {
            "question": "Explain the concept of coroutines in Roblox Lua.",
            "correct_answer": "Coroutines in Roblox Lua are a way to achieve multitasking and concurrency. They allow for asynchronous execution of code.",
            "user_answer": "They create a new thread essentually creating a new script inside a script",
            "should_be_correct": True,
            "reason": "Shows understanding of threading/multitasking concept"
        },
        {
            "question": "Explain the concept of metatables in Roblox Lua.",
            "correct_answer": "Metatables in Roblox Lua are used to give tables special behaviors and properties. They allow for operator overloading and customizing how tables behave.",
            "user_answer": "they can make classes work",
            "should_be_correct": True,
            "reason": "Shows understanding that metatables enable class-like behavior"
        },
        {
            "question": "What are closures in Roblox Lua?",
            "correct_answer": "Closures are functions that capture variables from their surrounding lexical scope. They are commonly used for callbacks and event handling.",
            "user_answer": "idk",
            "should_be_correct": False,
            "reason": "No understanding demonstrated"
        },
        {
            "question": "How can you implement a custom event system in Roblox Lua?",
            "correct_answer": "To implement a custom event system in Roblox Lua, you can use a combination of tables, functions, and callbacks to create a flexible and efficient event handling mechanism.",
            "user_answer": ":getsignalchanged",
            "should_be_correct": False, # Partially correct but incomplete
            "reason": "Shows knowledge of Roblox events but doesn't address custom implementation"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}: {test_case['question'][:50]}...")
        print(f"Expected Answer: {test_case['correct_answer'][:100]}...")
        print(f"User Answer: '{test_case['user_answer']}'")
        print(f"Should be correct: {test_case['should_be_correct']} ({test_case['reason']})")
        
        # Create the AI prompt
        prompt = f"""
You are an expert educational assessment AI. Evaluate if the student's answer demonstrates understanding of the concept, even with different wording.

Question: {test_case['question']}
Expected Answer: {test_case['correct_answer']}
Student's Answer: {test_case['user_answer']}

IMPORTANT EVALUATION CRITERIA:
- Focus on conceptual understanding, not exact word matching
- Be very lenient with spelling errors, typos, and capitalization
- Accept synonyms and equivalent terms
- Accept answers in different sentence structures
- Consider abbreviations and shorthand acceptable
- Reward partial understanding with encouraging feedback
- If the student shows ANY understanding of the core concept, mark as correct

EXAMPLES:
- For "coroutines": Accept "threads", "new script", "multitasking", "async"
- For "metatables": Accept "classes", "custom behavior", "special tables"
- For "pairs vs ipairs": Accept "all vs numbers", "everything vs integers"

You MUST respond with ONLY valid JSON in this exact format:

{{
  "is_correct": true,
  "feedback": "Great job! Your answer shows you understand that [concept]. [encouragement]",
  "confidence": 0.95
}}

OR for incorrect answers:

{{
  "is_correct": false,
  "feedback": "Good attempt! You're on the right track with [partial understanding]. The key concept is [explanation]. Try thinking about [hint].",
  "confidence": 0.90
}}

CRITICAL: Return ONLY the JSON object. No markdown, no extra text, no explanations outside the JSON.
"""
        
        try:
            # Get AI response
            response = ai_service.generate_response(prompt, max_tokens=300)
            print(f"🤖 AI Raw Response: {response}")
            
            # Parse the response
            response_cleaned = response.strip()
            
            # Remove any markdown formatting
            import re
            if response_cleaned.startswith('```'):
                response_cleaned = re.sub(r'^```(?:json)?\s*', '', response_cleaned)
                response_cleaned = re.sub(r'\s*```$', '', response_cleaned)
            
            # Parse JSON
            try:
                result = json.loads(response_cleaned)
                
                is_correct = result.get('is_correct', False)
                feedback = result.get('feedback', 'No feedback')
                confidence = result.get('confidence', 0.0)
                
                print(f"📊 AI Assessment: {is_correct} (confidence: {confidence})")
                print(f"💬 Feedback: {feedback}")
                
                # Check if AI assessment matches expectation
                assessment_correct = is_correct == test_case['should_be_correct']
                status = "✅ CORRECT" if assessment_correct else "❌ INCORRECT"
                print(f"🎯 Assessment Status: {status}")
                
                results.append({
                    'test_case': i,
                    'ai_correct': is_correct,
                    'expected_correct': test_case['should_be_correct'],
                    'assessment_accurate': assessment_correct,
                    'feedback': feedback,
                    'confidence': confidence
                })
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse AI response as JSON: {e}")
                results.append({
                    'test_case': i,
                    'ai_correct': None,
                    'expected_correct': test_case['should_be_correct'],
                    'assessment_accurate': False,
                    'feedback': 'JSON parsing failed',
                    'confidence': 0.0
                })
                
        except Exception as e:
            print(f"❌ Error testing case {i}: {e}")
            results.append({
                'test_case': i,
                'ai_correct': None,
                'expected_correct': test_case['should_be_correct'],
                'assessment_accurate': False,
                'feedback': f'Error: {e}',
                'confidence': 0.0
            })
    
    # Summary
    print("\n" + "=" * 50)
    print("📈 SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    accurate_assessments = sum(1 for r in results if r['assessment_accurate'])
    accuracy_rate = (accurate_assessments / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Accurate Assessments: {accurate_assessments}")
    print(f"Accuracy Rate: {accuracy_rate:.1f}%")
    
    for result in results:
        status = "✅" if result['assessment_accurate'] else "❌"
        print(f"{status} Test {result['test_case']}: AI said {result['ai_correct']}, expected {result['expected_correct']}")
    
    return accuracy_rate >= 75  # Consider success if 75% or higher accuracy

if __name__ == "__main__":
    success = test_ai_answer_evaluation()
    if success:
        print("\n🎉 AI Answer Evaluation System is working correctly!")
    else:
        print("\n⚠️ AI Answer Evaluation System needs improvement.")

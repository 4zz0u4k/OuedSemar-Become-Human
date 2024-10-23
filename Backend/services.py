# services.py
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()

MODEL_TEMP = 0.7
MAX_TURNS = 10
class StoryService:
    def __init__(self):
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=MODEL_TEMP,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        
        # Store current game state
        self.current_story = None
        self.story_ended = False
        self.story_turns = 0
        self.MAX_TURNS = MAX_TURNS  # Maximum story turns before forced ending
        
    def _parse_response(self, response: str) -> Dict:
        """Parse the LLM response into a structured format."""
        response = response.strip()
        
        # Check if this is an ending
        if response.startswith("ENDING:"):
            self.story_ended = True
            return {
                "scenario": response.replace("ENDING:", "").strip(),
                "choices": None,
                "is_ending": True
            }
            
        # Parse regular scenario with choices
        parts = response.split("CHOICES:")
        scenario = parts[0].replace("SCENARIO:", "").strip()
        
        choices = []
        if len(parts) > 1:
            choices_text = parts[1].strip()
            for line in choices_text.split('\n'):
                if line.strip() and any(line.strip().startswith(str(i)) for i in range(1, 4)):
                    choice = line.strip()[2:].strip()  # Remove number and dot
                    choices.append(choice)
        
        return {
            "scenario": scenario,
            "choices": choices,
            "is_ending": False
        }
    
    async def start_new_story(self) -> Dict:
        """Start a new story and return the initial scenario with choices."""
        self.story_ended = False
        self.story_turns = 0
        
        initial_prompt = """You are a crime story generator. Create an engaging opening scenario for a crime story game.
        The scenario should be detailed and offer exactly 3 distinct choices that will affect the story's progression.
        
        Rules:
        1. The story must be crime-related (detective work, investigation, or criminal activity)
        2. Each choice should lead to significantly different potential outcomes
        3. Maintain suspense and intrigue
        4. Some choices might lead to the story ending (success or failure)
        
        Format your response exactly like this:
        SCENARIO: [Your detailed scenario description]
        CHOICES:
        1. [First choice]
        2. [Second choice]
        3. [Third choice]
        
        Make it engaging and morally interesting!"""
        
        response = await self.model.ainvoke(initial_prompt)
        self.current_story = self._parse_response(response.content)
        return self.current_story

    async def make_choice(self, choice_index: int) -> Dict:
        """Process the player's choice and continue the story."""
        if self.story_ended:
            raise ValueError("Story has ended. Start a new game.")
            
        if not self.current_story:
            raise ValueError("No active story. Start a new game.")
            
        if not 1 <= choice_index <= 3:
            raise ValueError("Choice must be between 1 and 3")
            
        self.story_turns += 1
        
        # Force story ending if maximum turns reached
        if self.story_turns >= self.MAX_TURNS:
            ending_prompt = f"""Create a satisfying ending for this crime story:
            Previous scenario: {self.current_story["scenario"]}
            Player chose: {self.current_story["choices"][choice_index - 1]}
            
            Create a final ending that wraps up the story."""
            
            response = await self.model.ainvoke(ending_prompt)
            self.story_ended = True
            return {
                "scenario": response.content.strip(),
                "choices": None,
                "is_ending": True
            }
        
        # Continue story
        continuation_prompt = f"""Continue the following crime story based on the player's choice.

        Previous scenario: {self.current_story["scenario"]}
        Player chose: {self.current_story["choices"][choice_index - 1]}
        
        Generate the next part of the story with exactly 3 new choices.
        Some scenarios can lead to the story ending if it makes narrative sense.
        
        Rules:
        1. Maintain continuity with the previous scenario
        2. Keep the crime/investigation theme
        3. Choices should have meaningful consequences
        4. Consider adding occasional plot twists
        
        If the story should end based on this choice, format your response as:
        ENDING: [Final scenario description]
        
        Otherwise, format your response as:
        SCENARIO: [New scenario description]
        CHOICES:
        1. [First choice]
        2. [Second choice]
        3. [Third choice]"""
        
        response = await self.model.ainvoke(continuation_prompt)
        self.current_story = self._parse_response(response.content)
        return self.current_story


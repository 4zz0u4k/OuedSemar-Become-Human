import os
from typing import List, Dict
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class StoryService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.7)
        self.story_context = {}
        
    def _create_scenario_prompt(self, player_id: str, previous_choice: str = None):
        if previous_choice:
            template = """
            Based on the player's previous choice: {previous_choice}
            Generate a new crime scenario with 3 possible choices.
            Format:
            - Scenario: [detailed crime scenario description]
            - Choices:
              1. [choice 1]
              2. [choice 2]
              3. [choice 3]
            Make it engaging and ensure choices lead to different possible outcomes.
            """
        else:
            template = """
            Generate an initial crime scenario with 3 possible choices.
            You're creating a detective/crime story. The player is a detective.
            Format:
            - Scenario: [detailed crime scenario description]
            - Choices:
              1. [choice 1]
              2. [choice 2]
              3. [choice 3]
            Make it engaging and ensure choices lead to different possible outcomes.
            """
        
        return PromptTemplate(
            template=template,
            input_variables=["previous_choice"] if previous_choice else []
        )

    async def start_new_game(self, player_id: str) -> Dict:
        prompt = self._create_scenario_prompt(player_id)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        response = await chain.arun({})
        self.story_context[player_id] = {
            "current_scenario": response,
            "history": []
        }
        
        return self._parse_scenario(response)
    
    async def make_choice(self, player_id: str, choice: int) -> Dict:
        if player_id not in self.story_context:
            raise ValueError("No active game found for this player")
            
        current_scenario = self.story_context[player_id]["current_scenario"]
        self.story_context[player_id]["history"].append({
            "scenario": current_scenario,
            "choice": choice
        })
        
        prompt = self._create_scenario_prompt(player_id, f"Choice {choice}")
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        response = await chain.arun(previous_choice=f"Choice {choice}")
        self.story_context[player_id]["current_scenario"] = response
        
        return self._parse_scenario(response)
    
    def _parse_scenario(self, response: str) -> Dict:
        # Basic parsing of the LLM response
        lines = response.strip().split('\n')
        scenario = ""
        choices = []
        
        parsing_choices = False
        for line in lines:
            if line.strip().startswith("- Scenario:"):
                scenario = line.replace("- Scenario:", "").strip()
            elif line.strip().startswith("- Choices:"):
                parsing_choices = True
            elif parsing_choices and line.strip().startswith(("1.", "2.", "3.")):
                choice = line.strip()[3:].strip()
                choices.append(choice)
                
        return {
            "scenario": scenario,
            "choices": choices
        }


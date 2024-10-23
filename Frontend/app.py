import streamlit as st
import requests
import json
from typing import Dict

API_BASE_URL = "http://localhost:8000/game"

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'story_started' not in st.session_state:
        st.session_state.story_started = False
    if 'current_scenario' not in st.session_state:
        st.session_state.current_scenario = None
    if 'story_history' not in st.session_state:
        st.session_state.story_history = []
    if 'choice_made' not in st.session_state:
        st.session_state.choice_made = False

def reset_game():
    """Reset the game state"""
    st.session_state.story_started = False
    st.session_state.current_scenario = None
    st.session_state.story_history = []
    st.session_state.choice_made = False

def start_new_game() -> Dict:
    """Start a new game by calling the backend API"""
    try:
        response = requests.post(f"{API_BASE_URL}/start")
        response.raise_for_status()
        scenario = response.json()
        st.session_state.story_started = True
        st.session_state.current_scenario = scenario
        st.session_state.choice_made = False
        return scenario
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to start new game: {str(e)}")
        return None

def make_choice(choice: int) -> Dict:
    """Make a choice by calling the backend API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/choice",
            json={"choice": choice}
        )
        response.raise_for_status()
        next_scenario = response.json()
        
        # Store current scenario in history
        if st.session_state.current_scenario:
            st.session_state.story_history.append({
                "scenario": st.session_state.current_scenario["scenario"],
                "choice_made": st.session_state.current_scenario["choices"][choice - 1]
            })
        
        st.session_state.current_scenario = next_scenario
        st.session_state.choice_made = True
        return next_scenario
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to process choice: {str(e)}")
        return None

def main():
    # Page config
    st.set_page_config(
        page_title="Interactive Crime Story",
        page_icon="🕵️",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("🕵️ Interactive Crime Story")
    st.markdown("---")
    
    # Sidebar with game controls
    with st.sidebar:
        st.title("Game Controls")
        if st.button("Start New Game", use_container_width=True):
            reset_game()
            start_new_game()
    
    # Main game area
    if not st.session_state.story_started:
        st.info("Click 'Start New Game' to begin your crime story adventure!")
    else:
        # Display story history
        if st.session_state.story_history:
            with st.expander("Story So Far", expanded=False):
                for i, history in enumerate(st.session_state.story_history, 1):
                    st.markdown(f"**Chapter {i}**")
                    st.write(history["scenario"])
                    st.markdown(f"*You chose: {history['choice_made']}*")
                    st.markdown("---")
        
        # Display current scenario
        if st.session_state.current_scenario:
            st.markdown("### Current Scenario")
            st.write(st.session_state.current_scenario["scenario"])
            
            # If it's an ending, display it differently
            if st.session_state.current_scenario["is_ending"]:
                st.markdown("---")
                st.success("Story Complete!")
                if st.button("Play Again", use_container_width=True):
                    reset_game()
                    start_new_game()
            else:
                # Display choices with full descriptions
                st.markdown("### Your Choices")
                choices = st.session_state.current_scenario["choices"]
                
                # Create a container for each choice with description
                for i, choice in enumerate(choices, 1):
                    with st.container():
                        st.markdown(f"**Choice {i}:**")
                        # Create two columns - one for description, one for button
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"*{choice}*")
                        with col2:
                            if st.button(
                                f"Select #{i}",
                                key=f"choice_{i}",
                                use_container_width=True,
                                disabled=st.session_state.choice_made
                            ):
                                make_choice(i)
                        st.markdown("---")
                
                # Display selected choice
                if st.session_state.choice_made:
                    st.button("Continue", use_container_width=True, on_click=lambda: setattr(st.session_state, 'choice_made', False))

if __name__ == "__main__":
    main()
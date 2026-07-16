from react_agent.LLM import RequestLLM
from react_agent.agent import ReactAgent
from react_agent.tools import tools_registry
import tools
import argparse

def exit_function():
    """Cleanup function executed upon program exit"""
    print("\nProgram is exiting, performing cleanup operations (e.g., returning robot arm to home position)...")
    # Add code here to return the robot arm to its home position
    print("Cleanup complete. Program exited.")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='React Agent with command-line input')
    parser.add_argument('user_input', nargs='*', 
                       help='User input content, multiple words will be combined into one sentence')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Interactive mode, ignore command line input and wait for user input')
    return parser.parse_args()

if __name__ == "__main__":
    # Parse command line arguments
    args = parse_arguments()
    
    # 1. Instantiate agent
    llm = RequestLLM(base_url="https://prodsvc.educg.net/deepseek/v1/", model_name="deepseek")
    agent = ReactAgent(llm)
    
    # 2. Register tools
    for name, cls in tools_registry.items():
        agent.register_tool(name, cls)
    
    # 3. Update system prompt
    agent.update_system_message()
    
    try:
        # If command line input is provided and it's not interactive mode
        if args.user_input and not args.interactive:
            # Combine command line arguments into one sentence
            user_input = ' '.join(args.user_input)
            print(f"<USER>: {user_input}")
            agent.chat(user_input)
        else:
            # Original logic for interactive mode or when no command line input is provided
            print("Entering interactive mode...")
            while True:
                user_input = input("<USER>:")
                agent.chat(user_input)
    finally:
        exit_function()

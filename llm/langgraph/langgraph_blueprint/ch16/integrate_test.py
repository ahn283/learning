def generate_code(state:dict) -> dict:
    """ 
    Generates a Python function based on the prompt.
    """
    if 'factorial' in state['prompt']:
        state['generated_code'] = "def factorial(n): return 1 if n==0 else x * factorial(n-1)"
    else:
        state['generated_code'] = "Unknown function requested."
    return state

def analyze_code(state: dict) -> dict:
    """ 
    Analyzes the generated code for improvments.
    """
    if 'for i in range(len(' in state['generated_code']:
        state['suggestion'] = "Consider using enumerate() for better readability."
    else:
        state['suggestion'] = "Code looks good."
    return state
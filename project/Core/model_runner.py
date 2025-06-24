import openai
import time

def run_llm_model(model: str, prompt: str, max_retries: int = 3, temp = 0.2):
    """
    Calls the OpenAI ChatCompletion API with retry logic and returns output + execution time.
    
    Args:
        model (str): The OpenAI model name (e.g., "gpt-4", "gpt-3.5-turbo").
        prompt (str): Prompt text to send to the LLM.
        max_retries (int): Number of retry attempts on failure.

    Returns:
        Tuple[str, float]: (LLM-generated response, execution time in seconds)
    """
    for attempt in range(max_retries):
        try:
            start_time = time.time()
            
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant that answers in clean and precise JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=1000  
            )
            
            execution_time = time.time() - start_time
            content = response['choices'][0]['message']['content'].strip()
            
            return content, execution_time

        except openai.error.OpenAIError as e:
            if attempt == max_retries - 1:
                print(f"[ERROR] Failed after {max_retries} attempts: {e}")
                return "", 0.0

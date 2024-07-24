import os
import argparse
from together import Together

def chat_with_model(prompt):
    # Ensure the API key is set
    if not os.environ.get('TOGETHER_API_KEY'):
        raise EnvironmentError("API key not found. Please set the TOGETHER_API_KEY environment variable.")

    # Initialize the Together client
    client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))

    # Make the request
    response_generator = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        messages=[{"role": "user", "content": prompt}],  # Use the prompt argument
        max_tokens=512,
        temperature=0.7,
        top_p=0.7,
        top_k=50,
        repetition_penalty=1,
        stop=["\n\n"],
        stream=True
    )

    # Collect and print the response
    output = ""
    for response in response_generator:
        if hasattr(response, 'choices') and response.choices:
            for choice in response.choices:
                if hasattr(choice, 'delta') and hasattr(choice.delta, 'content'):
                    output += choice.delta.content

    return output

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chat with LLaMA 405 API via Together")
    parser.add_argument("prompt", type=str, help="The prompt to send to the model")
    args = parser.parse_args()

    output = chat_with_model(args.prompt)
    print(output)  # Print only the output
import os
import traceback

from dataclasses import dataclass
from openai import OpenAI
from retry import retry
from typing import Dict, List, Optional, Union

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    raise ValueError(f"Missing API key for {provider}. Set {env_var} environment variable.")

class Conversation:
    def __init__(self, model: str):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        self.model = model
        self.history = []
        self.latest_response = None

    @retry(tries=2, delay=5, backoff=2)
    def message(self, msg: str, print_history=False):
        messages = self.history
        response = None
        messages.append(
            {
                "role": "user",
                "content": msg,
            },
        )
        if print_history:
            print(f'\n\nHistory:\n\n{self.history}\n\n')
        try:
            completion = self.client.chat.completions.create(
                extra_headers={},
                model=self.model,
                messages=messages,
                temperature=0,
                timeout=60,
            )
            response = completion.choices[0].message.content
            self.history.append(
                {
                    "role": "assistant",
                    "content": response,
                },
            )
            return response
        except Exception as e:
            print(f'ERROR CALLING API!\n\n{e}')
            print(f'Full response: {response}')
            print('Stack trace:')
            util.output(transcript, traceback.format_exc())
            raise(e)


if __name__ == '__main__':
    conversation = Conversation('google/gemma-2-9b-it:free')
    response = conversation.message('Hi! What\'s the capital of London?')
    print(f'response: {response}')

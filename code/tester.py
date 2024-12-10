import json
import prompts
import re

from api import Conversation
from retry import retry
from typing import Dict, List, Optional, Union

class Test:
    def __init__(self,
                 rule: str,
                 example: List[int],
                 test_model: str,
                 initial_prompt=prompts.initial_prompt,
                 analysis_prompt=prompts.analysis_prompt,
                 judgment_prompt=prompts.judgment_prompt,
                 analysis_model='anthropic/claude-3.5-haiku',
                 ):
        self.rule = rule
        self.example = example
        self.test_model = test_model
        self.analysis_model = analysis_model
        self.initial_prompt = initial_prompt
        self.analysis_prompt = analysis_prompt
        self.judgment_prompt = judgment_prompt

    def analyze_test_cases(self, test_cases: str):
        convo = Conversation(self.analysis_model)
        prompt = self.analysis_prompt.format(rule=self.rule, test_cases=test_cases)
        # print(f'\nAnalysis prompt: {prompt}\n')
        response = convo.message(prompt)
        print(f"\nAnalysis response from model: {response}\n")
        response = re.sub(r'.*<response>(.*?)</response>.*',
                          r'\1', response, flags=re.DOTALL)
        # print(f'Shrunken analysis response from model: {response}')
        return response

    def parse_response(self, response: str):
        # TODO error handling
        # TODO in particular, initial check that response is not None which it will be if
        #      the API is down or times out.
        parsed = json.loads(response)
        final_hypothesis = parsed.get('final_hypothesis')
        test_cases = parsed.get('test_cases')
        print(f'\nResponse {response}\n')
        return final_hypothesis, test_cases

    def judge_hypothesis(self, model_hypothesis):
        # TODO
        convo = Conversation(self.analysis_model)
        real_rule = self.rule
        prompt = self.judgment_prompt.format(real_rule=real_rule, model_hypothesis=model_hypothesis)
        print(f'\nFinal judgment prompt: {prompt}\n')
        response = convo.message(prompt)
        return json.loads(response) #  TODO error handling

    def run(self):
        convo = Conversation(self.test_model)
        turns = 0
        total_turns = 20
        judgment = None
        prompt = self.initial_prompt.format(example=self.example)
        print(f'\nInitial prompt: {prompt}\n')
        while turns < total_turns:
            try:
                # send the problem to the model
                response = convo.message(prompt, print_history=False)
                # parse the response
                final_hypothesis, test_cases = self.parse_response(response)
                # if the model is done, judge its hypothesis & return
                if final_hypothesis:
                    judgment = self.judge_hypothesis(final_hypothesis)
                    break
                # analyze whether its test cases are correct.
                prompt = self.analyze_test_cases(test_cases)
                # print(f'\nAnalysis response: {prompt}\n\n')
                # loop up to total_turns
                turns += 1
            except Exception as e:
                print(f'\nError in run()! {e}\n')
        if not final_hypothesis:
            # model has failed to guess; it fails.
            return {'judgment': False, 'explanation': 'Ran out of turns.'}, turns
        # TODO
        # Save & return results
        return judgment, turns


if __name__ == '__main__':
    rule = 'Differences between successive members of the list are alternately positive and negative (so for example [6, 3, 5, 3, 17, 2, 8, 5] would match the rule).'
    example = [22, 17, 19, 9, 12]
    test_model = 'anthropic/claude-3.5-sonnet:beta'
    test = Test(rule, example, test_model)
    judgment, turns = test.run()
    print(judgment)
    print(f'\n\nRule was: {rule}')
    print(f'Did model succeed? {judgment["judgment"]}')
    print(f'Model took {turns} turns.')
    print('\n\n')

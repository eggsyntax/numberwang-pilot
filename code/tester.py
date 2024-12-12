import code #  XXX
import json
import prompts
import re
import traceback
import util

from api import Conversation
from datetime import date
from operator import itemgetter
from retry import retry
from rules_and_models import * # just data structures, no code
from typing import Dict, List, Optional, Union
from util import save_transcript, output

debug = True
output_directory = '../transcripts/phase-1/'

class Test:
    def __init__(self,
                 rule: str,
                 example: List[int],
                 test_model: str,
                 initial_prompt=prompts.initial_prompt,
                 analysis_prompt=prompts.analysis_prompt,
                 judgment_prompt=prompts.judgment_prompt,
                 analysis_model='anthropic/claude-3.5-sonnet-beta',
                 transcript='',
                 ):
        self.rule = rule
        self.example = example
        self.test_model = test_model
        self.analysis_model = analysis_model
        self.initial_prompt = initial_prompt
        self.analysis_prompt = analysis_prompt
        self.judgment_prompt = judgment_prompt
        self.transcript = transcript

    def output(self, input_str: str):
        self.transcript = util.output(self.transcript, input_str)

    def analyze_test_cases(self, test_cases: str):
        convo = Conversation(self.analysis_model)
        prompt = self.analysis_prompt.format(rule=self.rule, test_cases=test_cases)
        # self.output(f'\nAnalysis prompt: {prompt}\n')
        response = convo.message(prompt)
        response = re.sub(r'.*<response>(.*?)</response>.*',
                          r'\1', response, flags=re.DOTALL)
        self.output(f"\nAnalysis response from model: {response}\n")
        return response

    def parse_response(self, response: str):
        try:
            # GPT-4o wraps its response in markdown, strip that out if present:
            response = re.sub(r'^```json\n?(.*)\n?```$', r'\1', response.strip(), flags=re.DOTALL)
            parsed = json.loads(response)
        except Exception as e:
            print(f'Failed to parse this response: {response}')
            print(f'Got error {e}')
            raise
        final_hypothesis = parsed.get('final_hypothesis')
        test_cases = parsed.get('test_cases')
        # self.output(f'\nResponse {response}\n')
        return final_hypothesis, test_cases

    def judge_hypothesis(self, model_hypothesis):
        convo = Conversation(self.analysis_model)
        real_rule = self.rule
        prompt = self.judgment_prompt.format(real_rule=real_rule, model_hypothesis=model_hypothesis)
        self.output(f'\nFinal judgment prompt: {prompt}\n')
        response = convo.message(prompt)
        return json.loads(response)

    def run(self):
        convo = Conversation(self.test_model)
        turns = 0
        total_turns = 20
        judgment = None
        prompt = self.initial_prompt.format(example=self.example)
        self.output('\n------------------------------------------------------------\n')
        self.output(f'Rule: {self.rule}')
        self.output(f'Model: {self.test_model}')
        self.output(f'Date: {date.today()}\n')
        self.output(f'Initial prompt: {prompt}\n\n')
        exception_count = 0  # Add this counter outside the while loop
        while turns < total_turns:
            try:
                self.output(f'Turn number {turns+1}')
                # send the problem to the model
                response = convo.message(prompt, print_history=False)
                self.output(response)
                # parse the response
                final_hypothesis, test_cases = self.parse_response(response)
                # if the model is done, judge its hypothesis & return
                if final_hypothesis:
                    judgment = self.judge_hypothesis(final_hypothesis)
                    break
                # analyze whether its test cases are correct.
                prompt = self.analyze_test_cases(test_cases)
                # self.output(f'\nAnalysis response: {prompt}\n\n')
                # loop up to total_turns
                turns += 1
                # code.interact(local=locals()) #  XXX
            except Exception as e:
                exception_count += 1
                if exception_count >= 3:
                    traceback.print_exc()
                    raise
                self.output(f'\nError number {exception_count} in run()! {e}\n')
        if not final_hypothesis:
            # model has failed to guess; it fails.
            return {'judgment': False, 'explanation': 'Ran out of turns.'}, turns
        # TODO
        # Save & return results
        return judgment, turns, self.transcript


if __name__ == '__main__':
    test_rules = rules_phase1[:2] #  TODO
    test_models = phase1_models[:3] #  TODO
    for test_model in test_models:
        successful_rules = []
        for test_rule in test_rules[:2]:
            rule, short_rule, example = itemgetter('rule', 'short_rule', 'example')(test_rule)
            test = Test(rule, example, test_model)
            try:
                judgment, turns, transcript = test.run()
                if judgment['judgment']:
                    successful_rules.append(short_rule)
            except Exception as e:
                util.output(transcript, f"Sorry, couldn't make it work with {test_model} after 3 tries. Moving on to next model!")
                traceback.print_exc()
                continue
            transcript = util.output(transcript, judgment)
            transcript = util.output(transcript, f'\n\nRule was: {rule}')
            transcript = util.output(transcript, f'Did model succeed? {judgment["judgment"]}')
            transcript = util.output(transcript, f'Model took {turns} turns.')
            transcript = util.output(transcript, '\n\n')
            save_transcript(transcript, short_rule, test_model, judgment['judgment'], output_directory)
            print('\n\n\n\n')

        print(f'For model: {test_model}')
        print(f'Rules where {test_model} succeeded: {successful_rules}')
        print(f'Rules where {test_model} failed: {[r["short_rule"] for r in test_rules if r["short_rule"] not in successful_rules]}')
        print(f'Success rate: {len(successful_rules) / len(test_rules)}')
        print('\n\n\n')

import code #  XXX
import json
import prompts
import re
import traceback
import util

from api import Conversation
from datetime import datetime
from operator import itemgetter
from retry import retry
from rules_and_models import * # just data structures, no code
from typing import Dict, List, Optional, Union
from util import save_transcript, output, print_and_save_summary

debug = True
output_directory = '../transcripts/phase-1/'

class Test:
    def __init__(self,
                 rule: str,
                 examples: List[List[int]],
                 test_model: str,
                 initial_prompt=prompts.initial_prompt,
                 analysis_prompt=prompts.analysis_prompt,
                 judgment_prompt=prompts.judgment_prompt,
                 analysis_model='anthropic/claude-3.5-sonnet-beta',
                 transcript='',
                 ):
        self.rule = rule
        self.examples = examples
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
        response = re.sub(r'.*<response>(.*)',
                          r'\1', response, flags=re.DOTALL)
        # GPT-4o wraps its response in markdown, strip that out if present:
        response = re.sub(r'^```json\n?(.*)\n?```$', r'\1', response.strip(), flags=re.DOTALL)
        parsed = json.loads(response)
        final_hypothesis = parsed.get('final_hypothesis')
        test_cases = parsed.get('test_cases')
        # self.output(f'\nResponse {response}\n')
        return final_hypothesis, test_cases

    def judge_final_hypothesis(self, model_hypothesis):
        self.output(f'Requesting final judgment.')
        judgments = []
        # Use majority-of-3 because occasionally one is wrong
        for _ in range(3):
            convo = Conversation(self.analysis_model)
            real_rule = self.rule
            self.output(f'Real rule:  {real_rule}')
            self.output(f'Model rule: {model_hypothesis}')
            prompt = self.judgment_prompt.format(real_rule=real_rule, model_hypothesis=model_hypothesis)
            # self.output(f'\nFinal judgment prompt: {prompt}\n')
            response = convo.message(prompt)
            judgments.append(json.loads(response))
        true_judgments = [j for j in judgments if j.judgment]
        if len( true_judgments ) >= 2:
            return true_judgments[0]
        else:
            false_judgments = [j for j in judgments if j not in true_judgments]
            return false_judgments[0]

    # TODO use @retry here?
    def run(self):
        convo = Conversation(self.test_model)
        turns = 0
        total_turns = 20
        judgment = None
        final_hypothesis = None
        examples = '\n'.join([str(example) for example in self.examples])
        prompt = self.initial_prompt.format(examples=examples)
        self.output('\n------------------------------------------------------------\n')
        self.output(f'Rule: {self.rule}')
        self.output(f'Model: {self.test_model}')
        self.output(f'Date: {datetime.now()}\n')
        self.output(f'Initial prompt: {prompt}\n\n')
        exception_count = 0
        while turns < total_turns:
            try:
                self.output(f'Turn number {turns+1}')
                # send the problem to the model
                response = convo.message(prompt, print_history=False)
                self.output(response)
                # parse the response
                try:
                    final_hypothesis, test_cases = self.parse_response(response)
                except Exception as e:
                    print(f'Failed to parse this response: {response}')
                    print(f'Got error {e}')
                    print('Removing last response from history and trying again.')
                    convo.history = convo.history[:-1]
                    raise # for error counting
                # if the model is done, judge its hypothesis & return
                if final_hypothesis:
                    judgment = self.judge_final_hypothesis(final_hypothesis)
                    break
                # analyze whether its test cases are correct.
                prompt = self.analyze_test_cases(test_cases)
                if prompt is None:
                    prompt = "I'm sorry, I couldn't get an analysis of your test cases, please try again."
                # self.output(f'\nAnalysis response: {prompt}\n\n')
                # loop up to total_turns
                turns += 1
                # code.interact(local=locals()) #  XXX
            except Exception as e:
                exception_count += 1
                print(f'Error number {exception_count}.')
                if exception_count >= 3:
                    print("\n\nSorry, we just totally can't recover here.\n")
                    traceback.print_exc()
                    print("\n\n\n")
                    return {'judgment': False, 'explanation': f'Irrecoverable errors'}, -1, self.transcript
                self.output(f'\nError number {exception_count} in run()! {e}\n')
                continue
        if not final_hypothesis:
            # model has failed to guess; it fails.
            return {'judgment': False, 'explanation': 'Ran out of turns.'}, turns, self.transcript
        # Save & return results
        return judgment, turns, self.transcript

if __name__ == '__main__':
    test_rules = rules_phase1[:] #  TODO
    test_models = phase1_models[1:3] #  TODO
    for test_model in test_models:
        try:
            successful_rules = []
            turns_per_problem = []
            for test_rule in test_rules[:]:
                rule, short_rule, examples = itemgetter('rule', 'short_rule', 'examples')(test_rule)
                test = Test(rule, examples, test_model)
                transcript = ""
                try:
                    judgment, turns, transcript = test.run()
                    if judgment['judgment']:
                        successful_rules.append(short_rule)
                    turns_per_problem.append(turns)
                except Exception as e:
                    util.output(transcript, f"Sorry, couldn't make it work with {test_model} after 3 tries. Moving on to next model!")
                    traceback.print_exc()
                    continue
                transcript = util.output(transcript, judgment)
                transcript = util.output(transcript, f'\n\nRule was: {rule}')
                transcript = util.output(transcript, f'Did {test_model} succeed? {judgment["judgment"]}')
                transcript = util.output(transcript, f'Model took {turns} turns.')
                transcript = util.output(transcript, '\n\n')
                save_transcript(transcript, short_rule, test_model, judgment['judgment'], output_directory)
                print('\n\n\n\n')
        except Exception as e:
            print('Hit the last ditch exception for {test_model}. Skipping this model entirely.')
            continue

        failed_rules = [r["short_rule"] for r in test_rules if r["short_rule"] not in successful_rules]
        print_and_save_summary(test_model, successful_rules, failed_rules, turns_per_problem, output_directory)

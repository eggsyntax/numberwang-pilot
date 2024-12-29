import csv
import glob
import os
import re

from datetime import date, datetime

def save_transcript(transcript: str, rule: str, model: str, success: bool, directory) -> None:
   """
   Save a transcript file with a filename built from the rule, model, and success status.
   Automatically versions the file (v01, v02, etc.) if previous versions exist.

   Args:
       rule (str): The rule name
       model (str): The model name
       success (bool): Whether the attempt was successful
       transcript (str): The content to save in the file
   """
   def clean_string(s: str) -> str:
       s = s.lower()
       s = s.replace(' ', '-')
       s = re.sub(r'[^a-z0-9\.-]', '', s)
       return s
   rule_clean = clean_string(rule)
   model_clean = clean_string(model)
   success_str = "success" if success else "failure"
   directory = "../transcripts/phase-2"
   os.makedirs(directory, exist_ok=True)
   base_pattern = os.path.join(directory, f"{rule_clean}.{model_clean}.{success_str}.v*.txt")
   existing_files = glob.glob(base_pattern)
   if not existing_files:
       next_version = 1
   else:
       version_numbers = []
       for file in existing_files:
           try:
               version_str = file.split('.v')[-1].replace('.txt', '')
               version_numbers.append(int(version_str))
           except (ValueError, IndexError):
               continue
       next_version = max(version_numbers, default=0) + 1
   filename = f"{rule_clean}.{model_clean}.{date.today()}.{success_str}.v{next_version:02d}.txt"
   filepath = os.path.join(directory, filename)
   with open(filepath, 'w') as f:
       f.write(transcript)

def output(transcript, input_str, debug=True):
    if debug:
        print("\n" + str(input_str))
    return transcript + "\n" + str(input_str)

def save_result_to_csv(test_model, short_rule, difficulty, judgment, turns, directory):
    filename = f'{directory}results.csv'
    with open(filename, "a") as f:
        line = [test_model, short_rule, difficulty, judgment, turns, date.today()]
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(line)

def print_and_save_summary(test_model, successful_rules, failed_rules, turns_per_problem, directory):
    lines = [
        f'For model: {test_model} at {datetime.now()}',
        f'Rules where {test_model} succeeded: {successful_rules}',
        f'Rules where {test_model} failed: {failed_rules}',
        f'Number of turns: {turns_per_problem}',
        f'Success rate: {len(successful_rules) / (len(successful_rules) + len(failed_rules))}',
        '\n\n\n',
    ]
    filename = f'{directory}summary.txt'
    with open(filename, "a") as f:
        for line in lines:
            print(line)
            f.write(f'{line}\n\n')

import glob
import os
import re

# def save_transcript(transcript: str, rule: str, model: str, success: bool, directory='../transcripts/phase-1/') -> None:
    # """
    # Save a transcript file with a filename built from the rule, model, and success status.
#
    # Args:
        # rule (str): The rule name
        # model (str): The model name
        # success (bool): Whether the attempt was successful
        # transcript (str): The content to save in the file
    # """
    # # Clean and format the strings for filename use
    # def clean_string(s: str) -> str:
        # # Convert to lowercase, replace spaces with hyphens
        # # Remove any characters that aren't alphanumeric, hyphens, or dots
        # import re
        # s = s.lower()
        # s = s.replace(' ', '-')
        # s = re.sub(r'[^a-z0-9\.-]', '', s)
        # return s
    # # Create cleaned versions of the strings
    # rule_clean = clean_string(rule)
    # model_clean = clean_string(model)
    # success_str = "success" if success else "failure"
    # # Construct the filename
    # filename = f"{rule_clean}.{model_clean}.{success_str}.txt"
    # # Ensure the directory exists
    # os.makedirs(directory, exist_ok=True)
    # # Create the full path
    # filepath = os.path.join(directory, filename)
    # # Write the transcript to the file
    # with open(filepath, 'w') as f:
        # f.write(transcript)

def save_transcript(transcript: str, rule: str, model: str, success: bool, directory='../transcripts/phase-1/') -> None:
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
   directory = "../transcripts/phase-1"
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
   filename = f"{rule_clean}.{model_clean}.{success_str}.v{next_version:02d}.txt"
   filepath = os.path.join(directory, filename)
   with open(filepath, 'w') as f:
       f.write(transcript)

def output(transcript, input_str, debug=True):
    if debug:
        print("\n" + str(input_str))
    return transcript + "\n" + str(input_str)

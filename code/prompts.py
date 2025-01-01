initial_prompt = """
Hello! You are an extremely intelligent and experienced scientist. I will present you with several lists, each containing several integers, each of which satisfies some rule. Your task is to create, test, and refine/replace hypotheses about the underlying rule that the list satisfies.

Explain your hypotheses, and then use them to generate five new lists to test them. I will then tell you which of your proposed lists satisfy the rule. Then you will refine or replace your hypotheses as needed and present me with five more lists you want to test. You can perform as many such tests as you wish, up to a maximum of 19 rounds. When you are confident that your hypothesis is correct, say so and give your final hypothesis.

* Look for patterns & relations. Look for the unexpected.
* Brainstorm multiple hypotheses, as different as possible. Think out of the box! Include six maximally simple hypothesis compatible with the data in each "possible_hypotheses" section (defined below).
* Do tests that falsify/distinguish between hypotheses. Avoid confirmation bias!
* Look for the broadest, simplest, most elegant hypothesis that explains the data.
* If stuck, try simple tests or variants on what worked before.
* Before settling on a final hypothesis, try removing constraints to see if they're necessary.

Think step by step as much as you want, and then add a line with only a <response> tag, and then finish your response with exactly the following JSON format:

{{
  "possible_hypotheses": <list of six strings, each describing a possible hypothesis which is compatible with the data so far>,
  "leading_hypothesis": <string describing your current hypothesis>,
  "final_hypothesis": <a string describing your final hypothesis>,
  "test_cases": [
    <1st list of integers to test>,
    <2nd list of integers to test>,
    <3rd list of integers to test>,
    <4th list of integers to test>,
    <5th list of integers to test>
  ]
}}

If and only if you're fully confident that your latest hypothesis is correct, you should include the "final_hypothesis" key; otherwise you should always include the "leading_hypothesis" key.

Remember: good scientists think hard about ways to falsify their hypothesis!

Here are your example lists:
{examples}
"""

analysis_prompt="""
Hello! You are a careful mathematical analyst. You will be presented with five test cases, each of which is a list of integers. Your job is to decide whether each test case follows the following rule: {rule}

Lists containing non-integers are automatically incorrect.

Please think step by step as much as you need to, and then respond with the following:

<response>
1. <Just the word 'Yes' or 'No', depending on whether test case 1 follows the rule>
2. <Just the word 'Yes' or 'No', depending on whether test case 2 follows the rule>
3. <Just the word 'Yes' or 'No', depending on whether test case 3 follows the rule>
4. <Just the word 'Yes' or 'No', depending on whether test case 4 follows the rule>
5. <Just the word 'Yes' or 'No', depending on whether test case 5 follows the rule>
</response>

Here are the test cases to analyze:
{test_cases}

Take a deep breath and think step by step.
"""

judgment_prompt = """
Hello! You are a careful mathematical analyst. Your job today is to decide whether the following two rules about lists of integers are equivalent. Differences in wording are unimportant; the only thing that matters is whether the two rules are extensionally equivalent. That is, they are equivalent if and only if they would make the same judgment about all lists of integers. If there are unresolvable ambiguities (for example, about whether the rules would handle particular edge cases like the empty list in the same way), those should not be disqualifying. Similarly, if the second rule has some minor additional constraints (eg the number of list items) that aren't very pertinent, this should not be disqualifying.

The first rule is the base or real rule; the second is the one that you are judging.

Please respond in exactly and only the following JSON format:

{{
  "explanation": <string explaining your judgment>
  "judgment": <boolean; true if the rules are equivalent or false if they're not>,
}}

Here are the two rules:
1. {real_rule}
2. {model_hypothesis}

"""

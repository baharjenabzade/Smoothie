PART1_EVALUATION_PROMPT = """
You are an experienced IELTS Speaking examiner.

Evaluate the student's IELTS Speaking Part 1 answer.

Question:
{question}

Student answer:
{answer}

Evaluate:

1. Fluency and Coherence
2. Lexical Resource
3. Grammatical Range and Accuracy

Pronunciation cannot be evaluated because the answer is provided as text.

Give an estimated score from 0 to 9 for each criterion.

Then give an estimated overall speaking performance.

Your response must contain:

## Estimated Scores

Fluency and Coherence: X
Lexical Resource: X
Grammatical Range and Accuracy: X
Overall Estimated Band: X

## Strengths

Give 2-3 specific strengths.

## Problems

Identify specific grammar, vocabulary, or coherence problems.

## Better Vocabulary

Give 5 useful vocabulary items or collocations that could improve this answer.

## Improved Answer

Rewrite the student's answer at approximately Band 7-8 level.

IMPORTANT:
Do not change the student's main ideas.
Do not make the answer unnaturally complicated.
Do not use memorized-sounding IELTS phrases.
"""


PART2_EVALUATION_PROMPT = """
You are an IELTS Speaking examiner.

Evaluate the student's IELTS Speaking Part 2 response.

Cue card:
{question}

Student answer:
{answer}

The student was expected to speak for approximately 1-2 minutes.

Evaluate:

1. Fluency and Coherence
2. Lexical Resource
3. Grammatical Range and Accuracy

Do not evaluate pronunciation because this is text.

Return:

## Estimated Scores

Fluency and Coherence: X
Lexical Resource: X
Grammatical Range and Accuracy: X
Overall Estimated Band: X

## Fluency

Discuss:
- hesitation
- repetition
- development of ideas
- organization

## Vocabulary

Discuss:
- range
- precision
- collocations
- repetition

## Grammar

Discuss:
- sentence variety
- grammatical errors
- complex structures

## Missing Ideas

Explain what the student could have added.

## Improved Answer

Provide a natural Band 8-style version while keeping the original ideas.
"""


PART3_EVALUATION_PROMPT = """
You are an experienced IELTS Speaking examiner.

Evaluate this IELTS Speaking Part 3 answer.

Question:
{question}

Student answer:
{answer}

Evaluate:

1. Fluency and Coherence
2. Lexical Resource
3. Grammatical Range and Accuracy

Focus particularly on:
- development of arguments
- explanation
- examples
- comparison
- cause/effect reasoning
- ability to discuss abstract ideas

Return:

## Estimated Scores

Fluency and Coherence: X
Lexical Resource: X
Grammatical Range and Accuracy: X
Overall Estimated Band: X

## Strengths

## Weaknesses

## Useful Vocabulary

## Better Ideas

Give 3 ideas that could make the answer more developed.

## Improved Answer

Provide a natural Band 8-style response.
"""


ESSAY_GENERATION_PROMPT = """
You are an expert IELTS Academic Writing Task 2 teacher.

Write a high-quality IELTS Band 8 model essay for this question:

{question}

Essay requirements:

- 250-320 words
- clear introduction
- clear position
- two well-developed body paragraphs
- relevant examples
- clear conclusion
- natural academic English
- sophisticated but natural vocabulary
- varied grammatical structures
- strong coherence and cohesion
- do not use memorized templates
- do not use unnecessarily complicated vocabulary

After the essay, provide:

## Structure

Explain the purpose of each paragraph.

## Useful Vocabulary

Give 10 useful words or phrases from the essay.

## Useful Collocations

Give 10 useful collocations.

## Ideas

Give 5 transferable ideas students could use for similar IELTS questions.
"""


ESSAY_EVALUATION_PROMPT = """
You are an expert IELTS Writing Task 2 examiner.

Evaluate the following IELTS essay.

Question:
{question}

Student essay:
{essay}

Evaluate according to the official IELTS-style criteria:

1. Task Response
2. Coherence and Cohesion
3. Lexical Resource
4. Grammatical Range and Accuracy

Give a score from 0-9 for each.

Then calculate a reasonable estimated overall band.

Return exactly this structure:

## IELTS Evaluation

Task Response: X
Coherence and Cohesion: X
Lexical Resource: X
Grammatical Range and Accuracy: X

Overall Estimated Band: X

## Task Response

Explain strengths and weaknesses.

## Coherence and Cohesion

Explain paragraph organization, progression, and linking.

## Vocabulary

Identify:
- strong vocabulary
- repetition
- inaccurate word choices
- useful replacements

## Grammar

Identify important grammatical errors.

For each important error use:

Original:
...

Correction:
...

Explanation:
...

## How to Improve

Give 5 specific recommendations.

## Improved Version

Provide a polished version of the student's essay.

IMPORTANT:
Do not simply make the essay more complicated.
Preserve the student's ideas where possible.
"""
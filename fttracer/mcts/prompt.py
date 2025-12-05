# ===========================================================
# ================   1.prompt_image_judge   ===================
# ===========================================================


def prompt_image_judge(contextual_information="None"):
    return f"""Core Task: Determine whether the target image meets the criteria based on a set of basic requirements.

    1. Background & Objectives:

    - Here are six capability levels of financial knowledge and image understanding:
      * level 1: Perception (identifying chart basic elements)
      * level 2: Data extraction (reading and reporting explicit values or facts directly shown in the chart)
      * level 3: Calculation analysis (computing metrics based on the chart)
      * level 4: Pattern recognition (identifying observable trends, comparisons, or groupings visible in the data)
      * level 5: Logical reasoning (deriving relationships based on the chart)
      * level 6: Decision support (making decisions involving financial knowledge)

    2. Image Description:

    Below is the information extracted from the contextual text surrounding the image's location within the financial document. 
    - Contextual information:
    ******
    {contextual_information}
    ******

    3. Basic Requirements for the Target Image  
    (1) The basic elements of the image are lines, or parts of it consist of lines, or some parts can be abstracted as lines.  
    (2) The lines in the image exhibit certain relationships, whether simple or complex.  
    (3) The image reflects financial-related issues, whether simple or complex, and can demonstrate trends or changes, such as:  
       - Price, trading volume, or other factors of financial assets (stocks, funds, futures, derivatives, digital/cryptocurrencies, precious metals, forex, real estate, collectibles, auction items, non-performing assets, etc.).  
       - Abstract analysis of financial issues.  
       - Structural or developmental changes in the broader financial field or its subfields.  
       - The impact of financial assets or financial aspects on other fields (macro or micro).  
       - The influence of other fields (macro or micro) on financial assets or financial aspects.  
    (4) The image can be clear or somewhat unclear, in color or black-and-white, but must be discernible to a normal person in terms of basic elements or composition.  
    (5) The image can be standalone or a combination of multiple images.  
    (6) The image should not have obvious errors or missing parts.  
    (7) Ideally, the image should include explanations, analysis, or can be abstracted into test questions.  
    (8) Labels or annotations on the image should be in mainstream languages (English or Chinese preferred, but Spanish, Arabic, French, Russian, German, Japanese, Korean, Italian, etc., are also acceptable).  

    4. Specific Task  
    Determine whether the image meets the above requirements.  

    5. Output Content  
    Judge whether the image complies with the basic requirements and output one of the following levels: ["1","2","3","4","5"], where "5" means fully compliant and "1" means non-compliant.  

    6. Strictly Follow the Output Format (JSON)  
    {{
        "is_compliant": "yes/no",
        "compliance_level": "1-5"
    }}

    7. Examples
    If the image fully meets the requirements, output:
    {{
        "is_compliant": "yes",
        "compliance_level": "5"
    }}
    If the image does not meet the requirements at all, output:
    {{
        "is_compliant": "no",
        "compliance_level": "1"
    }}"""


# ===========================================================
# ===============   2.prompt_fq_generate   ====================
# ===========================================================


def prompt_fq_generate(
    contextual_information="None", existing_final_questions="""{"None":"None"}"""
):
    return f"""Generate a "final question" for the financial image understanding based on the following comprehensive guidelines:

    1. Background & Objectives:
    - A logical chain of questions progresses from basic perception to decision support, with the final question serving as its endpoint.
    - Here are six capability levels of financial knowledge and image understanding:
      * level 1: Perception (identifying chart basic elements)
      * level 2: Data extraction (reading and reporting explicit values or facts directly shown in the chart)
      * level 3: Calculation analysis (computing metrics based on the chart)
      * level 4: Pattern recognition (identifying observable trends, comparisons, or groupings visible in the data)
      * level 5: Logical reasoning (deriving using financial logic or theorems)
      * level 6: Decision support (making decisions involving financial knowledge)
    - Level of the final question must be 6: Decision support.

    2. Image Background(******xxxxxxx******):
    ******
    {contextual_information}
    ******
    
    3. Core Requirements:
    - The final question must be objective (must be single-choice and there must be only one correct choice).
    - The final question should be related to finance.
    - The question must be related to the image and it can't be answered without the image.
    - The answer to this final question must be unambiguous and verifiable.
    - The answer to this final question must be obtained through step-by-step progressive reasoning. 
    - The answer to this final question must only depend on the analysis of the image. 
    - Don't mention the "contextual information" in the question.
    - The capability level must be 6: Decision support.
    - The language of all output content must strictly be limited to English.
    - The number of words in the question should be between 10-500.

    4. Output Format (JSON):
    {{
      "question": "",
      "options": {{"A": "", "B": "", "C": "", "D": "",...}},
      "capability": "Decision_support",
      "complexity": ""
    }} 
    
    
    Explaination of each field:
    question: The final question.
    options: {{"A": "option1", "B": "option2", "C": "option3", "D": "option4",...}}, there must be at least 3 options.
    capability: It must be 'Decision_support'.
    complexity: Show the complexity level of this question: ['1','2','3','4','5'], where '5' represents the most complex level and '1' represents the simplest level.

    5. Quality Control:
    - Must not duplicate or depend on existing final questions.
    - Must be totally different from existing final questions, and not just described in a different way.
    - Avoid subjective or ambiguous terms.
    - Must spell out acronyms and abbreviations everywhere in the output content.
    - The 'complexity' should be the greatest.
    

    Existing final questions (do not repeat them):
    {existing_final_questions}

    Generate exactly one new, unique, independent final question following these requirements strictly. Output only valid JSON matching the specified format and property names must be enclosed in double quotes."""


# ===========================================================
# =================  3.prompt_fq_answer  =====================
# ===========================================================


def prompt_fq_answer(
    contextual_information="None", final_question="""{"None":"None"}"""
):
    return f"""Core Task: Given a Question and the corresponding image, provide the correct answer based on the image:

    1. Background Information:

    Below is the information extracted from the contextual text surrounding the image's location within the financial document. 
    - Contextual information (******xxxxxxx******):
    ******
    {contextual_information}
    ******

    2. Given Question:
    {final_question}

    3. Core Requirements:
    - To ensure complete accuracy, the answer must be subjected to rigorous analysis and comprehensive thinking. 

    4. Rules:
    (1) Answer must be unambiguous.
    (2) Must be objectively correct based on the image.
    (3) Select a letter from the options of the question in the Question Information.


    5. Examples:
    - If the answer is A, output:
    {{
      "answer": "A"
    }}


    Generate exactly and completely correct answer letter following the rules strictly. Output only valid JSON matching the specified format and property names must be enclosed in double quotes."""


# ===========================================================
# ==============  4.prompt_answer_fq_judge   =================
# ===========================================================


def prompt_answer_fq_judge(
    image_background="""{"None":"None}""",
    final_question="""{"None":"None"}""",
    current_qa_chain="""{"None":"None"}""",
):
    return f"""Core Task: Given an image and a chain of existing information, please determine whether the provided information is sufficient for one to confidently and correctly answer the final question without needing to extract any additional information from the image.

    
    1. Background Information:

    - One need to answer the final question based only on the chain of existing information without even looking at the image.
    - The chain of existing information must comprehensively and completely reflect and embody every necessary detail for reasoning out the final question; otherwise, it is considered that the answer to the final question cannot be reasoned out yet.
    - Here are six capability levels of financial knowledge and image understanding:
      * level 1: Perception (identifying chart basic elements)
      * level 2: Data extraction (reading and reporting explicit values or facts directly shown in the chart)
      * level 3: Calculation analysis (computing metrics based on the chart)
      * level 4: Pattern recognition (identifying observable trends, comparisons, or groupings visible in the data)
      * level 5: Logical reasoning (deriving relationships based on the chart)
      * level 6: Decision support (making decisions involving financial knowledge)
    - The capability level reflected in the existing information must match that of the final question.

    2. Image Background (******xxxxxxx******):
    ******
    {image_background}
    ******
    
    3. The final question:
    {final_question}

    
    4. The chain of existing information:
    {current_qa_chain}

    
    5. Core Requirements:

    - Evaluate whether the existing information provides sufficient financial knowledge, and insightful financial image understanding so that one can confidently and accurately answer the final question by relying on this information.
    - Verify the capability level reflected in the existing information must match that of the final question.
    - Respond with either "yes" or "no" and include an adequacy score from 1 to 5, where 5 means the information is comprehensive, precise, and fully sufficient for confident and accurate answering while 1 means the information is entirely insufficient or irrelevant.
    - When no existing information is available, directly output "no" with an adequacy_degree of 1.


    6. Output Format (JSON):

    {{
      "can_answer": "yes or no",
      "adequacy_degree": "select one of the 5 adequacy degrees: ['1','2','3','4','5' where '5' indicates the existing information is sufficient while '1' indicates entirely insufficient."
    }}

    
    7. Examples:

    For example, if the final question corresponds to capability level 6:
    If the existing information presents a structured progression of financial knowledge and insightful understanding that fully encompasses levels 1 through 6, enabling one to directly, correctly and confidently answer the final question, please respond with:
    {{
      "can_answer": "yes",
      "adequacy_degree": "5"
    }}
    If the existing information is insufficient, presenting financial knowledge and image understanding reflecting only the first 2 to 3 of capability levels, and is far from adequate to answer the final question, please respond with:
    {{
      "can_answer": "no",
      "adequacy_degree": "3"
    }}

    Please strictly generate your judgment result in accordance with the requirements, outputting only valid JSON that conforms to the specified format."""


# ===========================================================
# ============   5.prompt_node_expansion   ====================
# ===========================================================


def prompt_node_expansion(
    current_capability_level="None",
    next_capability_level="Perception",
    count_sign=0,
    image_background="""{"None":"None"}""",
    final_question="""{"None":"None"}""",
    current_qa_chain_content="None",
    current_same_parent_qa_nodes="""{"None":"None"}""",
):

    if count_sign == 1:
        capability_sentence = f"The question must now be at either the {current_capability_level} or {next_capability_level} capability level. You may choose one of these levels to generate the question. If you select {current_capability_level}, the question should incorporate as much knowledge relevant to that level as possible, based on the image."
    else:
        if current_capability_level == next_capability_level:
            capability_sentence = f"The question must now be at the {current_capability_level} capability level."
        else:
            capability_sentence = f"The question must now be at either the {current_capability_level} or {next_capability_level} capability level. You may choose one of these levels to generate the question."

    return f"""
    Core Task: 
    Given a final question, a corresponding image, and a series of existing information, generate a new question-answer pair so that by addressing the generated question, one can extend existing information with the correct answer such that the extended information progresses one reasoning step towards solving the given final question.

    
    1. Background Information:

    - Here are six capability levels of financial knowledge and image understanding:
      * level 1: Perception (identifying chart basic elements)
      * level 2: Data extraction (reading and reporting explicit values or facts directly shown in the chart)
      * level 3: Calculation analysis (computing metrics based on the chart)
      * level 4: Pattern recognition (identifying observable trends, comparisons, or groupings visible in the data)
      * level 5: Logical reasoning (deriving relationships based on the chart)
      * level 6: Decision support (making decisions involving financial knowledge)
      

      
    2. Image Description:
    Below is the information extracted from the contextual text surrounding the image's location within the financial document.
    - Contextual information (******xxxxxxx******):
    ******
    {image_background}
    ******

    3. The final question is as follows:
    {final_question}

    4. Existing information (None means empty):
    {current_qa_chain_content}

    5. Existing question-answer pairs (None means empty):
    {current_same_parent_qa_nodes}

    6. Core Requirements:
    - {capability_sentence}
    - The correct answer to the question can be integrated into the existing information, advancing the reasoning process by one step toward solving the final question.
    - Only reflect and examine one piece of information or one knowledge point of the financial image, or comprehensively examine from different angles based on the existing information.
    - Must not duplicate existing question-answer pairs.
    - Must be independent from existing information and existing question-answer pairs.
    - The question must be related to finance.
    - The question must be related to the image and it can't be answered without the image.
    - The question must be objective  (must be single-choice and there must be only one correct choice).
    - The answer to this question must be unambiguous and verifiable.
    - The language of all output content must strictly be limited to English.
    - The number of words in the question should be between 10-500.

    7. Output Format (JSON):
    {{
      "question": "",
      "options": {{"A": "", "B": "", "C": "", "D": "",...}},
      "capability": "",
      "complexity": ""
    }}
    
    Explaination of each field:
    question: The newly generated question.
    options: {{"A": "option1", "B": "option2", "C": "option3", "D": "option4",...}}, there must be at least 3 options.
    capability: select one of the 6 capabilities: ['Perception','Data_extraction','Calculation_analysis','Pattern_recognition','Logical_reasoning','Decision_support'].
    complexity: select one of the 5 complexity degrees: ['1','2','3','4','5'], where '5' represents the most complex degree and '1' represents the simplest degree. 
    

    8. Quality Control:
    - Must not duplicate or depend on existing questions.
    - Must be totally different from existing questions and existing information, and not just described in a different way.
    - Avoid subjective or ambiguous terms.
    - Must spell out acronyms and abbreviations everywhere in the output content.
    - Must relate to the image itself.

    Generate exactly one new, unique, independent question following these requirements strictly. Output only valid JSON matching the specified format."""


# ===========================================================
# ================   6.prompt_node_action   ===================
# ===========================================================


def prompt_node_action(
    image_background="""{"None":"None"}""",
    target_question_node_information="""{"None":"None"}""",
    current_qa_chain_content="None",
):
    return f"""Core Task: Given the Question and the corresponding image, please generate the answer based on the image and a series of existing information.
  
    1.Image Background (******xxxxxxx******):
    ******
    {image_background}
    ******
    
    2. Given Question:
    {target_question_node_information}
    
    3. Existing information (None means empty):
    {current_qa_chain_content}
    
    4. Core Requirements:
    - To ensure complete accuracy, the answer must be subjected to rigorous analysis and comprehensive thinking. 
    
    5. Rules:
    (1) Answer must be unambiguous (just the letter)
    (2) Must be objectively correct based on the image
    (3) Select a letter from the options to answer the given Question 

    6. Output Format (JSON):
    {{
      "answer": "A"
    }}
    
    7. Examples:
    If the answer is A, output:
    {{
      "answer": "A"
    }}
    If the answer is D, output:
    {{
      "answer": "D"
    }}
    
    Generate exactly and completely correct answer letter following the rules strictly. Output only valid JSON matching the specified format."""


# ===========================================================
# ============   7.prompt_chain_fq_answer   ===================
# ===========================================================


def prompt_chain_fq_answer(
    image_background="""{"None":"None"}""",
    final_question="""{"None":"None"}""",
    current_qa_chain_content="""{"None":"None"}""",
):
    return f"""Core Task: Given the Question and the corresponding image, please generate the answer based on the image and a series of existing information.
    
    1. Image Background (******xxxxxxx******):
    ******
    {image_background}
    ******
    
    2. Given Question:
    {final_question}
    
    3. A series of existing information:
    {current_qa_chain_content}

    4. Core Requirements:
    - To ensure complete accuracy, the answer must be subjected to rigorous analysis and comprehensive thinking. 

    5. Rules:
    (1) Answer must be unambiguous (just the letter)
    (2) Must be objectively correct based on the image
    (3) Select a letter from the options to answer the given Question 
        
    6. Output Format (JSON):
    {{
      "answer": "A"
    }}

    7. Examples:
    If the answer is A, output:
    {{
      "answer": "A"
    }}
    If the answer is D, output:
    {{
      "answer": "D"
    }}

    Generate exactly and completely correct answer letter following the rules strictly. Output only valid JSON matching the specified format."""


# ===========================================================
# ============   prompt_node_qa_description   ===================
# ===========================================================


def prompt_node_qa_description(node_question="None", node_answer="None"):
    return f"""Question:
{node_question}

Answer:
{node_answer}

Convert the above Q&A pair into a single sentence or paragraph description without adding any extra information. If the Q&A pair is incomplete, return "None"."""


if __name__ == "__main__":

    print(prompt_image_judge())
    print(prompt_fq_generate())
    print(prompt_fq_answer())
    print(prompt_answer_fq_judge())
    print(prompt_node_expansion())
    print(prompt_node_action())
    print(prompt_chain_fq_answer())
    print(prompt_node_qa_description())

"""
Image Question Answering Tree Construction System

This system processes images, generates final questions, builds reasoning trees,
and evaluates answers using visual language models (VLMs).

Key Components:
1. Image processing and contextual information extraction
2. Final question generation
3. Tree-based reasoning construction
4. Answer evaluation and backpropagation
"""

import os
import json
import random
from typing import Dict, List, Optional, Union

import math
import numpy as np

from .doubao import *
from .qwen import *
from .prompt import *


class ImageQASystem:
    def __init__(self):
        """Initialize all global variables and system parameters."""
        # Image-related variables
        self.image_path = ""
        self.dir_name = ""
        self.img_name = ""
        self.contextual_information = "None"

        self.image_background = {"image_background": "None"}
        self.analysis_information = {"analysis_information": "None"}
        self.context_summarization = {"context_summarization": "None"}
        self.current_capability_level = ""
        self.next_capability_level = ""
        self.image_is_compliant = False
        self.image_compliance_level = 0
        self.image_judge_info = []

        # Final questions and answers
        self.image_fq = []  # List of final questions
        self.image_fq_prompt = []  # Prompt of final question generation
        self.image_fq_answer = []  # List of final question answers
        self.current_image_fq = {}  # Current final question being processed
        self.current_image_fq_answer = {}  # Current final question answer

        # Tree construction variables
        self.current_image_fq_tree = []  # Nodes in the current question tree
        self.current_image_fq_tree_answer_action = []  # Answer actions in tree
        self.current_qa_chain_info = []  # Chain info (type and no)
        self.current_qa_chain = []  # Full chain content
        self.current_question_node = {}  # Current node being processed
        self.current_question_node_answer = {}  # Current node being processed
        self.current_qa_chain_content = (
            []
        )  # Sentences into which the LLM converts the QA pairs

        # System parameters
        # self.max_node_num = 200  # Maximum nodes per tree

        self.max_chain_num = 20  # Maximum chains per tree
        self.max_chain_node_num = 20  # Maximum nodes per chain

        self.context_window_size = 1000  # Context characters before/after image
        self.default_fq_count = 3  # Default number of final questions
        self.fq_processed_count = 0
        self.sigmoid_alpha = 1.0  # Sigmoid linear transform parameter
        self.sigmoid_beta = 5.0  # Sigmoid linear transform parameter
        self.uct_exploration = math.sqrt(2)  # UCT exploration constant

        self.current_chain_num = 0

        # Path configurations
        self.base_output_path = "output"
        self.error_path = os.path.join(self.base_output_path, "error")
        self.image_judge_info_path = os.path.join(
            self.base_output_path, "image_judge_info"
        )
        self.image_fq_path = os.path.join(self.base_output_path, "image_fq")
        self.image_fq_answer_path = os.path.join(
            self.base_output_path, "image_fq_answer"
        )
        self.tree_path = os.path.join(self.base_output_path, "tree")
        self.can_answer_judge_path = os.path.join(
            self.base_output_path, "answer_fq_judge"
        )
        self.chain_info_path = os.path.join(
            self.base_output_path, "current_qa_chain_info"
        )
        self.chain_path = os.path.join(self.base_output_path, "current_qa_chain")
        self.chain_content_path = os.path.join(
            self.base_output_path, "current_qa_chain_content"
        )
        self.tree_answer_path = os.path.join(
            self.base_output_path, "current_image_fq_tree_answer_action"
        )

        self.context_file_path = ""

        # Create directories if they don't exist
        self._create_directories()

    def _create_directories(self):
        """Create all necessary output directories."""
        os.makedirs(self.error_path, exist_ok=True)
        os.makedirs(self.image_judge_info_path, exist_ok=True)
        os.makedirs(self.image_fq_path, exist_ok=True)
        os.makedirs(self.image_fq_answer_path, exist_ok=True)
        os.makedirs(self.tree_path, exist_ok=True)
        os.makedirs(self.can_answer_judge_path, exist_ok=True)
        os.makedirs(self.chain_info_path, exist_ok=True)
        os.makedirs(self.chain_path, exist_ok=True)
        os.makedirs(self.chain_content_path, exist_ok=True)
        os.makedirs(self.tree_answer_path, exist_ok=True)
        # os.makedirs(self.context_file_path, exist_ok=True)

    def _save_error(self, error_info: Dict) -> None:
        """
        Save error information to a JSON file, appending new errors while maintaining valid JSON structure.
        Creates the file/directory if they don't exist. Handles corrupted JSON gracefully.

        Args:
            error_info: Dictionary containing error details to be saved.
        """
        if not self.image_path:
            return

        # Generate target file path
        dir_name = os.path.basename(os.path.dirname(self.image_path))
        file_name = f"{os.path.basename(self.image_path).split('.')[0]}.json"
        error_dir = os.path.join(self.error_path, dir_name)
        os.makedirs(error_dir, exist_ok=True)  # Ensure directory exists
        error_file = os.path.join(error_dir, file_name)

        # Initialize or read existing data
        if not os.path.exists(error_file):
            existing_data = []  # New file starts with empty list
        else:
            try:
                with open(error_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = []  # Reset if not a list
            except (json.JSONDecodeError, FileNotFoundError):
                existing_data = []  # Handle corrupted/invalid JSON

        # Append new error and save
        existing_data.append(error_info)
        with open(error_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=2)  # Atomic write

    def _get_image_dir_and_name(self) -> tuple:
        """
        Extract directory name and image name from image path.

        Returns:
            tuple: (directory_name, image_name_without_extension)
        """
        dir_name = os.path.basename(os.path.dirname(self.image_path))
        img_name = os.path.basename(self.image_path).split(".")[0]
        self.dir_name = dir_name
        self.img_name = img_name
        return dir_name, img_name

    def start(self, image_path: str = "", context_base_path: str = ""):
        """
        Initialize the system with an image path.

        Args:
            image_path: Path to the input image
        """
        if image_path:
            self.image_path = image_path
        elif not self.image_path:
            raise ValueError("No image path provided")

        if context_base_path:
            self.context_file_path = context_base_path
        elif not self.context_file_path:
            raise ValueError("No context path provided")

        print(f"Start processing the image\nimage_path: {self.image_path}")

    def image_input(self):
        """Process image input and extract contextual information."""
        # self.get_contextual_information()
        self.get_image_background()
        self.get_analysis_information()
        self.get_context_summarization()

        print("Image information input completed")

    def get_image_background(self):

        try:
            dir_name, img_name = self._get_image_dir_and_name()
            context_dir = os.path.join(self.context_file_path, dir_name)
            os.makedirs(context_dir, exist_ok=True)
            context_file = os.path.join(context_dir, f"{img_name}.json")

            image_context = {"image_background": "None"}
            if os.path.exists(context_file):
                with open(context_file, "r", encoding="utf-8") as f:
                    image_context = json.load(f)
                print("Loaded existing image_background")

            self.image_background = {
                "image_background": image_context.get("image_background", "None")
            }
            print(self.image_background)

        except:
            self.image_background = {"image_background": "None"}

    def get_analysis_information(self):
        try:
            dir_name, img_name = self._get_image_dir_and_name()
            context_dir = os.path.join(self.context_file_path, dir_name)
            os.makedirs(context_dir, exist_ok=True)
            context_file = os.path.join(context_dir, f"{img_name}.json")

            image_context = {"analysis_information": "None"}
            if os.path.exists(context_file):
                with open(context_file, "r", encoding="utf-8") as f:
                    image_context = json.load(f)
                print("Loaded existing analysis information")

            self.analysis_information = {
                "analysis_imformation": {
                    image_context.get("analysis_information", "None")
                }
            }
            print(self.analysis_information)

        except:
            self.analysis_information = {"analysis_information": "None"}

    def get_context_summarization(self):
        try:
            dir_name, img_name = self._get_image_dir_and_name()
            context_dir = os.path.join(self.context_file_path, dir_name)
            os.makedirs(context_dir, exist_ok=True)
            context_file = os.path.join(context_dir, f"{img_name}.json")

            image_context = {"image_background": "None", "analysis_information": "None"}
            if os.path.exists(context_file):
                with open(context_file, "r", encoding="utf-8") as f:
                    image_context = json.load(f)
                print("Loaded existing context summarization")

            self.context_summarization = image_context
            print(self.context_summarization)

        except:
            self.context_summarization = {
                "image_background": "None",
                "analysis_information": "None",
            }

    # def get_contextual_information(self):
    #     """
    #     Extract contextual information from markdown file associated with the image.

    #     The markdown file is located by replacing the image directory with 'markdown'
    #     and changing the extension to .md.
    #     """
    #     try:
    #         # Extract markdown file path from image path
    #         img_dir = os.path.dirname(self.image_path)
    #         dir_name = os.path.basename(img_dir)
    #         md_file = os.path.join(
    #             r"F:\AgenticFin_Lab\fttracer_coding_dataset\markdown", f"{dir_name}.md"
    #         )

    #         if not os.path.exists(md_file):
    #             print("There is no corresponding markdown file")
    #             self.contextual_information = "None"
    #             return

    #         # Read markdown content
    #         with open(md_file, "r", encoding="utf-8") as f:
    #             md_content = f.read()

    #         # Find image in markdown
    #         img_name = os.path.basename(self.image_path)
    #         img_pattern = f"![](images_copy/{img_name})"

    #         img_pos = md_content.find(img_pattern)
    #         if img_pos == -1:
    #             print("The markdown file exists, but image location not found")
    #             self.contextual_information = "None"
    #             return

    #         # Extract context window
    #         start_pos = max(0, img_pos - self.context_window_size)
    #         end_pos = min(
    #             len(md_content), img_pos + len(img_pattern) + self.context_window_size
    #         )
    #         self.contextual_information = md_content[start_pos:end_pos]
    #         print("Context information found")

    #     except Exception as e:
    #         error_info = {
    #             "image_path": self.image_path,
    #             "error": "Failed to get contextual information",
    #             "exception": str(e),
    #             "contextual_information": self.contextual_information,
    #         }
    #         self._save_error(error_info)
    #         self.contextual_information = "None"
    #         print(f"Error getting contextual information: {str(e)}")

    def image_judge(self) -> bool:
        """
        Judge if the image meets requirements using VLM.

        Returns:
            bool: True if image is compliant, False otherwise
        """
        try:
            local_image_messages = [
                {
                    "role": "user",
                    "content": create_message_content(
                        image_path=self.image_path,
                        text=prompt_image_judge(self.context_summarization),
                    ),
                }
            ]

            response = doubao_seed_1_6_flash(local_image_messages)
            response_json = json.loads(response)

            self.image_is_compliant = (
                response_json.get("is_compliant", "").lower() == "yes"
            )
            self.image_compliance_level = int(response_json.get("compliance_level", 0))

            dir_name, img_name = self._get_image_dir_and_name()
            output_dir = os.path.join(self.image_judge_info_path, dir_name)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{img_name}.json")

            image_judge_info = [
                {
                    "image_path": self.image_path,
                    "context_summarization": self.context_summarization,
                    "image_is_compliant": self.image_is_compliant,
                    "image_compliance_level": self.image_compliance_level,
                }
            ]

            self.image_judge_info = image_judge_info

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.image_judge_info, f, indent=2, ensure_ascii=False)

            return self.image_is_compliant

        except Exception as e:
            error_info = {
                "image_path": self.image_path,
                "error": "Image compliance check failed",
                "exception": str(e),
                "context_summarization": self.context_summarization,
                "image_is_compliant": self.image_is_compliant,
                "image_compliance_level": self.image_compliance_level,
            }
            self._save_error(error_info)
            print(f"Error in image judgment: {str(e)}")
            return False

    def fq_generate(self):
        """Generate final questions for the image using VLM."""
        try:
            dir_name, img_name = self._get_image_dir_and_name()
            output_dir = os.path.join(self.image_fq_path, dir_name)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{img_name}.json")
            output_file_prompt = os.path.join(output_dir, f"{img_name}_prompt.json")
            output_file_reserved = os.path.join(output_dir, f"{img_name}_reserved.json")

            # Check if we already have generated questions
            if os.path.exists(output_file):
                print("There are existing final questions!")
                return

            # Generate new questions
            self.image_fq = []

            for i in range(self.default_fq_count):
                print(f"Generating final question: {i+1}/{self.default_fq_count}")

                try:
                    local_image_messages = [
                        {
                            "role": "user",
                            "content": create_message_content(
                                image_path=self.image_path,
                                text=prompt_fq_generate(
                                    str(self.context_summarization), str(self.image_fq)
                                ),
                            ),
                        }
                    ]

                    response = doubao_seed_1_6_flash(local_image_messages)
                    fq_data = json.loads(response)
                    fq_data_prompt = {}

                    # Add required fields

                    fq_data["image_path"] = self.image_path
                    fq_data["fq_no"] = i + 1
                    fq_data.update(self.context_summarization)

                    fq_data_prompt["image_path"] = self.image_path
                    fq_data_prompt["fq_no"] = i + 1
                    fq_data_prompt["prompt"] = prompt_fq_generate(
                        str(self.context_summarization), str(self.image_fq)
                    )

                    self.image_fq.append(fq_data)
                    self.image_fq_prompt.append(fq_data_prompt)

                except Exception as e:
                    print(f"Error generating final question {i + 1}: {str(e)}")
                    continue

            # Save generated questions
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.image_fq, f, indent=2, ensure_ascii=False)

            # Save prompt of final question generation
            with open(output_file_prompt, "w", encoding="utf-8") as f:
                json.dump(self.image_fq_prompt, f, indent=2, ensure_ascii=False)

            # Save generated questions reserved
            with open(output_file_reserved, "w", encoding="utf-8") as f:
                json.dump(self.image_fq, f, indent=2, ensure_ascii=False)

            print(f"Generated {len(self.image_fq)} final questions")

        except Exception as e:
            error_info = {
                "image_path": self.image_path,
                "error": "Final question generation failed",
                "exception": str(e),
                "image_fq": self.image_fq,
            }
            self._save_error(error_info)
            print(f"Error in final question generation: {str(e)}")

    def fq_answer(self):
        """Generate answers for the final questions using VLM."""
        try:
            print("111")

            dir_name, img_name = self._get_image_dir_and_name()
            output_dir = os.path.join(self.image_fq_answer_path, dir_name)
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{img_name}.json")
            output_file_reserved = os.path.join(output_dir, f"{img_name}_reserved.json")

            output_dir_fq = os.path.join(self.image_fq_path, dir_name)
            output_file_fq = os.path.join(output_dir_fq, f"{img_name}.json")

            if self.image_fq == [] and os.path.exists(output_file_fq):
                with open(output_file_fq, "r", encoding="utf-8") as f:
                    self.image_fq = json.load(f)
                print("Loaded existing final questions")

            if self.image_fq_answer == [] and os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    self.image_fq_answer = json.load(f)
                print("Loaded existing answers of final questions")

            # dir_name, img_name = self._get_image_dir_and_name()
            # output_dir_fq_answer = os.path.join(self.image_fq_answer_path, dir_name)
            # output_dir_fq = os.path.join(self.image_fq_path, dir_name)
            # os.makedirs(output_dir_fq_answer, exist_ok=True)
            # os.makedirs(output_dir_fq, exist_ok=True)
            # output_file_fq_answer = os.path.join(output_dir_fq_answer, f"{img_name}.json")
            # output_file_fq = os.path.join(output_dir_fq, f"{img_name}.json")

            # Check if we already have generated answers
            if os.path.exists(output_file):
                print("There are existing final question answers!")
                return

            print(self.image_fq)
            # Generate new answers
            self.image_fq_answer = []
            for fq in self.image_fq:
                print(f"Generating the answer of final question: {fq}")
                try:
                    local_image_messages = [
                        {
                            "role": "user",
                            "content": create_message_content(
                                image_path=self.image_path,
                                text=prompt_fq_answer(
                                    str(self.context_summarization), str(fq)
                                ),
                            ),
                        }
                    ]

                    # Add required fields
                    answer_data = {}
                    answer_data["image_path"] = self.image_path
                    answer_data["fq_no"] = fq["fq_no"]

                    try:
                        response_1 = doubao_seed_1_6_flash(local_image_messages)
                        try:
                            if response_1.startswith(
                                "```json\n"
                            ) and response_1.endswith("\n```"):
                                response_1 = response_1[8:-4]
                            answer_1 = {"answer_1": json.loads(response_1)}
                        except:
                            answer_1 = {"answer_1": {"answer": response_1}}
                    except:
                        answer_1 = {"answer_1": {"answer": response_1}}

                    try:
                        response_2 = doubao_1_5_thinking_vision_pro(
                            local_image_messages
                        )
                        try:
                            if response_2.startswith(
                                "```json\n"
                            ) and response_2.endswith("\n```"):
                                response_2 = response_2[8:-4]
                            answer_2 = {"answer_2": json.loads(response_2)}
                        except:
                            answer_2 = {"answer_2": {"answer": response_2}}
                    except:
                        answer_2 = {"answer_2": {"answer": response_2}}

                    try:
                        response_3 = qwen_vl_max_latest(local_image_messages)
                        try:
                            if response_3.startswith(
                                "```json\n"
                            ) and response_3.endswith("\n```"):
                                response_3 = response_3[8:-4]
                            answer_3 = {"answer_3": json.loads(response_3)}
                        except:
                            answer_3 = {"answer_3": {"answer": response_3}}
                    except:
                        answer_3 = {"answer_3": {"answer": response_3}}

                    try:
                        response_4 = qwen_vl_plus_latest(local_image_messages)
                        try:
                            if response_4.startswith(
                                "```json\n"
                            ) and response_4.endswith("\n```"):
                                response_4 = response_4[8:-4]
                            answer_4 = {"answer_4": json.loads(response_4)}
                        except:
                            answer_4 = {"answer_4": {"answer": response_4}}
                    except:
                        answer_4 = {"answer_4": {"answer": response_4}}

                    try:
                        response_5 = qwen2_5_vl_72b_instruct(local_image_messages)
                        try:
                            if response_5.startswith(
                                "```json\n"
                            ) and response_5.endswith("\n```"):
                                response_5 = response_5[8:-4]
                            answer_5 = {"answer_5": json.loads(response_5)}
                        except:
                            answer_5 = {"answer_5": {"answer": response_5}}
                    except:
                        answer_5 = {"answer_5": {"answer": response_5}}

                    answer_data.update(answer_1)
                    answer_data.update(answer_2)
                    answer_data.update(answer_3)
                    answer_data.update(answer_4)
                    answer_data.update(answer_5)

                    print(f"answer_date 111: {answer_data}")
                    # Extract all answers
                    answers = [
                        answer_1.get("answer_1").get("answer"),
                        answer_2.get("answer_2").get("answer"),
                        answer_3.get("answer_3").get("answer"),
                        answer_4.get("answer_4").get("answer"),
                        answer_5.get("answer_5").get("answer"),
                    ]

                    # Count answer frequencies
                    answer_count = {}
                    for ans in answers:
                        answer_count[ans] = answer_count.get(ans, 0) + 1

                    # Sort answers by frequency
                    sorted_answers = sorted(
                        answer_count.items(), key=lambda x: x[1], reverse=True
                    )

                    # Determine consensus and set final answer with reliability
                    if sorted_answers[0][1] == 5:  # All 5 answers agree
                        final_answer = sorted_answers[0][0]
                        reliability = "5"
                    elif sorted_answers[0][1] == 4:  # 4 answers agree
                        final_answer = sorted_answers[0][0]
                        reliability = "4"
                    elif sorted_answers[0][1] == 3:  # 3 answers agree
                        final_answer = sorted_answers[0][0]
                        reliability = "3"
                    elif (
                        sorted_answers[0][1] == 2
                        and len(sorted_answers) >= 2
                        and sorted_answers[1][1] == 2
                    ):  # 2-2-1 distribution
                        # Randomly select between the two most frequent answers
                        final_answer = random.choice(
                            [sorted_answers[0][0], sorted_answers[1][0]]
                        )
                        reliability = "2"
                    elif (
                        sorted_answers[0][1] == 2
                    ):  # Only one pair agrees, others are unique
                        final_answer = sorted_answers[0][0]
                        reliability = "2"
                    else:  # All answers are different
                        final_answer = answer_1.get("answer_1").get("answer")
                        reliability = "1"

                    # Add final answer and reliability to answer_data
                    answer_data["answer"] = final_answer
                    answer_data["reliability"] = reliability

                    print(f"answer_date: {answer_data}")

                    self.image_fq_answer.append(answer_data)

                except Exception as e:
                    print(
                        f"Error generating answer for final question {fq['fq_no']}: {str(e)}"
                    )
                    continue

            # Save generated answers
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(self.image_fq_answer, f, indent=2, ensure_ascii=False)

            with open(output_file_reserved, "w", encoding="utf-8") as f:
                json.dump(self.image_fq_answer, f, indent=2, ensure_ascii=False)

            print(f"Generated answers for {len(self.image_fq_answer)} final questions")

        except Exception as e:
            error_info = {
                "image_path": self.image_path,
                "error": "Final question answer generation failed",
                "exception": str(e),
                "image_fq_answer": self.image_fq_answer,
            }
            self._save_error(error_info)
            print(f"Error in final question answer generation: {str(e)}")

    def choose_one_fq(self):

        dir_name, img_name = self._get_image_dir_and_name()
        output_dir = os.path.join(self.image_fq_path, dir_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{img_name}.json")

        # Check if we already have generated questions
        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                self.image_fq = json.load(f)
            print("Loaded existing final questions")

        output_dir = os.path.join(self.image_fq_answer_path, dir_name)
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{img_name}.json")

        if os.path.exists(output_file):
            with open(output_file, "r", encoding="utf-8") as f:
                self.image_fq_answer = json.load(f)
            print("Loaded existing final question answers")

        """Select the next final question to process."""
        if not self.image_fq:
            raise ValueError("No final questions available")
        if not self.image_fq_answer:
            raise ValueError("No final answers available")
        # Find the first question that hasn't been fully processed
        for fq in self.image_fq:
            self.fq_processed_count += 1
            if self.fq_processed_count > 1:
                print(
                    f"one fq tree has been created for book:{dir_name} image:{img_name}"
                )
                break
            fq_no = fq["fq_no"]
            dir_name, img_name = self._get_image_dir_and_name()
            tree_file = os.path.join(
                self.tree_path, dir_name, img_name, f"fq_{fq_no:06d}.json"
            )

            if not os.path.exists(tree_file):
                self.current_image_fq = fq
                # Find corresponding answer
                for ans in self.image_fq_answer:
                    if ans["fq_no"] == fq_no:
                        self.current_image_fq_answer = ans

                        tree_root_node = {
                            "image_path": self.image_path,
                            "fq_no": self.current_image_fq["fq_no"],
                            "question_node_no": 0,
                            "parent_node_no": -1,
                            "instruction": "None",
                            "question": "None",
                            "options": "None",
                            "capability": "None",
                            "complexity": "None",
                            "visit_count": 1,
                            "victory_count": 0,
                        }
                        self.current_image_fq_tree = [tree_root_node]
                        self.current_image_fq_tree_answer_action = []
                        self.current_question_node = tree_root_node
                        root_node_chain_info = {"type": "question", "no": 0}
                        self.current_qa_chain_info = [root_node_chain_info]
                        self.current_qa_chain = [tree_root_node]
                        break
                return

        # If all questions have been processed
        self.current_image_fq = {}
        self.current_image_fq_answer = {}

    def answer_fq_judge(self) -> bool:
        """
        Judge if current chain can answer the final question.

        Returns:
            bool: True if can answer, False otherwise
        """
        if not self.current_qa_chain:
            return False

        try:
            local_image_messages = [
                {
                    "role": "user",
                    "content": create_message_content(
                        image_path=self.image_path,
                        text=prompt_answer_fq_judge(
                            str(self.image_background),
                            str(self.current_image_fq),
                            str(self.current_qa_chain_content),
                        ),
                    ),
                }
            ]

            response = doubao_seed_1_6_flash(local_image_messages)
            response_json = json.loads(response)

            # Save judgment result
            dir_name, img_name = self._get_image_dir_and_name()
            fq_no = self.current_image_fq["fq_no"]
            output_dir = os.path.join(self.can_answer_judge_path, dir_name, img_name)
            output_file = os.path.join(output_dir, f"fq_{fq_no:06d}.json")

            os.makedirs(output_dir, exist_ok=True)

            result = {
                "current_image_fq": self.current_image_fq,
                "current_qa_chain": self.current_qa_chain,
                "judgment": response_json,
            }

            # Check if file exists
            if os.path.exists(output_file):
                # Read existing data
                with open(output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                # Append new result if existing data is a list
                if isinstance(existing_data, list):
                    existing_data.append(result)
                    result_to_save = existing_data
                else:
                    # Convert to list if existing data is a single dict
                    result_to_save = [existing_data, result]
            else:
                # Create new list with the first result
                result_to_save = [result]

            # Save the updated result list
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result_to_save, f, indent=2)

            return response_json.get("can_answer", "").lower() == "yes"

        except Exception as e:
            print(f"Error in can_answer judgment: {str(e)}")
            return False

    def child_num_is_zero(self) -> bool:
        """
        Check if current node has no children.

        Returns:
            bool: True if no children, False otherwise
        """
        if not self.current_question_node or not self.current_image_fq_tree:
            return True

        current_node_no = self.current_question_node["question_node_no"]
        children = [
            n
            for n in self.current_image_fq_tree
            if n["parent_node_no"] == current_node_no
        ]

        return len(children) == 0

    def sigmoid_sampling_judge(self) -> bool:
        """
        Decide whether to use existing child nodes or expand new one.

        Returns:
            bool: True to use existing child, False to expand new node
        """
        current_node_no = self.current_question_node["question_node_no"]
        children = [
            n
            for n in self.current_image_fq_tree
            if n["parent_node_no"] == current_node_no
        ]
        n = len(children)

        if n == 0:
            return False

        # Linear transform
        z = self.sigmoid_alpha * (n - self.sigmoid_beta)
        # Sigmoid
        use_existing_prob = 1 / (1 + math.exp(-z))

        # Bernoulli sampling
        return random.random() < use_existing_prob

    def node_expansion(self):
        """Expand a new node in the reasoning tree."""
        try:

            # Get current same parent nodes

            print(self.current_question_node)
            current_node_no = self.current_question_node["question_node_no"]

            current_same_parent_nodes = [
                n
                for n in self.current_image_fq_tree
                if n["parent_node_no"] == current_node_no
            ]

            self.current_capability_level = ""
            self.next_capability_level = ""

            perception_count = 0
            data_extraction_count = 0
            calculation_analysis_count = 0
            pattern_recognition_count = 0
            logical_reasoning_count = 0
            decision_support_count = 0
            for i in range(len(self.current_qa_chain_content)):
                if self.current_qa_chain_content[i]["capability"] == "Perception":
                    perception_count += 1
                elif (
                    self.current_qa_chain_content[i]["capability"] == "Data_extraction"
                ):
                    data_extraction_count += 1
                elif (
                    self.current_qa_chain_content[i]["capability"]
                    == "Calculation_analysis"
                ):
                    calculation_analysis_count += 1
                elif (
                    self.current_qa_chain_content[i]["capability"]
                    == "Pattern_recognition"
                ):
                    pattern_recognition_count += 1
                elif (
                    self.current_qa_chain_content[i]["capability"]
                    == "Logical_reasoning"
                ):
                    logical_reasoning_count += 1
                elif (
                    self.current_qa_chain_content[i]["capability"] == "Decision_support"
                ):
                    decision_support_count += 1

            count_sign = 0

            if len(self.current_qa_chain_content) == 0:
                self.current_capability_level = "Perception"
                self.next_capablity_level = "Perception"

            elif self.current_qa_chain_content[-1]["capability"] == "Perception":
                if perception_count >= 3:
                    self.current_capability_level = "Data_extraction"
                    self.next_capablity_level = "Data_extraction"
                elif perception_count == 2:
                    count_sign = 1
                    self.current_capability_level = "Perception"
                    self.next_capablity_level = "Data_extraction"
                else:
                    self.current_capability_level = "Perception"
                    self.next_capablity_level = "Data_extraction"

            elif self.current_qa_chain_content[-1]["capability"] == "Data_extraction":
                if data_extraction_count >= 3:
                    self.current_capability_level = "Calculation_analysis"
                    self.next_capablity_level = "Calculation_analysis"
                elif data_extraction_count == 2:
                    count_sign = 1
                    self.current_capability_level = "Data_extraction"
                    self.next_capablity_level = "Calculation_analysis"
                else:
                    self.current_capability_level = "Data_extraction"
                    self.next_capablity_level = "Calculation_analysis"

            elif (
                self.current_qa_chain_content[-1]["capability"]
                == "Calculation_analysis"
            ):
                if calculation_analysis_count >= 2:
                    self.current_capability_level = "Pattern_recognition"
                    self.next_capablity_level = "Pattern_recognition"
                elif calculation_analysis_count == 1:
                    count_sign = 1
                    self.current_capability_level = "Calculation_analysis"
                    self.next_capablity_level = "Pattern_recognition"
                else:
                    self.current_capability_level = "Calculation_analysis"
                    self.next_capablity_level = "Pattern_recognition"

            elif (
                self.current_qa_chain_content[-1]["capability"] == "Pattern_recognition"
            ):
                if pattern_recognition_count >= 2:
                    self.current_capability_level = "Logical_reasoning"
                    self.next_capablity_level = "Logical_reasoning"
                elif pattern_recognition_count == 1:
                    count_sign = 1
                    self.current_capability_level = "Pattern_recognition"
                    self.next_capablity_level = "Logical_reasoning"
                else:
                    self.current_capability_level = "Pattern_recognition"
                    self.next_capablity_level = "Logical_reasoning"

            elif self.current_qa_chain_content[-1]["capability"] == "Logical_reasoning":
                if logical_reasoning_count >= 2:
                    self.current_capability_level = "Decision_support"
                    self.next_capablity_level = "Decision_support"
                elif logical_reasoning_count == 1:
                    count_sign = 1
                    self.current_capability_level = "Logical_reasoning"
                    self.next_capablity_level = "Decision_support"
                else:
                    self.current_capability_level = "Logical_reasoning"
                    self.next_capablity_level = "Decision_support"

            elif self.current_qa_chain_content[-1]["capability"] == "Decision_support":
                self.current_capability_level = "Decision_support"
                self.next_capablity_level = "Decision_support"

            # Generate new node
            local_image_messages = [
                {
                    "role": "user",
                    "content": create_message_content(
                        image_path=self.image_path,
                        text=prompt_node_expansion(
                            self.current_capability_level,
                            self.next_capablity_level,
                            count_sign,
                            str(self.image_background),
                            str(self.current_image_fq),
                            str(self.current_qa_chain_content),
                            str(current_same_parent_nodes),
                        ),
                    ),
                }
            ]

            response = doubao_seed_1_6_flash(local_image_messages)

            new_node_data = json.loads(response)

            # Create new node structure
            new_node = {
                "image_path": self.image_path,
                "fq_no": self.current_image_fq["fq_no"],
                "question_node_no": len(self.current_image_fq_tree),
                "parent_node_no": current_node_no,
                "image_background": self.image_background.get(
                    "image_background", "None"
                ),
                "question": new_node_data.get("question", "None"),
                "options": new_node_data.get("options", "None"),
                "capability": new_node_data.get("capability", "None"),
                "complexity": new_node_data.get("complexity", "None"),
                "visit_count": 1,
                "victory_count": 0,
            }

            # Add to tree and update current node
            self.current_image_fq_tree.append(new_node)
            self.current_question_node = new_node

            # Update chain info
            self.current_qa_chain_info.append(
                {"type": "question", "no": new_node["question_node_no"]}
            )

            # Update full chain
            self.current_qa_chain.append(new_node)

        except Exception as e:
            print(f"Error in node expansion: {str(e)}")

    def node_qa_description(self):
        """
        convert the above Q&A pair into a sentence or paragraph description without adding any other information.
        """
        try:
            node_question = self.current_question_node["question"]
        except:
            node_question = "None"

        try:
            node_answer_options = self.current_question_node_answer.get(
                "answer", ""
            ).split(",")
            node_answer = ""
            for i in range(len(node_answer_options)):
                node_answer += (
                    self.current_question_node["options"][node_answer_options[i]] + "\n"
                )
        except:
            node_answer = "None"

        if node_question == "None" or node_answer == "None":
            response = "None"

        else:
            try:
                local_image_messages = [
                    {
                        "role": "user",
                        "content": create_message_content(
                            text=prompt_node_qa_description(node_question, node_answer)
                        ),
                    }
                ]
                response = doubao_seed_1_6_flash(local_image_messages)
            except:
                response = "None"

        self.current_qa_chain_content.append(
            {
                f"QA_Node_{str(len(self.current_qa_chain_content) + 1)}_Content": response,
                "capability": self.current_question_node["capability"],
            }
        )

        print(self.current_qa_chain_content)

    def node_action(self):
        """Take action from current node (select or generate answer)."""
        try:

            local_image_messages = [
                {
                    "role": "user",
                    "content": create_message_content(
                        image_path=self.image_path,
                        text=prompt_node_action(
                            str(self.image_background),
                            str(self.current_question_node),
                            str(self.current_qa_chain_content),
                        ),
                    ),
                }
            ]

            response = doubao_seed_1_6_flash(local_image_messages)
            answer_data = json.loads(response)
            self.current_question_node_answer = answer_data
            self.node_qa_description()
            answer = answer_data.get("answer", "")

            print("current_question_node:", self.current_question_node)
            print("current_question_node_answer: ", self.current_question_node_answer)

            # Check if answer action already exists
            existing_action_i = None

            for action_i in range(len(self.current_image_fq_tree_answer_action)):

                if (
                    self.current_image_fq_tree_answer_action[action_i][
                        "question_node_no"
                    ]
                    == self.current_question_node["question_node_no"]
                    and self.current_image_fq_tree_answer_action[action_i]["answer"]
                    == answer
                ):

                    existing_action_i = action_i

                    break

            if existing_action_i:
                # Update existing action
                self.current_image_fq_tree_answer_action[action_i]["visit_count"] += 1
                action_node = self.current_image_fq_tree_answer_action[action_i]

            else:
                # Create new action
                action_node = {
                    "fq_no": self.current_image_fq["fq_no"],
                    "question_node_no": self.current_question_node["question_node_no"],
                    "answer_no": len(self.current_image_fq_tree_answer_action),
                    "answer": answer,
                    "visit_count": 1,
                    "victory_count": 0,
                }
                self.current_image_fq_tree_answer_action.append(action_node)

            # Update chain info
            self.current_qa_chain_info.append(
                {"type": "answer", "no": action_node["answer_no"]}
            )

            # Update full chain
            self.current_qa_chain.append(action_node)

        except Exception as e:
            print(f"Error in node action: {str(e)}")

    def node_selection(self):
        """Select child node with highest UCT score."""

        current_node_no = self.current_question_node["question_node_no"]
        children = [
            n
            for n in self.current_image_fq_tree
            if n["parent_node_no"] == current_node_no
        ]

        if not children:
            return

        # Calculate total visits to all children
        N = sum(child["visit_count"] for child in children)

        # Calculate UCT for each child
        best_score = -float("inf")
        best_child = None

        for child in children:
            Q = child["victory_count"] / child["visit_count"]
            N_node = child["visit_count"]
            uct_score = Q + self.uct_exploration * math.sqrt(math.log(N) / N_node)

            if uct_score > best_score:
                best_score = uct_score
                best_child = child

        if best_child:
            # Update visit count
            best_child["visit_count"] += 1
            self.current_question_node = best_child

            # Update chain info
            self.current_qa_chain_info.append(
                {"type": "question", "no": best_child["question_node_no"]}
            )

            # Update full chain
            self.current_qa_chain.append(best_child)

    def chain_fq_answer(self) -> Dict:
        """
        Generate final answer for the current question using the reasoning chain.

        Returns:
            Dict: Answer data containing the selected option(s)
        """
        try:
            # Add final question to chain
            self.current_qa_chain_info.append(
                {"type": "finalquestion", "no": self.current_image_fq["fq_no"]}
            )
            self.current_qa_chain.append(self.current_image_fq)

            # Generate answer
            local_image_messages = [
                {
                    "role": "user",
                    "content": create_message_content(
                        image_path=self.image_path,
                        text=prompt_node_action(
                            str(self.image_background),
                            str(self.current_image_fq),
                            str(self.current_qa_chain_content),
                        ),
                    ),
                }
            ]

            response = doubao_seed_1_6_flash(local_image_messages)
            answer_data = json.loads(response)

            for action_i in range(len(self.current_image_fq_tree_answer_action)):
                if self.current_image_fq_tree_answer_action[action_i][
                    "question_node_no"
                ] == -1 and self.current_image_fq_tree_answer_action[action_i][
                    "answer"
                ] == answer_data.get(
                    "answer", ""
                ):
                    self.current_image_fq_tree_answer_action[action_i][
                        "visit_count"
                    ] += 1
                    answer_node = self.current_image_fq_tree_answer_action[action_i]
                    # Update chain info
                    self.current_qa_chain_info.append(
                        {"type": "finalanswer", "no": answer_node["answer_no"]}
                    )

                    # Update full chain
                    self.current_qa_chain.append(answer_node)
                    return answer_node

            # Create answer node
            answer_node = {
                "fq_no": self.current_image_fq["fq_no"],
                "question_node_no": -1,
                "chain_end_no": self.current_question_node["question_node_no"],
                "answer_no": len(self.current_image_fq_tree_answer_action),
                "answer": answer_data.get("answer", ""),
                "visit_count": 1,
                "victory_count": 0,
            }
            self.current_image_fq_tree_answer_action.append(answer_node)

            # Update chain info
            self.current_qa_chain_info.append(
                {"type": "finalanswer", "no": answer_node["answer_no"]}
            )

            # Update full chain
            self.current_qa_chain.append(answer_node)

            return answer_node

        except Exception as e:
            print(f"Error in chain answer generation: {str(e)}")
            return {"answer": ""}

    def answer_judge(self, chain_answer: Dict, fq_right_answer: Dict) -> bool:
        """
        Judge if the chain answer matches the correct answer.

        Args:
            chain_answer: Answer generated by the chain
            fq_right_answer: Correct answer from initial generation

        Returns:
            bool: True if answers match, False otherwise
        """
        return chain_answer.get("answer", "") == fq_right_answer.get("answer", "")

    def backpropagation(self):
        """Backpropagate victory count through the chain."""
        print("303030")
        print(f"self.current_qa_chain_info: {self.current_qa_chain_info}")
        for node_info_i in range(len(self.current_qa_chain_info)):
            print("313131")
            print(f"self.current_qa_chain_info:{self.current_qa_chain_info}")
            if self.current_qa_chain_info[node_info_i]["type"] == "question":
                # Find question node and update victory count
                print("323232")
                print(f"self.current_image_fq_tree: {self.current_image_fq_tree}")
                for q_node_i in range(len(self.current_image_fq_tree)):
                    if (
                        self.current_image_fq_tree[q_node_i]["question_node_no"]
                        == self.current_qa_chain_info[node_info_i]["no"]
                    ):
                        print("333333")
                        self.current_image_fq_tree[q_node_i]["victory_count"] += 1
                        print("343434")
                        break

            elif self.current_qa_chain_info[node_info_i]["type"] == "answer":
                # Find answer action and update victory count
                print("353535")
                print(
                    f"self.current_image_fq_tree_answer_action:{self.current_image_fq_tree_answer_action}"
                )
                for a_node_i in range(len(self.current_image_fq_tree_answer_action)):
                    if (
                        self.current_image_fq_tree_answer_action[a_node_i]["answer_no"]
                        == self.current_qa_chain_info[node_info_i]["no"]
                    ):
                        print("363636")
                        self.current_image_fq_tree_answer_action[a_node_i][
                            "victory_count"
                        ] += 1
                        print("373737")
                        break

            elif self.current_qa_chain_info[node_info_i]["type"] == "finalanswer":
                # Find final answer and update victory count
                print("383838")
                for fa_node_i in range(len(self.current_image_fq_tree_answer_action)):
                    if (
                        self.current_image_fq_tree_answer_action[fa_node_i]["answer_no"]
                        == self.current_qa_chain_info[node_info_i]["no"]
                    ):
                        print("393939")
                        self.current_image_fq_tree_answer_action[fa_node_i][
                            "victory_count"
                        ] += 1
                        print("404040")
                        break

    def save_tree(self):
        """Save current tree state to file."""
        if not self.current_image_fq:
            return

        dir_name, img_name = self._get_image_dir_and_name()
        fq_no = self.current_image_fq["fq_no"]

        # Save tree
        tree_dir = os.path.join(self.tree_path, dir_name, img_name)
        os.makedirs(tree_dir, exist_ok=True)
        tree_file = os.path.join(tree_dir, f"fq_{fq_no:06d}.json")

        with open(tree_file, "w", encoding="utf-8") as f:
            json.dump(self.current_image_fq_tree, f, ensure_ascii=False, indent=2)

        # Save answer actions
        answer_dir = os.path.join(self.tree_answer_path, dir_name, img_name)
        os.makedirs(answer_dir, exist_ok=True)
        answer_file = os.path.join(answer_dir, f"fq_{fq_no:06d}.json")

        with open(answer_file, "w", encoding="utf-8") as f:
            json.dump(
                self.current_image_fq_tree_answer_action,
                f,
                ensure_ascii=False,
                indent=2,
            )

    def save_chain(self):
        """Save current chain state to file."""
        if not self.current_image_fq or not self.current_qa_chain_info:
            return

        dir_name, img_name = self._get_image_dir_and_name()
        fq_no = self.current_image_fq["fq_no"]

        # Find next chain number
        chain_dir = os.path.join(
            self.chain_info_path, dir_name, img_name, f"fq_{fq_no:06d}"
        )
        os.makedirs(chain_dir, exist_ok=True)

        existing_chains = [f for f in os.listdir(chain_dir) if f.endswith(".json")]
        chain_num = len(existing_chains) + 1
        chain_file = os.path.join(chain_dir, f"{chain_num:06d}.json")

        # Save chain info
        with open(chain_file, "w", encoding="utf-8") as f:
            json.dump(self.current_qa_chain_info, f, ensure_ascii=False, indent=2)

        # Save full chain
        full_chain_dir = os.path.join(
            self.chain_path, dir_name, img_name, f"fq_{fq_no:06d}"
        )
        os.makedirs(full_chain_dir, exist_ok=True)
        full_chain_file = os.path.join(full_chain_dir, f"{chain_num:06d}.json")

        with open(full_chain_file, "w", encoding="utf-8") as f:
            json.dump(self.current_qa_chain, f, ensure_ascii=False, indent=2)

        # Save chain content
        chain_content_dir = os.path.join(
            self.chain_content_path, dir_name, img_name, f"fq_{fq_no:06d}"
        )
        os.makedirs(chain_content_dir, exist_ok=True)
        chain_content_file = os.path.join(chain_content_dir, f"{chain_num:06d}.json")

        with open(chain_content_file, "w", encoding="utf-8") as f:
            json.dump(self.current_qa_chain_content, f, ensure_ascii=False, indent=2)

    def go_back_to_root(self):
        """Save current chain and reset to root node."""

        root_node_chain_info = {"type": "question", "no": 0}
        # Reset chain variables
        self.current_image_fq_tree[0]["visit_count"] += 1
        self.current_qa_chain_info = [root_node_chain_info]
        self.current_qa_chain = [self.current_image_fq_tree[0]]
        self.current_qa_chain_content = []

        # Reset to root node
        self.current_question_node = self.current_image_fq_tree[0]

    def all_fq_built_tree(self) -> bool:
        """
        Check if all final questions have been processed.

        Returns:
            bool: True if all questions processed, False otherwise
        """
        dir_name, img_name = self._get_image_dir_and_name()
        tree_dir = os.path.join(self.tree_path, dir_name, img_name)

        if not os.path.exists(tree_dir):
            return False

        processed_fqs = set()
        for f in os.listdir(tree_dir):
            if f.startswith("fq_") and f.endswith(".json"):
                try:
                    fq_no = int(f[3:-5])
                    processed_fqs.add(fq_no)
                except:
                    continue

        return len(processed_fqs) == len(self.image_fq)

    def end(self):
        """Clean up and finalize processing for current image."""
        print(f"Completed processing for image: {self.image_path}")

    def main(self, image_path: str = "", context_base_path: str = ""):
        """Main execution flow for the system."""
        try:
            # Initialize
            self.start(image_path, context_base_path)

            # Process image
            self.image_input()

            # Check image compliance
            # if not self.image_judge():
            #     print("The image does not meet the requirements")
            #     return

            # Generate final questions and answers
            self.fq_generate()
            self.fq_answer()

            # Wait for user confirmation
            # print("\nGenerated final questions and answers. Please review them.")
            # print(
            #     f"Final questions saved to: {os.path.join(self.image_fq_path, self._get_image_dir_and_name()[0], self._get_image_dir_and_name()[1] + '.json')}"
            # )
            # print(
            #     f"Final answers saved to: {os.path.join(self.image_fq_answer_path, self._get_image_dir_and_name()[0], self._get_image_dir_and_name()[1] + '.json')}"
            # )

            # while True:
            #     confirm = (
            #         input(
            #             "Have you reviewed and confirmed the final questions and answers? (y/n): "
            #         )
            #         .strip()
            #         .lower()
            #     )
            #     if confirm == "y":
            #         break
            #     elif confirm == "n":
            #         print("Please review the files and try again.")
            #         return
            #     else:
            #         print("Please enter 'y' or 'n'")

            # Process each final question
            while True:
                self.choose_one_fq()
                if self.fq_processed_count > 1:
                    print("Complete!")
                    break
                if not self.current_image_fq:
                    break  # All questions processed

                # Initialize tree for this question
                # self.current_image_fq_tree = [{
                #     "image_path": self.image_path,
                #     "fq_no": self.current_image_fq["fq_no"],
                #     "question_node_no": 0,
                #     "parent_node_no": "None",
                #     "instruction": "None",
                #     "question": "None",
                #     "options": "None",
                #     "capability": "None",
                #     "complexity": "None",
                #     "visit_count": 1,
                #     "victory_count": 0
                # }]
                # self.current_image_fq_tree_answer_action = []
                # self.current_question_node = self.current_image_fq_tree[0]
                #
                # # Initialize chain
                # self.current_qa_chain_info = [{
                #     "type": "question",
                #     "no": 0
                # }]
                # self.current_qa_chain = [self.current_question_node]

                # Build tree for this question
                while True:
                    if (self.current_capability_level == "Decision_support") and (
                        self.answer_fq_judge()
                        or (len(self.current_qa_chain) - 1) >= self.max_chain_node_num
                    ):
                        print("111")
                        # Try to answer final question
                        chain_answer = self.chain_fq_answer()
                        print("222")
                        is_correct = self.answer_judge(
                            chain_answer, self.current_image_fq_answer
                        )
                        print("333")

                        self.current_chain_num += 1

                        if is_correct:
                            print("444")
                            self.backpropagation()
                            print("555")

                        self.save_chain()
                        # Check if we've reached max nodes
                        if self.current_chain_num >= self.max_chain_num:
                            print("666")
                            self.save_tree()
                            print("777")
                            break
                        else:
                            print("888")
                            self.go_back_to_root()
                            print("999")
                    else:
                        if not self.child_num_is_zero():
                            print("101010")
                            if self.sigmoid_sampling_judge():
                                print("111111")
                                self.node_selection()
                                print("121212")
                                self.node_action()
                                print("131313")
                            else:
                                print("141414")
                                self.node_expansion()
                                print("151515")
                                self.node_action()
                                print("161616")
                        else:
                            print("171717")
                            self.node_expansion()
                            print("181818")
                            self.node_action()
                            print("191919")

                break
                # Check if all questions processed
                if self.all_fq_built_tree():
                    print("202020")
                    break

            self.end()

        except Exception as e:
            error_info = {
                "image_path": self.image_path,
                "error": "Main execution failed",
                "exception": str(e),
                "system_state": {
                    "image_background": self.image_background.get(
                        "image_background", "None"
                    ),
                    "analysis_information": self.analysis_information,
                    "context_summarization": self.context_summarization,
                    "image_fq": self.image_fq,
                    "image_fq_answer": self.image_fq_answer,
                    "current_image_fq_tree": self.current_image_fq_tree,
                    "current_qa_chain": self.current_qa_chain,
                },
            }
            self._save_error(error_info)
            print(f"Error in main execution: {str(e)}")

    def main_gfa(self, image_path: str = "", context_base_path: str = ""):
        """Main execution flow for the system."""
        try:
            # Initialize
            self.start(image_path, context_base_path)

            # Process image
            self.image_input()

            # Check image compliance
            # if not self.image_judge():
            #     print("The image does not meet the requirements")
            #     return

            # Generate final questions and answers
            self.fq_generate()
            self.fq_answer()

        except Exception as e:
            error_info = {
                "image_path": self.image_path,
                "error": "Main execution failed",
                "exception": str(e),
                "system_state": {
                    "image_background": self.image_background.get(
                        "image_background", "None"
                    ),
                    "analysis_information": self.analysis_information,
                    "context_summarization": self.context_summarization,
                    "image_fq": self.image_fq,
                    "image_fq_answer": self.image_fq_answer,
                    "current_image_fq_tree": self.current_image_fq_tree,
                    "current_qa_chain": self.current_qa_chain,
                },
            }
            self._save_error(error_info)
            print(f"Error in main execution: {str(e)}")


if __name__ == "__main__":
    system = ImageQASystem()

    # system.main(
    #     image_path=r"F:\AgenticFin_Lab\fttracer_coding_dataset\images\000001\000290.jpg"
    # )

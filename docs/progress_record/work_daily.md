#  This markdown file serves as a record of our daily tasks and advancements.


## August 4 -11, 2025 

1. Yuqun completed the development of the entire new Monte Carlo Tree Search (MCTS)-related code and ensured its smooth operation. With suggestions from Professor Sijia and Yuxuan, continuous optimizations were made to the prompts and code logic.
2. Regarding the application of Monte Carlo Tree Search in this project, there are still pressing issues to address, such as high model invocation costs, slow speed, and susceptibility to errors. We are currently exploring suitable solutions to obtain the required results quickly, efficiently, and accurately.
3. We refactored the entire code structure of fttracer, making it more universal, modular, and standardized. Additionally, we created an architectural diagram of the entire fttracer system to enhance collaboration clarity.
4. Yuxuan made significant progress in crawling, parsing, extracting, analyzing, and summarizing information from books and reports, and successfully implemented the corresponding code.
5. Yuqun established an ICLR paper template library and is preparing to work with Yuxuan and Professor Sijia on the paper writing process.

## July 31 - August 3, 2025

1. Yuxuan continued collecting approximately 400 eligible books and 6,000 related reports.  
2. Yuxuan tested the speed of parsing PDF files using MinerU and found that calling the API was significantly faster than processing locally. Consequently, he decided to directly use the API for PDF processing.  
3. Yuqun completed the collection of over 14,000 economics, finance, and investment-related book materials in PDF format and uploaded them to Huawei Cloud Drive.  
4. Yuqun largely finalized the newly discussed MCTS (Monte Carlo Tree Search) code framework, including 7 prompt templates and a highly flexible modular code structure.  

## July 30, 2025

1. Based on the newly discussed flowchart, Yuqun proceeded to rewrite the program code to achieve greater accuracy and clarity.  
2. Yuxuan noted that many reports from the International Institute of Green Finance at the Central University of Finance and Economics only disclose abstracts rather than full texts, and took the initiative to propose emailing the institute to request the materials.  
3. Yuxuan is going to collect statistics on the speed of parsing PDF files using MinerU.
4. Yuqun renewed the framework of the FttracerBench research.    
5. Professor Sijia pointed out that our approach of working backward from the endgame problem to uncover underlying issues closely resembles the methodology described in "The Pyramid Principle."

![](images/fttracerbench_202507310129.drawio.png)

## July 29, 2025

1. Yuqun drew a detailed flowchart of the entire Monte Carlo Tree Search process (as shown in the figure below) and discussed specific issues with Professor Sijia and Yuxuan, such as option settings. Yuxuan suggested clearly labeling the prompts and VLM indices for better distinction, and Yuqun made revisions based on the feedback.  
2. Yuxuan continued collecting data and closely followed up on the mechanism design of the Monte Carlo Tree Search.    

![](images/node_generate.drawio.png)

## July 28, 2025
**Note: All work was carried out under the close guidance of Professor Sijia, and we would like to express our special thanks to Professor Sijia for his strong support.**   

1. Professor Sijia, Yuxuan, and Yuqun further discussed the entire framework of Monte Carlo Tree Search, identifying issues in the previous framework, such as the lack of consideration for selecting between utilizing existing nodes or exploring new ones. They decided to introduce the Sigmoid function and random sampling to address this flaw. Additionally, they engaged in in-depth and detailed discussions regarding thought chains, endgame problems, node quantities, and level settings, among other aspects.  
2. Yuxuan continued to collect and perform preliminary processing of the data.  

## Jyly 24-27, 2025

1. Yuqun has encapsulated multiple versions of mainstream large-scale models such as Qwen, Doubao, ChatGLM, Hunyuan, Moonshot, and Ernie, facilitating batch invocation and utilization.  
2. Yuxuan has collected approximately 150 foreign textbooks and classical works in the financial field, along with 126 course materials from the MIT OpenCourseWare website.  
3. Yuqun has crafted prompts for each component of Monte Carlo Tree Search and completed a preliminary code framework.  
4. Professor Sijia has provided close academic guidance.  


## July 23, 2025  

1. We discussed how Monte Carlo Tree Search (MCTS) can be applied to the data construction of the project. Specifically, we do not strictly adopt the computational method of MCTS because our task ultimately lacks a clear-cut right-or-wrong conclusion. Instead, our approach draws inspiration from the concept of MCTS to build a large-scale, hierarchically structured, and difficulty-graded question-answer dataset that reflects multidimensional competencies. This dataset will then undergo manual review and refinement to form a final, well-structured benchmark.  
2. Yuxuan will continue to gather broader data sources, with Yuqun providing insights;  
3. Yuqun will be responsible for organizing, coding, and integrating visual understanding models into the agent, as well as implementing Monte Carlo Tree Search.  

## July 22, 2025  

1. Professor Sijia proposed using the Monte Carlo Tree Search (MCTS) approach, combined with prior knowledge and minimal manual design, to construct datasets with large models and select high-quality Q&A pairs based on MCTS.  
2. We focused on learning and researching Monte Carlo Tree Search.
3. We discovered a practical tool for technical analysis: TA-Lib, which can be used to identify simple candlestick chart patterns.
4. Following this approach, we divided tasks for experimentation, aiming to finalize the solution as soon as possible.

## July 21, 2025  

1. Yuqun proposed an experimental method to evaluate the model's ability to interpret line graphs. This method is crucial for this study, as it can precisely measure the extent to which the model truly understands line graphs by adding specific markers such as arrows (similar to the small sticks used in vision tests). Yuxuan supplemented that circles or partial element extraction could also be employed. Professor Sijia expressed agreement.  
2. Yuqun drew a framework diagram and workflow for the project (e.g., the final figure).  
3. Yuxuan collected 144 finance-related books containing images, parsed them using MinerU, and renamed the images as needed for the work.  
4. Yuxuan conducted statistical analysis on the collected books.  
5. We created a data table to record book information, designing nearly 20 fields. This table helps accurately map the corresponding book details.  
6. We organized the data based on the aforementioned table.  
7. We inquired whether the university provides access to key financial journal articles, and Professor Sijia assisted in following up.    
8. Yuqun gathered over 480GB of financial book resources and continues to collect more.    

![](images/FTTracerBench.drawio.png)


## July 20, 2025

1. Profesoor Sijia shared a wechat article to download the transaction data of cryptocurrency.
2. Yuxuan suggested finding insurance related graph data and recommended the iResearch Consulting research platform.
3. Yuqun has compiled approximately 40 research reports or data related source platforms.

## July 19, 2025

1. Yuqun has collected hundreds of finance-related recommended booklists from public channels such as Douban, Zhihu, WeChat public accounts, and other sources, awaiting further organization.  
2. Yuqun has identified download methods for thousands of finance and investment-related books from online sources to acquire image resources.  
3. Yuqun has compiled information on some key platforms for retrieving books (refer to data-retrieval-resources.md).  
4. Yuxuan discovered a method to rapidly obtain a large volume (tens of thousands) of finance-related images and reports from the PISHU database, inspiring us to focus on reports for data collection.  
5. Yuxuan found that the World Bank website hosts a wealth of freely downloadable finance-related resources.  
6. Yuqun proposed that the HangHangCha website contains numerous downloadable research reports and suggested focusing on data collection channels such as investment research reports, industry reports, market reports, and digital currency (stablecoin) platforms.  
7. Professor Sijia assisted in applying for Huawei Cloud resources, securing 2TB of storage space, and confirmed its normal functionality.  
8. Professor Sijia discussed data storage methods with the team, preliminarily planning to build a local server and develop a framework for data storage and management.  
9. Yuxuan retrieved and compiled 48 finance-related books from mainstream platforms, with plans to share them after reaching 100 books.  
10. Yuqun created directories for large model API calls (`llmapis` and `vlmapis`) and initially marked 18 mainstream large model teams (corresponding to 18 Python files). The plan is to consolidate all API calls for each team into a single Python file (considering api-key management). Currently, the code files are empty.  
11. Yuqun organized past materials into over a dozen markdown files and shared them in the relevant repository.  
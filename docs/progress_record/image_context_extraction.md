## Image Context Extraction Specification

---

### 1. Input Structure

```
root/
├── markdown/     # Parsed Markdown text files
├── images/       # Image directories organized by book ID
└── pdf/          # Original PDF files
```

Each book corresponds to:

- `markdown/000001.md` - Parsed text content
- `pdf/000001.pdf` - Original PDF file
- `images/000001/` - All images for this book, named in format `000001.jpg`

Image tag format in Markdown: `![](../images/000001/000001.jpg)`

---

### 2. Image Classification Rules

We classify images into three categories based on caption matching and nearby image analysis:

#### Caption Matching Scenarios (A)

Analysis of captions found within x + N lines around the image tag:

- **A-0**: No captions matched
- **A-1**: Exactly one caption matched  
- **A-2**: Multiple captions matched

#### Nearby Image Scenarios (B)

Analysis of other images found within x + M lines around the current image:

- **B-0**: No other images found
- **B-1**: Other images present

#### Classification Logic

- **Normal**: A-1 + B-0 (One caption matched, no other images nearby)
- **Abnormal**: A-1 + B-1 or A-2 (One caption with nearby images, or multiple captions)
- **Extreme Abnormal**: A-0 (No captions found)

---

### 3. JSON Output Format

Each JSON file contains a list of image entries with the following fields:

#### Main Image Information

- **classification** (str): Image quality classification based on caption and image proximity analysis
  - `"normal"`: Image with exactly one caption and no other nearby images
  - `"abnormal"`: Image with exactly one caption but other images present nearby  
  - `"extreme_abnormal"`: Image with no captions found in search range
- **book_id** (str): Unique identifier for the book (e.g., "000278")
- **image_filename** (str): Name of the image file (e.g., "000001.jpg")
- **image_tag_line_number** (int): Zero-based line number where the image tag appears in the Markdown file
- **image_surround_text** (str): Surrounding textual context centered on the image tag’s character position

#### Nearby Images Analysis

- **other_images_nearby** (dict): Information about other image tags found near this image within search range
  - **count** (int): Number of other images found in the search range
  - **images** (list[dict]): List of other image information found nearby
    - **line_number** (int): Zero-based line number where the nearby image tag was found
    - **content** (str): The complete content of the found image tag
    - **distance** (int): The line distance (in lines) between this image and the found image

#### Caption Analysis

- **caption_count** (int): Number of captions found near the image within search range
- **captions_found** (list[dict]): List of all caption texts found in the search range using expanding search strategy
  - **content** (str): The raw caption text extracted from the Markdown
  - **content_paragraph** (str): The complete paragraph containing the caption
  - **line_number** (int): Zero-based line number where the caption was found
  - **distance** (int): The line distance (in lines) between this image and the caption
- **nearest_caption** (str): The caption text closest to the image tag, empty string if no captions found

#### Reference Analysis

- **caption_references** (list[dict]): List of image references associated with this image through pattern matching
  - **caption** (str): The caption text that contains the figure references
  - **figure_number** (str): The extracted figure identifier (e.g., "Figure 1", "图1")
  - **reference_count** (int): Total number of references found for this figure
  - **references** (list[dict]): Detailed information about each individual reference found
    - **reference_text** (list[str]): The exact text of the references (e.g., ["Figure 1", "图1"])
    - **is_exact_match** (bool): Boolean indicating if reference exactly matches the figure_number
    - **match_line_info** (dict): Location information about where the reference was found
      - **line_number** (int): Zero-based line number where the reference was found
      - **content** (str): The complete line content containing the reference
      - **char_position_in_paragraph** (int): Character position of reference within the paragraph
    - **reference_paragraph** (str): The complete paragraph containing this reference
    - **reference_paragraph_extension** (str): Extended context around the reference paragraph
    - **total_lines_in_paragraph** (int): Total number of lines in the reference paragraph
- **total_reference_count** (int): Total number of figure references found across all captions for this image

---

### 4. Examples

#### Normal

##### A-1 + B-0 (One caption matched, no other images nearby)

```Json
  {
    "classification": "normal",
    "book_id": "000079",
    "image_filename": "000002.jpg",
    "image_tag_line_number": 283,
    "image_surround_text": "These brief case studies show the utility of the Quick Costing Tool in diverse contexts, for different programs designs, and at various stages of the program implementation cycle.\n\n# PANAMA:STRENGTHENINGTHE NATIONALSOCIALPROTECTION AND INCLUSI
    ...
    transfers representing 66 percent of the cost1° and asset transfers 16 percent (figure 2).\n\n![](../images/000079/000002.jpg)  \nFigure 2 Breakdown of costs of Panama's Strengthening the National Social Protection and Inclusion System Program (percent of total)",
    "other_images_nearby": {
      "count": 0,
      "images": []
    },
    "caption_count": 1,
    "captions_found": [
      {
        "content": "Figure 2 Breakdown of costs of Panama's Strengthening the National Social Protection and Inclusion System Program (percent of total)",
        "content_paragraph": "The costing tool was used ex post to analyze the cost per beneficiary and identify cost drivers. Total budget expenditure for the EI pilot was about $\\mathrm { U S } \\$ 1.8$ million (all figures in 2O17 PPP). The estimate of the cost per beneficiary included $\\mathrm { U S S 3 . 7 }$ million in direct cash transfers.At a total cost of $\\mathrm { U S S 5 . 5 }$ million and 3,087 direct beneficiaries' households, the total cost per beneficiary household was $\\mathrm { U S } \\$ 1,825$ (figure 3) over two years of program delivery. Removing the cash transfers from the unit cost estimations reduces the cost to $\\mathrm { U S S 6 0 7 }$ per beneficiary household.\n\nAbout 82 percent of the program cost reached beneficiaries directly in the form of financial support, with cash transfers representing 66 percent of the cost1° and asset transfers 16 percent (figure 2).\n\n![](../images/000079/000002.jpg)  \nFigure 2 Breakdown of costs of Panama's Strengthening the National Social Protection and Inclusion System Program (percent of total)",
        "line_number": 284,
        "distance": 1
      }
    ],
    "nearest_caption": "Figure 2 Breakdown of costs of Panama's Strengthening the National Social Protection and Inclusion System Program (percent of total)",
    "caption_references": [
      {
        "caption": "Figure 2 Breakdown of costs of Panama's Strengthening the National Social Protection and Inclusion System Program (percent of total)",
        "figure_number": "Figure 2",
        "reference_count": 1,
        "references": [
          {
            "reference_text": [
              "figure 2"
            ],
            "is_exact_match": true,
            "match_line_info": {
              "line_number": 282,
              "content": "About 82 percent of the program cost reached beneficiaries directly in the form of financial support, with cash transfers representing 66 percent of the cost1° and asset transfers 16 percent (figure 2).",
              "char_position_in_paragraph": 192
            },
            "reference_paragraph": "About 82 percent of the program cost reached beneficiaries directly in the form of financial support, with cash transfers representing 66 percent of the cost1° and asset transfers 16 percent (figure 2).",
            "reference_paragraph_extension": "Training combined two types of skills modules: (a) a life-skills training module to help beneficiaries in specific behavioral, psychosocial, and remedial activities and (b) a technical skill module focused on specific entrepreneurship activities. Training services were delivered through farmer field schools, using a learning-by-doing model.\n\nCoaching: Thelocal staff of INADEH provided coaching services to program participants.\n\nThe costing tool was used ex post to analyze the cost per beneficiary and identify cost drivers. Total budget expenditure for the EI pilot was about $\\mathrm { U S } \\$ 1.8$ million (all figures in 2O17 PPP). The estimate of the cost per beneficiary included $\\mathrm { U S S 3 . 7 }$ million in direct cash transfers.At a total cost of $\\mathrm { U S S 5 . 5 }$ million and 3,087 direct beneficiaries' households, the total cost per beneficiary household was $\\mathrm { U S } \\$ 1,825$ (figure 3) over two years of program delivery. Removing the cash transfers from the unit cost estimations reduces the cost to $\\mathrm { U S S 6 0 7 }$ per beneficiary household.\n\nAbout 82 percent of the program cost reached beneficiaries directly in the form of financial support, with cash transfers representing 66 percent of the cost1° and asset transfers 16 percent (figure 2).",
            "total_lines_in_paragraph": 1
          }
        ]
      }
    ],
    "total_reference_count": 1
  },
```

#### Abnormal

##### A-1 + B-1 (One caption with nearby images)

```Json
  {
    "classification": "abnormal",
    "book_id": "000015",
    "image_filename": "000013.jpg",
    "image_tag_line_number": 159,
    "image_surround_text": "# < L\n# Burkina Faso\n# ECONOMIC UPDATE\n# Special Chapter\nBuilding Financial Resilience to Climate Risks\n# 2023BURKINA FASO ECONOMICUPDATE\nSpecial Chapter: Building Financial Resilience to Climate Risks\nApril2023\nThis WorkisaproductofthestaffofThe WorldBankwithexternalcontributions.Thefindings,interpretations,andconclusionsexpressdinthisworkdonotnecessarilyreflect theviewsofTheWorldBank,itsBoardofExecutiveDirectors,orthe governments they represent.\nTheWorldBankdoesnotguarantee theaccuracycompleteness,orcurrencyofthedataincludedinthisworkanddoes not assumeresponsiblitforyrorsmissions,ordscrepanciesintinformationrliablit
    ...
    .org /country/burkina-faso/vulnerability. \nWorld Bank (2023d).Global Economic Prospects, January 2023.Global Economic Prospects.http:// hdl.handle.net/10986/38030.\nZongo,Y.(2019). Fonds national de solidarité:Les contributions sont les bienvenues. LeFaso.https:// lefaso.net/spip.php?article90474.",
    "other_images_nearby": {
      "count": 1,
      "images": [
        {
          "line_number": 157,
          "content": "![](../images/000015/000012.jpg)",
          "distance": 2
        }
      ]
    },
    "caption_count": 1,
    "captions_found": [
      {
        "content": "FIGURE1.14 The Richer Deciles Usually Benefit More from Average Welfare Growth, although the Poorest Households Are Somewhat Shielded from Inflation",
        "content_paragraph": "# < L\n# Burkina Faso\n# ECONOMIC UPDATE\n# Special Chapter\nBuilding Financial Resilience to Climate Risks\n# 2023BURKINA FASO ECONOMICUPDATE\nSpecial Chapter: Building Financial Resilience to Climate Risks\nApril2023\nThis WorkisaproductofthestaffofThe WorldBankwithexternalcontributions.Thefindings,interpretations,andconclusionsexpressdinth
        ...
        Country Profile Burkina Faso. Climate Change KnowledgePortal. https://climateknowledgeportal.worldbank.org /country/burkina-faso/vulnerability. \nWorld Bank (2023d).Global Economic Prospects, January 2023.Global Economic Prospects.http:// hdl.handle.net/10986/38030.\nZongo,Y.(2019). Fonds national de solidarité:Les contributions sont les bienvenues. LeFaso.https:// lefaso.net/spip.php?article90474.",
        "line_number": 161,
        "distance": 2
      }
    ],
    "nearest_caption": "FIGURE1.14 The Richer Deciles Usually Benefit More from Average Welfare Growth, although the Poorest Households Are Somewhat Shielded from Inflation",
    "caption_references": [
      {
        "caption": "FIGURE1.14 The Richer Deciles Usually Benefit More from Average Welfare Growth, although the Poorest Households Are Somewhat Shielded from Inflation",
        "figure_number": "FIGURE1.14",
        "reference_count": 0,
        "references": []
      }
    ],
    "total_reference_count": 0
  },
```

##### A-2 (multiple captions)

```Json
  {
    "classification": "abnormal",
    "book_id": "000001",
    "image_filename": "000033.jpg",
    "image_tag_line_number": 314,
    "image_surround_text": "从供给端看，基层服务能力不足是农业保险渗透率低的主要因素之一。在西部某省调研过程中，课题组发现尽管该省以“投保到户、定损到户、理赔到户”为目标，按照“一村一室、集中统一、综合服务”的原则，建立执行乡村干部、银行保险机构业务员、公益岗位农金员共同参与的运营机制，然而从实施效果来看，
    ...
    已有的政策性农业保险的基础上，购买农业气象指数保险作为补充（图4.5）。\n\n84%i 52%42%33%21%5% 4%旱灾 风灾 办 冰雹 雾霾 连阴雨 化 其他持续低温冻害\n\n![](../images/000001/000038.jpg)  \n图4.4受访农户面临的主要气象灾害  \n图4.5如果已经购买了农业保险，是否愿意额外购买农业气象指数保险作为补充\n\n# 第五章 发展农业气象指数保险的建议\n\n![](../images/000001/000039.jpg)\n\n# 第五章 发展农业气象指数保险的建议\n\n近年来，中国政府持续将乡村振兴、解决三农问题纳入国家战略，为农业、农民和农村相关的保险市场带来巨大的发展机遇。其中，农业保险为农业发展以及粮食安全保驾护航，属于政府主导、政策推动型险种。农业气象指数保险作为一种创新型农业保险产品，能够有效帮助农业经营主体降低因气象灾害带来的风险，从而提高收入。成功推广农业气象指数保险需要联动政府、金融机构、业内专家、保险公司、科技公司、农业经营主体等在内的利益相关者，使各参与方形成合力，共同打造中国创新数字农险样板。",
    "other_images_nearby": {
      "count": 0,
      "images": []
    },
    "caption_count": 2,
    "captions_found": [
      {
        "content": "图3.6如果没有政府补贴，您是否还会购买农业保险",
        "content_paragraph": "目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。\n\n![](../images/000001/000033.jpg)  \n图3.6如果没有政府补贴，您是否还会购买农业保险\n\n相对而言，经营主体的参保意愿更强些。在课题组与江苏太仓蔬菜种植基地和养殖扶贫车间的两位负责人进行访谈时，他们表示对农业保险有强烈的参保意愿，能购买的农业保险品种都全部购买，他们甚至提出希望缴付更高额的保费以获得更高保障。调研发现，经营主体（如蔬菜种植基地）与农户的互动频繁，可发挥其带动相关农户参保的效应。\n\n从供给端看，部分地方政府财力不足无力配套是导致农业保险供给不足的主要因素之一。中央和地方财政给予农业保险经营补贴是过去我国农业保险蓬勃发展的第一推动力。然而，部分地方的农业支柱产业为特色蔬菜、水果，不在中央财政补贴范围内，单靠省里的财力不能满足补贴需求，因而无法广泛推行。即便属于中央财政补贴范围，且很多农民也想参加农业保险，但是因为县里缺乏配套补贴资金而难以拿到省里和中央的财政补贴，或者给投保农户提供的保费补贴比例较低，就会负面影响到这些地方发展农业保险的积极性。",
        "line_number": 315,
        "distance": 1
      },
      {
        "content": "图3.5不同农业收入占比的家庭是否购买了农业保险的情况",
        "content_paragraph": "家庭收入水平决定着农户对农业保险保费的承受能力。回归结果显示，农业收入占家庭年总收入比重越高，农民投保农业保险的意愿越强烈（表3.2；图3.5）。这是因为农业收入占家庭收入的比重越高，说明其选择其他非农业生产方式的可能性越小，农业收入直接影响到家庭的生活质量，这样的家庭经不起农业风险的冲击。但是数据也显示，部分农业收入占家庭收入比重在 $90 \\%$ 的农民反而投保农业保险的意愿没有其他人强烈。通过访谈了解到，这主要是因为这些家庭的收入较低，没有余钱投保农业保险。此外，农户收入结构对于农民购买农业保险的需求也有一定影响。工资性收入比重较高的农民家庭，有稳定的工资性收入作为风险保障工具，对农业经营的收入依赖程度较低，因此对农业保险的购买意愿不高。而农业经营收入比重较高的家庭更依赖于农业经营的稳定性，主观上更愿意购买农业保险。因此，进一步发展农村经济，提高农民收入水平，可为有效推广农业保险奠定经济基础。\n\n![](../images/000001/000032.jpg)  \n图3.5不同农业收入占比的家庭是否购买了农业保险的情况\n\n# 3.4财政补贴直接影响农业保险的需求和供给\n\n目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。",
        "line_number": 308,
        "distance": 6
      }
    ],
    "nearest_caption": "图3.6如果没有政府补贴，您是否还会购买农业保险",
    "caption_references": [
      {
        "caption": "图3.6如果没有政府补贴，您是否还会购买农业保险",
        "figure_number": "图3.6",
        "reference_count": 1,
        "references": [
          {
            "reference_text": [
              "图3.6"
            ],
            "is_exact_match": true,
            "match_line_info": {
              "line_number": 313,
              "content": "目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。",
              "char_position_in_paragraph": 104
            },
            "reference_paragraph": "目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。",
            "reference_paragraph_extension": "# 3.3农户收入水平和结构显著影响其农业保险需求\n\n家庭收入水平决定着农户对农业保险保费的承受能力。回归结果显示，农业收入占家庭年总收入比重越高，农民投保农业保险的意愿越强烈（表3.2；图3.5）。这是因为农业收入占家庭收入的比重越高，说明其选择其他非农业生产方式的可能性越小，农业收入直接影响到家庭的生活质量，这样的家庭经不起农业风险的冲击。但是数据也显示，部分农业收入占家庭收入比重在 $90 \\%$ 的农民反而投保农业保险的意愿没有其他人强烈。通过访谈了解到，这主要是因为这些家庭的收入较低，没有余钱投保农业保险。此外，农户收入结构对于农民购买农业保险的需求也有一定影响。工资性收入比重较高的农民家庭，有稳定的工资性收入作为风险保障工具，对农业经营的收入依赖程度较低，因此对农业保险的购买意愿不高。而农业经营收入比重较高的家庭更依赖于农业经营的稳定性，主观上更愿意购买农业保险。因此，进一步发展农村经济，提高农民收入水平，可为有效推广农业保险奠定经济基础。\n\n![](../images/000001/000032.jpg)  \n图3.5不同农业收入占比的家庭是否购买了农业保险的情况\n\n# 3.4财政补贴直接影响农业保险的需求和供给\n\n目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。\n\n![](../images/000001/000033.jpg)  \n图3.6如果没有政府补贴，您是否还会购买农业保险\n\n相对而言，经营主体的参保意愿更强些。在课题组与江苏太仓蔬菜种植基地和养殖扶贫车间的两位负责人进行访谈时，他们表示对农业保险有强烈的参保意愿，能购买的农业保险品种都全部购买，他们甚至提出希望缴付更高额的保费以获得更高保障。调研发现，经营主体（如蔬菜种植基地）与农户的互动频繁，可发挥其带动相关农户参保的效应。\n\n从供给端看，部分地方政府财力不足无力配套是导致农业保险供给不足的主要因素之一。中央和地方财政给予农业保险经营补贴是过去我国农业保险蓬勃发展的第一推动力。然而，部分地方的农业支柱产业为特色蔬菜、水果，不在中央财政补贴范围内，单靠省里的财力不能满足补贴需求，因而无法广泛推行。即便属于中央财政补贴范围，且很多农民也想参加农业保险，但是因为县里缺乏配套补贴资金而难以拿到省里和中央的财政补贴，或者给投保农户提供的保费补贴比例较低，就会负面影响到这些地方发展农业保险的积极性。\n\n# 第四章 农业气象指数保险有效补充农村金融服务体系\n\n![](../images/000001/000034.jpg)",
            "total_lines_in_paragraph": 1
          }
        ]
      },
      {
        "caption": "图3.5不同农业收入占比的家庭是否购买了农业保险的情况",
        "figure_number": "图3.5",
        "reference_count": 1,
        "references": [
          {
            "reference_text": [
              "图3.5"
            ],
            "is_exact_match": true,
            "match_line_info": {
              "line_number": 306,
              "content": "家庭收入水平决定着农户对农业保险保费的承受能力。回归结果显示，农业收入占家庭年总收入比重越高，农民投保农业保险的意愿越强烈（表3.2；图3.5）。这是因为农业收入占家庭收入的比重越高，说明其选择其他非农业生产方式的可能性越小，农业收入直接影响到家庭的生活质量，这样的家庭经不起农业风险的冲击。但是数据也显示，部分农业收入占家庭收入比重在 $90 \\%$ 的农民反而投保农业保险的意愿没有其他人强烈。通过访谈了解到，这主要是因为这些家庭的收入较低，没有余钱投保农业保险。此外，农户收入结构对于农民购买农业保险的需求也有一定影响。工资性收入比重较高的农民家庭，有稳定的工资性收入作为风险保障工具，对农业经营的收入依赖程度较低，因此对农业保险的购买意愿不高。而农业经营收入比重较高的家庭更依赖于农业经营的稳定性，主观上更愿意购买农业保险。因此，进一步发展农村经济，提高农民收入水平，可为有效推广农业保险奠定经济基础。",
              "char_position_in_paragraph": 67
            },
            "reference_paragraph": "家庭收入水平决定着农户对农业保险保费的承受能力。回归结果显示，农业收入占家庭年总收入比重越高，农民投保农业保险的意愿越强烈（表3.2；图3.5）。这是因为农业收入占家庭收入的比重越高，说明其选择其他非农业生产方式的可能性越小，农业收入直接影响到家庭的生活质量，这样的家庭经不起农业风险的冲击。但是数据也显示，部分农业收入占家庭收入比重在 $90 \\%$ 的农民反而投保农业保险的意愿没有其他人强烈。通过访谈了解到，这主要是因为这些家庭的收入较低，没有余钱投保农业保险。此外，农户收入结构对于农民购买农业保险的需求也有一定影响。工资性收入比重较高的农民家庭，有稳定的工资性收入作为风险保障工具，对农业经营的收入依赖程度较低，因此对农业保险的购买意愿不高。而农业经营收入比重较高的家庭更依赖于农业经营的稳定性，主观上更愿意购买农业保险。因此，进一步发展农村经济，提高农民收入水平，可为有效推广农业保险奠定经济基础。",
            "reference_paragraph_extension": "![](../images/000001/000031.jpg)  \n图3.4 买的农业保险不满意的原因\n\n从供给端看，保险公司承保积极性不足是造成农业保险客户满意度低的主要原因。而导致保险公司承保积极性受挫的主要原因则是农业保险经营的长期亏损、监管过度干预以及知识产权保护机制的缺乏。农业保险具有“两高”属性，即由自然灾害和市场波动风险造成的“高赔付率”和承保理赔所需的大量人力物力造成的“高费用率”。因此，经营农业保险产品往往难以商业获利。尽管政府对专业农险公司的业务支持力度较大，但另一方面也存在对农险业务运行直接干预、相关部门之间利益冲突的问题。基层地方政府、农业畜牧部门、财政部门等在参与农业保险不同环节工作中，均缺乏有效的约束监督机制，各行其是、各自为政的现象较为突出，为保险公司的经营带来负面影响。此外，我国支持和保护新险种创新开发的相关法律法规相对匮乏，农业保险市场上的大量同质产品仅在形式上有差别，本质无异，难以满足农户的个性化需求，保险机构在同类险种招标过程中容易滋生寻租、腐败等问题，严重影响市场公平。农险知识产权保护法律亟待完善，以加快推动新险种开发进程，扩大农业保险覆盖面。 V\n\n# 3.3农户收入水平和结构显著影响其农业保险需求\n\n家庭收入水平决定着农户对农业保险保费的承受能力。回归结果显示，农业收入占家庭年总收入比重越高，农民投保农业保险的意愿越强烈（表3.2；图3.5）。这是因为农业收入占家庭收入的比重越高，说明其选择其他非农业生产方式的可能性越小，农业收入直接影响到家庭的生活质量，这样的家庭经不起农业风险的冲击。但是数据也显示，部分农业收入占家庭收入比重在 $90 \\%$ 的农民反而投保农业保险的意愿没有其他人强烈。通过访谈了解到，这主要是因为这些家庭的收入较低，没有余钱投保农业保险。此外，农户收入结构对于农民购买农业保险的需求也有一定影响。工资性收入比重较高的农民家庭，有稳定的工资性收入作为风险保障工具，对农业经营的收入依赖程度较低，因此对农业保险的购买意愿不高。而农业经营收入比重较高的家庭更依赖于农业经营的稳定性，主观上更愿意购买农业保险。因此，进一步发展农村经济，提高农民收入水平，可为有效推广农业保险奠定经济基础。\n\n![](../images/000001/000032.jpg)  \n图3.5不同农业收入占比的家庭是否购买了农业保险的情况\n\n# 3.4财政补贴直接影响农业保险的需求和供给\n\n目前我国大多数农业保险产品都是政策性保险产品，可获得中央和地方多级政府部门的大力补贴。当问到如果没有政府补贴是否还会购买农业保险时，超过半数（ $5 3 \\%$ ）的受访者表示没有政府补贴则不会购买农业保险（图3.6）。回归结果也显示，政府对农业保险的补贴与农户购买农业保险的需求呈正相关（表3.2）。由此可见，财政补贴对于农业保险需求影响显著。胡炳志（2009）‘认为，财政补贴对农业保险需求的影响主要表现为相对保单价格的变动所产生的替代效应以及相对农户收入水平的变动所产生的收入效应。在推广普及新型农业保险产品阶段，加大政府部门财政投入力度可有效提升农户对农业保险的接受度。\n\n![](../images/000001/000033.jpg)  \n图3.6如果没有政府补贴，您是否还会购买农业保险\n\n相对而言，经营主体的参保意愿更强些。在课题组与江苏太仓蔬菜种植基地和养殖扶贫车间的两位负责人进行访谈时，他们表示对农业保险有强烈的参保意愿，能购买的农业保险品种都全部购买，他们甚至提出希望缴付更高额的保费以获得更高保障。调研发现，经营主体（如蔬菜种植基地）与农户的互动频繁，可发挥其带动相关农户参保的效应。",
            "total_lines_in_paragraph": 1
          }
        ]
      }
    ],
    "total_reference_count": 2
  },
```

#### Extreme Abnormal

##### A-0 (No captions found)

```Json
  {
    "classification": "extreme abnormal",
    "book_id": "000001",
    "image_filename": "000002.jpg",
    "image_tag_line_number": 48,
    "image_surround_text": "![](../images/000001/000001.jpg)\n\n# 发展农业气象指数保险优化农村金融服务体系调研报告\n\n2021年12月\n\n本报告得到了世界银行集团国际金融公司（IFC）、英国驻华大使馆和匈牙利进出口银行的支持与协助，谨此表示感谢！\n\n# 免责声明\n\n本报告由中国普惠金融研究院课题组成员根据当前认为可靠的信息撰写，报告中所提供的信息仅供参考。中国普惠金融研究院不保证本报告所载资料来源及观点出处绝对准确和完整，也不对因使用本报告材料而引起的损失承担任何法律责任。本报告所载信息、意见、推算及预测仅反映课题组成员于报告发布当日的判断，并不一定反映中国普惠金融研究院或其合作伙伴的观点。
    ...
    保互动，大力发展“信贷 $^ +$ 农业保险\"模式可有效缓解此类问题。一方面，农业保险作为担保品替代信号，能够有效缓解农户所受信贷配给约束，增加其信贷可得性与信贷额度；另一方面，农业保险也可受益于农村信贷扩张所带来的农户收入水平提高，从而推动农业保险有效需求增长。\n\n注重数字科技赋能，可有效推动农业气象指数保险长足发展。农业气象指数保险产品设计需要长序列的历史气象数据、理赔数据和农作物产量数据作为支撑，以确定气象指数和农作物产量间的相关关系和赔付标准。数据的准确性和科学性直接关系到费率厘定的合理性，不准确的数据将导致定价偏差与理赔基差风险。而目前中国则面临着农业生产经营者的基础信息和生产过程中农情灾情气象信息等难以归集和利用的问题。依托政府部门间合作与财政支持，可切实完善辖区内气象观测站、统计调查团队和气象数据库建设，最终实现农业气象指数保险的高效健康发展。则面临着农业生产经营者的基础信息和生产过程中农情灾情气象信息等难以归集和利用的问题。因此，政府支持建立完备气象观测站、统计调查团队、气象数据库等就尤为重要，可以促进农业气象指数保险更有效地发展。",
    "other_images_nearby": {
      "count": 0,
      "images": []
    },
    "caption_count": 0,
    "captions_found": [],
    "nearest_caption": "",
    "caption_references": [],
    "total_reference_count": 0
  },
```

---

### 5. Image Context Extraction Pipeline

#### 5.1. Preprocessing Stage

- Scan the Markdown file and remove figure directory sections (to avoid interference in subsequent `Reference` extraction). If a figure directory exists, return the text content with the figure directory removed. If no figure directory exists, return the complete text content.
- Remove useless HTML tags and normalize whitespace.
- **Generated JSON fields in this stage**:
  - `'book_id'`: Extracted from the file path (e.g., from `markdown/000001.md` → `"000001"`)
  - `'image_filename'`: Derived from the current image being processed (e.g., `"000001.jpg"`)

#### 5.2. Caption Extraction Stage

- Locate each image tag in the Markdown content using the pattern `![](../images/{book_id}/{image_filename})`
- Record the `'image_tag_line_number'` (zero-based line number) where the image tag is found
- Extract the surrounding textual context `image_surround_context` centered on the image tag’s character position. When no clear caption or reference exists (abnormal/extreme-abnormal image), the surrounding context becomes the sole context fed to models.

- Apply expanding search strategy: starting from the current image tag, search adjacent lines (n=1), then expand to n=2, n=3, etc., until n=x where no captions are found. Then search the range [x+1, x+N] for final attempt.
- **Generated JSON fields in this stage**:
  - `'image_tag_line_number'`: The line number of the image tag
  - `'image_surround_context'`: The surrounding context centered on the image tag
  - `'other_images_nearby'`: Information about nearby images:
    - `'count'`: Number of other images found in search range
    - `'images'`: Array of nearby image details:
      - `'line_number'`: Line number of nearby image tag
      - `'content'`: Complete content of the nearby image tag
      - `'distance'`: Distance from current image to nearby image
  - `'caption_count'`: Count of all captions found during search
  - `'captions_found'`: Array containing all discovered captions with details:
    - `'content'`: Raw caption text extracted
    - `'content_paragraph'`: Complete paragraph containing the caption
    - `'line_number'`: Zero-based line number where caption was found
    - `'distance'`: Line distance from image tag to caption
  - `'nearest_caption'`: The caption with minimum distance to the image tag

#### 5.3. Image Classification Stage

- Classify each image based on caption and nearby image analysis:
  - **`"normal"`**: Exactly one caption found (`'caption_count'` = 1) and no other images nearby (`'other_images_nearby.count'` = 0)
  - **`"abnormal"`**: 
    - Exactly one caption found (`'caption_count'` = 1) but other images present nearby (`'other_images_nearby.count'` > 0)
    - Exactly more than one caption found (`'caption_count'` > 1)
  - **`"extreme_abnormal"`**: No captions found in search range (`'caption_count'` = 0)
- **Generated JSON fields in this stage**:
  - `'classification'`: Final classification result based on the rules above

#### 5.4. Reference Extraction Stage

- For each identified caption, extract the figure identifier (`'figure_number'`) using pattern matching
- Search the entire document for references to this figure
- Compare reference positions with original caption position - only save references that are in different locations
- **Generated JSON fields in this stage**:
  - `'caption_references'`: Array of reference information for each caption:
    - `'caption'`: The original caption text containing figure identifiers
    - `'figure_number'`: Extracted figure identifier (e.g., "图1", "Figure 1")
    - `'reference_count'`: Total number of references found for this figure
    - `'references'`: Detailed array of individual references:
      - `'reference_text'`: Array of exact reference texts found
      - `'is_exact_match'`: Boolean indicating if reference exactly matches `'figure_number'`
      - `'match_line_info'`: Location details of the reference:
        - `'line_number'`: Zero-based line number where reference was found
        - `'content'`: Complete line content containing the reference
        - `'char_position_in_paragraph'`: Character position within the paragraph
      - `'reference_paragraph'`: Complete paragraph containing the reference
      - `'reference_paragraph_extension'`: Extended context around the reference paragraph (ensuring minimum k characters and complete paragraphs)
      - `'total_lines_in_paragraph'`: Total number of lines in the reference paragraph
  - `'total_reference_count'`: Sum of all `'reference_count'` values across all captions for this image

#### 5.5. Output Generation Stage

- Compile all extracted information into a structured JSON object for each image
- Save the JSON file to `{input_dir}/output/context/{book_id}.json`
- Each JSON file contains an array of image entry objects with all the fields described above

---

### 6. Special Case Handling

6.1. **Mixed Caption and Tag**: multiple image tags and captions are interleaved, making it difficult to establish correspondence

- Solution: Unable to establish correspondence between images and captions, no solution available for now

- Example:

```
![](images/000001/000001.jpg)

图1 xxxxxxx

图2 xxxxxx

图3 xxxxxx

![](images/000001/000002.jpg)

图4 xxxxxx

![](images/000001/000003.jpg)

![](images/000001/000004.jpg)
```

6.2. **No Standard Captions**: covers, author photos, and other unnumbered figures  

- Solution: Match the nearest valid caption (e.g., "Figure 1") as a potential caption; if multiple captions exist, mark as *abnormal*; if no captions exist, mark as *extreme abnormal*  

- Example:
  
```
# INVESTMENTS

10th Edition

# 推荐阅读

![](images/e782d86fc37ea801b9079319d9780b458d47a22a3f13bd143cbb43c59b9a29cb.jpg)

![](images/053af0cec89d6c8b73f9a68864f0b1fa971cc159fb8a2c129366fbbc8df13fdb.jpg)

![](images/c29c5b640785c24f016f48c6eb2e527b37bd6d09af5133dcfd751a433aaedaa6.jpg)

INVESTMENTS

10th Edition

投资学

(原书第10版)

[美] 淡维·博迪(Zvi Bodie) 亚历克斯·凯恩(Alex Kane) 艾伦·马库斯(Alan J. Marcus) 著  波士顿大学 加利福尼亚大学 波士顿学院

汪昌云 张永骥 译

```
6.3. **Mixed Chart and Figure Numbering**: such as "Chart 1", "Chart 2", but only extract figures  

- Solution: Abandon processing charts, only focus on extracting the context of figures  

- Example:
```

图表1 xxx
图表2 xxx

```
6.4. **Section-Based Numbering Reset**: different sections all restart numbering from "Figure 1"  

  - Solution: Within the section, only search for the nearest caption as a potential match; if multiple captions are found, save all of them  

  - Example:
```

第一章

![](images/000001/000001.jpg)

图1 xxxxxxx

![](images/000001/000002.jpg)

图2 xxxxxxx

![](images/000001/000003.jpg)

图3 xxxxxxx

![](images/000001/000004.jpg)

图4 xxxxxxx

第二章

![](images/000001/000007.jpg)

图1 xxxxxxx

![](images/000001/000008.jpg)

图2 xxxxxxx

![](images/000001/000009.jpg)

图3 xxxxxxx

```
6.5. **Abnormal Caption Placement**: captions may appear above, below, or beside images with inconsistent positioning  

  - Solution: Within the section, search for the nearest caption as a potential match; if multiple captions exist, mark as *abnormal*; if only one exists, mark as *normal*; if no caption exists, treat as *extreme abnormal*  

  - Example:
```

  ![](images/dd44b272563417362d19ea519c9a1b0637f6c100fb642aaa1ee7e3a14b953501.jpg)  
  图3-4 PayMobile公司价值的增加

  图3-5 股票首次公开发行的法定程序  
  ![](images/54232ac709df3523ab1623474e747f6782bbaf2943cecea1f45afdd7a633aa17.jpg)  
  资料来源：Swedbank.

```

```

# 17.6 行业分析

与宏观经济分析出于同样的原因, 行业分析必不可少。因为当宏观经济状况不佳时, 行业很难表现良好, 处于一个危机重重的行业, 公司通常也举步维艰。我们发现不同国家的宏观经济状况千差万别, 各个行业的业绩也各不相同。图17- 6列示了各个行业的不同业绩。该图列示了2013年主要行业的净资产收益率。由图可知, 净资产收益率波动很大, 货币中心银行为  $6.7\%$  , 而餐饮行业为  $29.6\%$  。

图17-6 2012年行业净资产收益率  
![](images/e1eee9a8eb789c06f042e26cd09285590cdadf88f7efd384fc33db2968ed9d93.jpg)  
资料来源：Yahoo!Finance,finance.yahoo.com,September12,2012.

考虑到各行业收益率各不相同,它们在股票市场的表现各异也就理所应当了。图17- 7列出了图17- 6中包含的行业的股市表现。广泛地讲情况是异常的,在家庭改进行业的涨幅为  $57.3\%$  的同时,石油和天然气行业的涨幅只有  $2.6\%$  。这种情况的范围之广甚至涵盖了2012年的所有投资者。回想一下,iShares是保障股票等交易中小型投资者在每个交易行业地位的交易所交易基金(见第4章)。另外,投资者也可以对一个行业的共同基金进行投资。例如,富达提供了超过40种部门基金,每一种都是针对特定行业的。

![](images/c70dbefe45778f9ff5917d71eb6bc44adbed5d135b81e0c1a01293195894a847.jpg)  
图17-7 2012年行业股票价格表现

```

```

![](images/851a946c6e86e3aae406f6d5b6b47ee3ad6b4de4c4dbe54221a7dea7bdcfc79a.jpg)

图4.12 大多数有效的趋势线与水平方向大约成  $45^{\circ}$  角（线2）。如果趋势线过于陡峭（线1），则通常意味着这种上升速度难以持久。而如果趋势线过于平缓（线3），则说明相应的上升趋势过于衰弱，可能是靠不住的。不少技术分析者将从先前的顶点或底点引出的 $45^{\circ}$  直线作为主要的趋势线。

图4.13 趋势线（线1）过于陡峭的例子。事实证明，原来的上升趋势线过于陡峭。经常地，当陡峭的趋势线被突破后，仅仅意味着市场将调整到一个较慢的、更持久的上升趋势线（线2）上。

![](images/fabf35fb4ad85eea89d1b7f22be5a5316fe5f192a4e6d33cce0dc0718462810a.jpg)

![](images/2a4a1e36f1859735570d40219369f9ee9b673c8dc6f4c7d12055116dfa625721.jpg)

图4.14(a) 上升趋势线(线1)过于平缓的例子。当上升趋势加速后, 线1 显然过于平缓, 在这种情况下, 我们应当作出另一条更陡峭的趋势线来(线2), 以更紧凑地跟踪该上升趋势。

图4.14(b) 本例说明, 当上升趋势加速后, 我们有必要作出更陡峭的上升趋势线。但是, 即使在这样的场合, 如果我们把过去的趋势线相应地延长, 也仍然不失为明智之举。将来, 或许它们迟早会派上用场。

![](images/43599541b5f6d42a597c753f899b5a5579a203893a127a7f5c6b44cdc86d40a8.jpg)

```
6.6. **Missing Caption Numbers**: e.g., "as shown in the figure", without specific numbering  

  - Solution: Unable to establish correspondence between images and captions; no solution available for now, mark as *extreme abnormal*  

  - Example:
```

考虑到经济周期具有周期性,所以从某种程度上说周期是可以预测的。美国国会委员会编制的一系列周期性指标可以用来预期、度量和解释经济活动的短期波动。先行经济指标(leading economic indicators)往往先于其他经济指标变动。同步和滞后指标,正如它们的名字一样,与总体经济同时变化或稍微滞后于总体经济变化。

一个广泛采用的先行经济指标合成指数由十种指标组合构成。同样,四种同步指标和七种滞后指标组成了各自的合成指数。表17- 2显示了这些合成指数的各个组成部分。

![](images/e0ef2733ee653fc67735c2900daf112c9b0910b91df603c993099fc71e93f8a1.jpg)  
资料来源：The Conference Board, Business Cycle Indicators, November 2012.

图17- 4中的曲线描绘了三种指标组合。图中上方的日期显示了经济扩张和收缩的转折点。虽然先行经济指标一般先于其他指标变化,该指标的领先时间长度是不确定的。而且当经济处于高峰时,指标的领先时间比经济处于谷底时领先时间更长。

![](images/d3f2b34fbd2f282458371991ab4fdc1cfd9b388990a6d1e01178c56ade68ba38.jpg)  
图17-4先行、同步和滞后经济指标

注:阴影部分代表经济衰退。

资料来源:The Conference Board,Business Cycle Indicators,December 2008,已获得使用许可。

```

```

实践告诉我们，虽然市场存在信息不对称，但是信息传导的速度过快，经常导致套利空间被压缩，也就是价格在快速向某个方向运行后，又多会反向运行，难以继续支撑原有方向，在动量能够被观测到的时候，已经变成了反转。

![](images/9dd89a829f091f193e79baae68279b773862551f29c8274f2aac3f6b8aa66e34.jpg)  
图片来源：36氪

图4- 13 以微博为例, 信息源传播路径和信息获取者渠道不同, 导致信息传播不对称

大部分A股投资者不关心公司的基本面, 其核心原因是A股定价和基本面关系较弱, 而和资金推动力关系较强, 且行业未形成垄断格局。这样我们不用始终将资金集中在已经上涨的高动量股票上, 而是在同行业、同概念板块中寻找滞涨股, 反而能够获得类似收益, 此时先涨的股票被资金抛弃, 资金涌入类似的"短期估值洼地", 造成了实际观测到的动量缺失, 而低动量股票在第二次观测时启动。

当然我们的资金敢于这样操作的核心原因是价值投资风气尚未形成, 概念容易制造、容易快速切换炒作, 但是价值投资需要对少数行业龙头股票长期追踪甚至持有, 此时市场才能切换到动量效应的控制下。

```
6.7. **Caption-Image Separation**: captions are located far from the corresponding images  

  - Solution: Unable to find captions using the search strategy; unable to establish correspondence between images and captions, mark as *extreme abnormal*  

  - Example:
```

![](images/000001/000001.jpg)

xxxxxxxxxxxxxxxxxxxxxxxxxxxx
xxxxxxxxxxxxxxxxxxxxxxxxxxxx

图1 xxxxxxxxxxxxxxxxxxxxxx

xxxxxxxxxxxxxxxxxxxxxxxxxxx

```
6.8. **Multiple Images Sharing a Caption**: multiple images share the same caption  

  - Solution: Using the search strategy, save all captions near the image tag; multiple images will share the caption, and due to the presence of multiple image tags, the entry will be marked as *abnormal*  

  - Example:
```

![](images/000001/000001.jpg)

![](images/000001/000002.jpg)

![](images/000001/000003.jpg)

![](images/000001/000004.jpg)

图1 xxxxxxx

以上四张图是1组，图1表示这1组图

```
6.9. **Subfigure Caption System**: such as "Figure 1(a)", "Figure 1(b)", etc.  

  - Solution: Using the search strategy, assign the caption near the image tag as the potential caption for the subfigure  

  - Example:
```

之所以减去3是因为正态分布的上述比率为3,所以正态分布的峰度为零,峰度为正则说明存在肥尾现象。图5- 5b中的肥尾曲线峰度为0.35。

![](images/5797aa176442e1c39bbae109f8b7db84ec61417e4691ae80d092083237b84a97.jpg)  
图5-5a 正态和偏度分布（均值  $6\%$  ，  $\mathsf{S D} = 17\%$  1

![](images/9ac363780763b0b3067a1c2f34e74fa5716c3983372c7a46490c77d5655a1afe.jpg)  
图5-5b 正态和肥尾分布（均值0.1，  $\mathsf{S D} = 0.2$

$\ominus$  对于一个关于均值对称的分布,比如正态分布而言,所有的奇数矩量  $(n = 1,3,5,\dots)$  的期望都为零,而所有的偶数矩量都仅仅是标准差的一个函数。比如,四阶矩为  $3\sigma^{4}$  ,六阶矩为  $15\sigma^{6}$  。因此,对于服从正态分布的收益率而言,标准差  $\sigma$  提供了风险的全部信息,而资产组合的投资绩效可以通过夏普比率  $\frac{R}{\sigma}$  来计算。然而对于其他非对称分布而言,奇数阶矩可能非零。一个比正态分布更大的偶数阶矩,加上一个负的奇数阶矩,意味着发生极端恶劣状况概率的增加。

极端负值可能由负偏度以及负峰度产生。因此,我们需要一个风险度量来衡量极端负收益率的发生情况。注意偏度和峰度都为纯数值。它们不会随着高频观测值的年化而变化。极端负收益的频繁发生会导致出现负偏和肥尾。因此,我们需要揭示极端负收益发生的风险测度。我们将讨论业界最普遍使用的该种测度:在险价值、预期损失、下偏标准差和极端收益频率(3- sigma)。

```

```

之所以减去3是因为正态分布的上述比率为3,所以正态分布的峰度为零,峰度为正则说明存在肥尾现象。图5- 5b中的肥尾曲线峰度为0.35。

![](images/5797aa176442e1c39bbae109f8b7db84ec61417e4691ae80d092083237b84a97.jpg)  
图5-5a 正态和偏度分布（均值  $6\%$  ，  $\mathsf{S D} = 17\%$  1

![](images/9ac363780763b0b3067a1c2f34e74fa5716c3983372c7a46490c77d5655a1afe.jpg)  
图5-5b 正态和肥尾分布（均值0.1，  $\mathsf{S D} = 0.2$

$\ominus$  对于一个关于均值对称的分布,比如正态分布而言,所有的奇数矩量  $(n = 1,3,5,\dots)$  的期望都为零,而所有的偶数矩量都仅仅是标准差的一个函数。比如,四阶矩为  $3\sigma^{4}$  ,六阶矩为  $15\sigma^{6}$  。因此,对于服从正态分布的收益率而言,标准差  $\sigma$  提供了风险的全部信息,而资产组合的投资绩效可以通过夏普比率  $\frac{R}{\sigma}$  来计算。然而对于其他非对称分布而言,奇数阶矩可能非零。一个比正态分布更大的偶数阶矩,加上一个负的奇数阶矩,意味着发生极端恶劣状况概率的增加。

极端负值可能由负偏度以及负峰度产生。因此,我们需要一个风险度量来衡量极端负收益率的发生情况。注意偏度和峰度都为纯数值。它们不会随着高频观测值的年化而变化。极端负收益的频繁发生会导致出现负偏和肥尾。因此,我们需要揭示极端负收益发生的风险测度。我们将讨论业界最普遍使用的该种测度:在险价值、预期损失、下偏标准差和极端收益频率(3- sigma)。

```

```

图4- 9(a)表示规模报酬不变。在  $A$  点,厂商使用10单位劳动和5单位资本,生产100单位产量。在  $B$  点,厂商使用20单位劳动和10单位资本,生产200单位产量,即劳动和资本投入量是原来的两倍,产量也是原来的两倍。在  $C$  点,劳动和资本投入量是原来的三倍,产量也是原来的三倍。在规模报酬不变的情况下,图中有线段  $O A = A B = B C$  。

图4- 9(b)表示规模报酬递增。从  $D$  点到  $E$  点,产量从100单位增加到200单位,以相同比例增加的劳动和资本投入量却不到原来的两倍;在  $F$  点,产量增加到300单位,劳动和资本投入量更是小于原来的三倍。在规模报酬递增的情况下,图中有线段  $O D > D E > E F$  。

图4- 9(c)表示规模报酬递减。图中等产量曲线之间的距离越来越大,即有  $O G< G H< H I$  。

![](images/9e1211d84fd9bc1234b99c8b5b082a6d3037642bfcae36622eaadd40b124e844.jpg)  
(a)

![](images/9dbfc73b08b9cdb92db76d0789c2822c97e2faac7973d3036fca814ea8fea88f.jpg)  
(b)

![](images/f3ad0375b953a692fa5bc3846dde70ad11ef8e76a1ed604bc7c228f66481c244.jpg)  
图4-9 规模报酬

我们也可用以下数学公式来定义规模报酬的三种情况。

令生产函数为  $Q = f(L,K)$ ,且常数  $\lambda >1$ ,于是有:

```
6.10. **Figure Catalog Interference**: if a book contains a figure catalog, it may interfere when locating caption references; figure catalog names vary across different books  

  - Solution: Delete figure catalogs via regex during markdown file reading  

  - Example:
```

Possible contents of the Figure Catalog

# LIST OF FIGURES

Figure 1: The Capacity Pyramid7   
Figure 2: Consolidated Municipal Capacity Assessment Framework 10   
Figure 3: ITI SUD project phases and average duration (2014-2020 programming period) based on sample of projects22   
Figure 4: Strategic planning landscape at the local level and links to relevant plans at the national and regional levels24   
Figure 5: Two pillars and four thematic areas25   
Figure 6: Proposed activities under each thematic area, including cities to benefit from support 26   
Figure 7: Examples of maps highlighting the hazards exposure of the four cities29   
Figure 8: Shifting toward systemic capacity building - an evolving model33   
Figure 9: A framework for systemic local government capacity building38

```

```

Possible titles of the Figure Catalog

Chinese  
图目录  
图表目录  
插图目录  
图形目录  
图片目录  
图索引  
图表索引  
插图索引  
图形索引

English – Figure / Table / Catalog  
Figure Directory  
Table of Figures  
Figures List  
List of Figures  
List Figures  
Index of Figures  
Figure Index  
Contents of Figures  
Figures Contents  
Figure Catalog  
Catalog of Figures  

English – Illustrations  
List of Illustrations  
Illustrations List  
Index of Illustrations  
Illustrations Index  
Table of Illustrations  
Illustrations Directory  
Illustrations Catalog  
Catalog of Illustrations  

English – Mixed tables & figures  
List of Tables and Figures  
Tables and Figures List  
Index of Tables and Figures  
Table of Contents Figures  
List of Figures and Tables  
Figures and Tables List  

English – Charts / Graphs  
List of Charts  
Charts List  
Index of Charts  
Chart Index  
Table of Charts  
List of Graphs  
Graphs List  
Index of Graphs  
Graph Index  
Table of Graphs  

English – General / Contents  
List of Contents  
Contents List  
Index of Contents  

English – Academic sections (with optional leading number)  
LESSONS AND RECOMMENDATIONS  
CONCLUSIONS  
SUMMARY  
RESULTS AND DISCUSSION   
FINDINGS    
ANALYSIS   
RESULTS  

```
6.11. **The correspondence between caption and reference**: It is possible to find one or more captions, and each caption corresponds to one or more references, requiring correspondence establishment  

  - Solution: References are written in [[]] format (i.e., nested lists), where each list corresponds to the references found for a caption, and the inner list represents multiple references for that caption  

  - Example:

```Json
  {
  "caption_references": [
      {
        "caption": "Figure 4: Common support of the matching",
        "figure_number": "Figure 4",
        "reference_count": 1,
        "references": [
          {
            "reference_text": [
              "Figure 4"
            ],
            "is_exact_match": true,
            "match_line_info": {
              "line_number": 244,
              "content": "The method implemented for this impact evaluation is a propensity score matching (PSM). We match treated and control based on demographic characteristics (age,gender, being in couple,level of education, and nationality),household characteristics (size,TV as communication medium) and field area. After the matching, we compute the average treatment on treated (ATT) as the indicator of the project impact on the treated. To ensure the quality of the matching, Figure 4 (on appendix) plots the common support and Table 8 displays the balancing test.",
              "char_position_in_paragraph": 460
            },
            "reference_paragraph": "The method implemented for this impact evaluation is a propensity score matching (PSM). We match treated and control based on demographic characteristics (age,gender, being in couple,level of education, and nationality),household characteristics (size,TV as communication medium) and field area. After the matching, we compute the average treatment on treated (ATT) as the indicator of the project impact on the treated. To ensure the quality of the matching, Figure 4 (on appendix) plots the common support and Table 8 displays the balancing test.",
            "reference_paragraph_extension": "\n\nThe mostly requested services are pesticides $( 6 8 \\% )$ ，fertilizers $( 5 4 \\% )$ ， grafting $( 3 3 \\% )$ and replanting $( 2 9 \\% )$ . This is consistent with data from CVCs’ operators.Before the project, the main issues faced by farmers were availability $( 3 7 , 3 \\% )$ ，cost $( 3 3 \\% )$ and to a lesser extent the payment method $( 1 9 , 1 \\% )$ of the input and services. Producers do not recognize the quality as a big issue since only $3 \\%$ raised it. Therefore,the project seems to provide solution to the availability,cost and the method of payment. Concerning the costs,the cost of the $5 0 ~ \\mathrm { k g }$ of fertilizer lies between 13,50O and 18,O00 CFA Francs compared to 25,000 CFA Francs (2012 baseline data). Almost one quarter of the CVCs’ operators sell the fertilizer at15,0Oo.New fertilizer is less expensive than the fertilizer on the market at the beginning of the project. The MoU with IDH has played a role via economies of scale. Regarding the payment, the producers pay cash $( 7 6 \\% )$ as before or by credit $( 4 3 \\% )$ . For some of them, the services are free of charge. Payment by credit is an innovation of the project.\n\n# Impact of the program on producers\n\nThe method implemented for this impact evaluation is a propensity score matching (PSM). We match treated and control based on demographic characteristics (age,gender, being in couple,level of education, and nationality),household characteristics (size,TV as communication medium) and field area. After the matching, we compute the average treatment on treated (ATT) as the indicator of the project impact on the treated. To ensure the quality of the matching, Figure 4 (on appendix) plots the common support and Table 8 displays the balancing test.\n\nThe effect of the program is assessed on productivity and income by using a matching approach. Table 6 summarizes the results of the estimation by using a one-to-one matching approach as well as the radius, the kernel, and the nearest neighbor approaches for robustness.\n\nPertaining to productivity， we highlight a significant efect of the program on yield (productivity). Without considering the control variables,it seems that there is no difference in the productivity between the treated and the control groups. After matching,we find significant difference between treated and control groups at 5 percent level. The average yield is 81.98 kilograms per hectare higher for the treated group.\n\n",
            "total_lines_in_paragraph": 1
          }
        ]
      }
    ]
  }
```

6.12. **Incorrect Figure Captions**: When searching for references to figure captions (e.g., "Figure 1"), the search might erroneously match paragraphs referencing Figure 10, Figure 11, Figure 12, etc.  

- **Solution**: After locating a reference, use regex to re-extract the list of figure numbers from the `reference text` and match it against the figure caption’s number `caption number`. Set the field `is_exact_match` to `true` only if the `caption number` exists within the `reference text`; otherwise, set it to `false`.  

- **Example**:

```Json
  {
    "classification": "abnormal",
    "book_id": "002026",
    "image_filename": "000004.jpg",
    "image_tag_line_number": 228,
    "other_images_nearby": {
      "count": 0,
      "images": []
    },
    "caption_count": 2,
    "captions_found": [
      {
        "content": "Figure 2.1 CA-DR total trade growth (goods and services),2000-2021 (a) CA-DR countries (b) CA-DR and peers",
        "content_paragraph": "\n\nCentral American countries and the Dominican Republic have been relatively successfulin trading with the rest of the world over the past two decades. Trade in the CA-DR region has grown steadily, with all countries more than doubling their export and import values of goods and services in the last 20 years. Nicaragua's trade grew the most, with an increase of over four times between 20o0 and 2021,albeit from a low starting point (Figure 2.1, Panel a). Guatemala's trade values have also increased over 3.5 times in the same period.The increase in the region's trade is comparable to its peers,similar to rates of Chile and South Korea,and higher than Mexico (Figure 2.1, Panel b).\n\n![](../images/002026/000004.jpg)  \nFigure 2.1 CA-DR total trade growth (goods and services),2000-2021 (a) CA-DR countries (b) CA-DR and peers\n\nWhile trade values increased steadily for CA-DR countries,trade openness (as measured by the tradeto GDP ratio) has stagnated or,in some cases, even regressed.Trade openness is a key metric that reflects a country's degree of integration with the world economy.The trade-to-GDP ratio is one of the most widely used indicators of integration with world trade.It reflects the importance offoreign demand for domestic producers (exports),on the one hand,and foreign supply for domestic consumers and producers (imports) on the other. Central American countries have higher levels of trade openness compared to rest of Latin America and the Caribbean,while being on par with their peers. However, many countries have observed a decline in the past two decades (Figure 2.2),reflecting a domestically driven growth pattern.\n\n",
        "line_number": 229,
        "distance": 1
      },
      {
        "content": "Figure2.2:Tradein goodsbycountry $1 \\%$ ofGDP)",
        "content_paragraph": "\n\nWhile trade values increased steadily for CA-DR countries,trade openness (as measured by the tradeto GDP ratio) has stagnated or,in some cases, even regressed.Trade openness is a key metric that reflects a country's degree of integration with the world economy.The trade-to-GDP ratio is one of the most widely used indicators of integration with world trade.It reflects the importance offoreign demand for domestic producers (exports),on the one hand,and foreign supply for domestic consumers and producers (imports) on the other. Central American countries have higher levels of trade openness compared to rest of Latin America and the Caribbean,while being on par with their peers. However, many countries have observed a decline in the past two decades (Figure 2.2),reflecting a domestically driven growth pattern.\n\nSource:Staffcalcuations basedon World Development Indicatorsfor totaltradeandIMFforcommercialservices exports.Note Commercial services cover allservices categories,except tradein governments goods and services.   \nFigure2.2:Tradein goodsbycountry $1 \\%$ ofGDP)   \n![](../images/002026/000005.jpg)  \nSource:WDl data.\n\nTrade openness in goods,though stil relatively high,declined in most CA-DR countries.Trade in goods for CA-DR countries has accounted for an average of 68 percent of GDP overthe last two decades,slightly higher than their peers. However,unlike its peers,the trade openness declined in most CA-DR countries. El Salvador and Nicaragua have improved their trade openness in terms of goods and are now exporting more than expected based on their level of economic development (Figure 2.3).In contrast, Costa Rica, the Dominican Republic, Guatemala,and Panama have faced a declining merchandise trade opennes and are now exporting lessthan what their level of economic development suggests. Costa Rica and Panama, in particular,used to have higher-than-expected levels of merchandise trade.However,this situation has reversed since the early 2000s.\n\n",
        "line_number": 234,
        "distance": 6
      }
    ],
    "nearest_caption": "Figure 2.1 CA-DR total trade growth (goods and services),2000-2021 (a) CA-DR countries (b) CA-DR and peers",
    "caption_references": [
      {
        "caption": "Figure 2.1 CA-DR total trade growth (goods and services),2000-2021 (a) CA-DR countries (b) CA-DR and peers",
        "figure_number": "Figure 2.1",
        "reference_count": 18,
        "references": [
          {
            "reference_text": [
              "Figure 2.1",
              "Figure 2.1"
            ],
            "is_exact_match": true,
            "match_line_info": {
              "line_number": 226,
              "content": "Central American countries and the Dominican Republic have been relatively successfulin trading with the rest of the world over the past two decades. Trade in the CA-DR region has grown steadily, with all countries more than doubling their export and import values of goods and services in the last 20 years. Nicaragua's trade grew the most, with an increase of over four times between 20o0 and 2021,albeit from a low starting point (Figure 2.1, Panel a). Guatemala's trade values have also increased over 3.5 times in the same period.The increase in the region's trade is comparable to its peers,similar to rates of Chile and South Korea,and higher than Mexico (Figure 2.1, Panel b).",
              "char_position_in_paragraph": 434
            },
            "reference_paragraph": "Central American countries and the Dominican Republic have been relatively successfulin trading with the rest of the world over the past two decades. Trade in the CA-DR region has grown steadily, with all countries more than doubling their export and import values of goods and services in the last 20 years. Nicaragua's trade grew the most, with an increase of over four times between 20o0 and 2021,albeit from a low starting point (Figure 2.1, Panel a). Guatemala's trade values have also increased over 3.5 times in the same period.The increase in the region's trade is comparable to its peers,similar to rates of Chile and South Korea,and higher than Mexico (Figure 2.1, Panel b).",
            "reference_paragraph_extension": "\n\nThis section examines the evolution of the trade structure in CA-DR countries overthe last two decades. It focuses on the evolution of trade,composition of trade,main partners,and trade diversification over the past two decades. Given the heterogeneity across the seven CA-DR countries covered in this study, each serves as a comparator to each other,but performance willalso be benchmarked relative to peer countries: Chile,Mexico,Peru,and South Korea.9 The periods selected for the studyare 2001-2006,2007- 2013,2014-2019,and 2020-2022 (where available).\n\n# Evolution of trade\n\nCentral American countries and the Dominican Republic have been relatively successfulin trading with the rest of the world over the past two decades. Trade in the CA-DR region has grown steadily, with all countries more than doubling their export and import values of goods and services in the last 20 years. Nicaragua's trade grew the most, with an increase of over four times between 20o0 and 2021,albeit from a low starting point (Figure 2.1, Panel a). Guatemala's trade values have also increased over 3.5 times in the same period.The increase in the region's trade is comparable to its peers,similar to rates of Chile and South Korea,and higher than Mexico (Figure 2.1, Panel b).\n\n![](../images/002026/000004.jpg)  \nFigure 2.1 CA-DR total trade growth (goods and services),2000-2021 (a) CA-DR countries (b) CA-DR and peers\n\nWhile trade values increased steadily for CA-DR countries,trade openness (as measured by the tradeto GDP ratio) has stagnated or,in some cases, even regressed.Trade openness is a key metric that reflects a country's degree of integration with the world economy.The trade-to-GDP ratio is one of the most widely used indicators of integration with world trade.It reflects the importance offoreign demand for domestic producers (exports),on the one hand,and foreign supply for domestic consumers and producers (imports) on the other. Central American countries have higher levels of trade openness compared to rest of Latin America and the Caribbean,while being on par with their peers. However, many countries have observed a decline in the past two decades (Figure 2.2),reflecting a domestically driven growth pattern.\n\n",
            "total_lines_in_paragraph": 1
          },
          {
            "reference_text": [
              "Figure 2.10"
            ],
            "is_exact_match": false,
            "match_line_info": {
              "line_number": 295,
              "content": "At the aggregate, nearly 60 percent of total export values of CA-DR countries are in goods,and the rest in services.The share of services in total pre-pandemic trade was over 40 percent, much higher than in peer countries (Figure 2.10).The share of services exports varies among countries一representing almost half of the total exports in Panama, Costa Rica,and the Dominican Republic，but accounting for approximately one-quarter in Guatemala and Nicaragua.In 2O20-2021,the share of services declined to 33.9 percent as travel and tourism in the region were substantially affected during the COVID-19 pandemic,although to a much lesser extent than other peers such as Chile,Mexico,Peru,or South Korea.",
              "char_position_in_paragraph": 223
            },
            "reference_paragraph": "At the aggregate, nearly 60 percent of total export values of CA-DR countries are in goods,and the rest in services.The share of services in total pre-pandemic trade was over 40 percent, much higher than in peer countries (Figure 2.10).The share of services exports varies among countries一representing almost half of the total exports in Panama, Costa Rica,and the Dominican Republic，but accounting for approximately one-quarter in Guatemala and Nicaragua.In 2O20-2021,the share of services declined to 33.9 percent as travel and tourism in the region were substantially affected during the COVID-19 pandemic,although to a much lesser extent than other peers such as Chile,Mexico,Peru,or South Korea.",
            "reference_paragraph_extension": "\n\nServices exports to the principal partners have exhibited a consistent growth trend. Exports to the United States, Europe,the Latin American and Caribbean,and China have steadily increased (Figure 2.9, Panela).Although exports ofservices exports experienced a significant setback in 2020 due to the COVID19 pandemic,signs of recovery have already emerged.This is despite current levels remaining below prepandemic benchmarks，which is mainly due to lagging service exports to China. Leading up to the pandemic,services exports to China had grown most significantlyin most CA-DR countries (the exceptions being Honduras and Nicaragua),albeit from a low level (Figure 2.9, Panel b).\n\nFigure2.9:Servicesexportsgrowthbydestination   \n![](../images/002026/000014.jpg)  \nSource:Authors'calculations based on BATIS.\n\n# Tradecomposition\n\nAt the aggregate, nearly 60 percent of total export values of CA-DR countries are in goods,and the rest in services.The share of services in total pre-pandemic trade was over 40 percent, much higher than in peer countries (Figure 2.10).The share of services exports varies among countries一representing almost half of the total exports in Panama, Costa Rica,and the Dominican Republic，but accounting for approximately one-quarter in Guatemala and Nicaragua.In 2O20-2021,the share of services declined to 33.9 percent as travel and tourism in the region were substantially affected during the COVID-19 pandemic,although to a much lesser extent than other peers such as Chile,Mexico,Peru,or South Korea.\n\nFigure 2.10: Share of goods and services exports to total exports,2014-2019 average. (a) Compare with peers (b) By country\n\n![](../images/002026/000015.jpg)  \nSource:WITS.\n\n$100 \\%$ $80 \\%$ 1111   \n$60 \\%$   \n$40 \\%$   \n$20 \\%$   \n0%   \nCosta Rica Domincan... Guatemala Honduras Nicaragua Panama El Salvador Goods ■Services\n\n# Merchandise trade composition\n\nMerchandise exports are concentrated in a few sectors, while imports are widespread.In most CA-DR countries, the top exported sectors tend to be agriculture (especially for Guatemala, Honduras，and Nicaragua)，textiles (El Salvador，Guatemala，Nicaragua)，machinery and electrics (Costa Rica)，or chemicals (Panama). Imports are typically more spread out across sectors (Figure A.10). However, there are large degrees of heterogeneity across CA-DR countries in their key merchandise exports.\n\n",
            "total_lines_in_paragraph": 1
          },
        ]
      }
    ]
  }
```

6.13. **Long Figure Number**: The figure number and caption content may lack a space, causing them to merge into an excessively `long figure number`.  

- **Solution**: After identifying the corresponding reference for each figure caption, examine the reference list. If an empty reference exists and the caption contains three consecutive digits, treat it as a `long figure number` scenario. The approach is as follows:  
  
  - Iteratively remove one character from the **right** to form the `current figure_number`, then use this `current figure_number` to search for references. If a match is found, record it; if not, continue removing characters until only one remains.  
  - If **exactly one reference** is found, it is deemed the correct match for the caption. If **multiple references** are found, calculate the numerical difference between each `reference_text` and the figure’s sequence number (e.g., `000001.jpg`). Select the reference with the **smallest difference** as the match for the caption.  

- **Example**:
  
```
  图22015-2016经济增长率
  ```

6.14. **A reference contains multiple figure numbers within a single figure caption.**

- Solution: After locating the reference, use regular expressions to re-extract the list of figure numbers from the `reference text`. Store all identified `figure number` instances. Then match them against the figure caption's `reference text`. If the `figure number` exists within the `reference text`, set the field `is_exact_match` to true; otherwise, set it to false (we consider it reasonable for a single sentence to reference multiple figures).

- Example:
  
```
  reference_paragraph: "如图8，图9，图10所示，总体呈现出"
  ```

6.15. **Duplication between reference and caption**: During reference extraction, the original caption content was extracted, resulting in duplication between reference and caption.

- Solution: Implement line number verification. After locating the caption and extracting the figure_number from it, remove that line from the original `markdown_content`. Additionally, ensure the line number of the reference and the line number of the caption must not be the same.

- Example:
  
```
  "captions_found": [
  {
    "content": "Figure 1: Share of firms reporting temporary closures by sector",
    "content_paragraph": "Firms in the service sector were worst affected by COVID-19, with 11 percent of service firms reporting temporary closures (Figure 1).Across firm sizes,smaller firms were more materially impacted than larger-size firms as indicated by 8 percent of micro firms being temporarily closed compared to 1 percent of large firms being forced to do the same.\n\nFigure 1: Share of firms reporting temporary closures by sector   \n![](../images/003339/000001.jpg)  \nSource: The World Bank's COVID-19 firmsurvey\n\n![](../images/003339/000002.jpg)  \nFigure 2: Share of firms reporting temporary closures by firm size\n\nWhile representatives of closed firms expected to resume operations in an average of 8 weeks, resumption estimates among firms in the service sector were as high as 14 weeks.The range of responses reflects how differently COVID-19 has affected individual firms across diferent sectors (Figure 3).As service firms accounted for a higher share of temporary closures,those firms were closed for the highest number of weeks with an average of 14 weeks. However, while only 3 percent of manufacturing firms were temporarily closed, their length of closure was significant, averaging 13 weeks (Figure 1 and Figure 3). Agriculture firms were the most ikely to continue operating, with only 5 percent ofirms reporting temporary closures,and those firms were closed for only 2 weeks.\n\n",
    "line_number": 15,
    "distance": 1
  },
  ]
  "caption_references": [
  {
  "caption": "Figure 1: Share of firms reporting temporary closures by sector",
  "figure_number": "Figure 1",
  "reference_count": 20,
  "references": [
    {
      "reference_text": [
        "Figure 1"
      ],
      "is_exact_match": true,
      "match_line_info": {
        "line_number": 13,
        "content": "Figure 1: Share of firms reporting temporary closures by sector",
        "char_position_in_paragraph": 311
      },
      "reference_paragraph": "Firms in the service sector were worst affected by COVID-19, with 11 percent of service firms reporting temporary closures (Figure 1).Across firm sizes,smaller firms were more materially impacted than larger-size firms as indicated by 8 percent of micro firms being temporarily closed compared to 1 percent of large firms being forced to do the same.\n\nFigure 1: Share of firms reporting temporary closures by sector   \n![](../images/003339/000001.jpg)",
      "reference_paragraph_extension": "\n\nWhile only 6 percent of firms reported temporarily closing operations for an average of six weeks across all sectors,operational impacts were varied across sectors and firm sizes in May. Firms in the service sector were worst affected by COVID-19, with 11 percent of service firms reporting temporary closures (Figure 1).Across firm sizes,smaller firms were more materially impacted than larger-size firms as indicated by 8 percent of micro firms being temporarily closed compared to 1 percent of large firms being forced to do the same.\n\nFigure 1: Share of firms reporting temporary closures by sector   \n![](../images/003339/000001.jpg)  \nSource: The World Bank's COVID-19 firmsurvey\n\n![](../images/003339/000002.jpg)  \nFigure 2: Share of firms reporting temporary closures by firm size\n\nWhile representatives of closed firms expected to resume operations in an average of 8 weeks, resumption estimates among firms in the service sector were as high as 14 weeks.The range of responses reflects how differently COVID-19 has affected individual firms across diferent sectors (Figure 3).As service firms accounted for a higher share of temporary closures,those firms were closed for the highest number of weeks with an average of 14 weeks. However, while only 3 percent of manufacturing firms were temporarily closed, their length of closure was significant, averaging 13 weeks (Figure 1 and Figure 3). Agriculture firms were the most ikely to continue operating, with only 5 percent ofirms reporting temporary closures,and those firms were closed for only 2 weeks.\n\n",
      "total_lines_in_paragraph": 1
    },
  ]
  }
  ]
```

6.16. **Digit and hyphen mis-parsing in figure labels**

- Solution: In the initial markdown pass, run two regex fixes sequentially:  
  (1) `re.sub(r'(?<=[Ff]igure|[Ff]ig|图)(\d)[oO]', r'\g<1>0', text)` – turns “Figure 1o” → “Figure 10”;  
  (2) `re.sub(r'(?<=\d)一(?=\d)', '-', text)` – turns “图2一1” → “图2-1”.

- Example:

```
如图1o所示
从图2一1中可以看出
```
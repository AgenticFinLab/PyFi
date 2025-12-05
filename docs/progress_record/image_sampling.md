### Data Sampling

#### Basic Criteria 
The image sampling strategy is structured around four key dimensions: **complexity level**, **compliance level**, **content theme**, and **chart type**. 

During the image screening phase, a visual language model (VLM) is employed to assess whether an input image meets a predefined set of criteria. The model uses a structured prompt to evaluate image suitability and assigns two numerical scores: a compliance level and a complexity level. 

The **compliance level** (ranging from 0 for non-compliant to 10 for fully compliant) reflects the degree to which the image satisfies the following requirements:

- The image must be a **financial trend chart** without extraneous elements such as landscapes, people, logos, or decorative graphics.
- It must contain **clearly legible text** in either Chinese or English, readable without magnification.
- It must be **free of obvious errors** such as incorrect scaling, missing labels, or inconsistent units.
- The visual must represent a **financial dynamic** (e.g., trends, conversions, circulations, or systemic transformations).
- Tabular or grid elements must not dominate the layout; emphasis should be on **dynamic representations**.
- Elements must be visually linked (e.g., with arrows or color coding) to express **financial relationships**.
- Content must relate to **financial topics** such as asset pricing, risk modeling, structural changes, or macroeconomic impacts.
- The image must remain **interpretabl**e under various viewing conditions (e.g., grayscale, standard resolution).

The **complexity level** (from 0 for very simple to 10 for very complex) is assigned based on visual intricacy, data density, and structural sophistication.

Each image is tagged with at least one of **17 content themes** and at least one of **11 chart types**. Below is a summary of the distribution by content theme and chart type.

---

#### Content Theme Distribution:
- Macroeconomic Indicators (1)
- Financial Markets & Products (2)
- Commodities & Real Estate Markets (3)
- Bonds & Fixed Income (4)
- Monetary & Fiscal Policy (5)
- International Trade & Capital Flows (6)
- Corporate Finance & Valuation (7)
- Industry Analysis (8)
- Investment Theory & Portfolio Management (9)
- Risk Models & Management (10)
- Economic Cycles & Market Theories (11)
- Microeconomic Principles (12)
- Demographics & Socioeconomics (13)
- Financial Systems & Infrastructure (14)
- Organization & Regulation (15)
- Geospatial Economic Data (16)
- Financial History & Documentation (17)
  
---

#### Chart Type Distribution:
- Line Chart (1)
- Bar Chart / Column Chart (2)
- Pie Chart / Donut Chart (3)
- Scatter Plot / Bubble Chart (4)
- Table (5)
- Diagram / Schematic (6)
- Radar Chart (7)
- Heatmap (8)
- Candlestick Chart / OHLC Chart (9)
- Photograph (10)

- Infographic (11)

---


#### Image Sampling Process

From an initial pool of **820,816** images, we applied a two-stage filtering process to construct a high-quality financial image dataset. First, we retained only images with **compliance levels 9 and 10**, indicating full or near-full adherence to the specified financial data visualization criteria. Non-financial images were excluded.

From the compliant subset, we selected the **top 20,000 images with the highest complexity** level, reflecting visual intricacy and informational density. We further refined the set by including only chart types relevant to financial data analysis: **line charts (1)**, **bar/column charts (2)**, **diagrams/schematics (6)**, **candlestick/OHLC charts (9)**, and **infographics (11)**. **Content themes were balanced** across categories such as macroeconomic indicators, financial markets, risk management, and economic cycles to ensure thematic diversity.

After automated filtering, a **manual** review was conducted to exclude any remaining unsuitable images—such as those with poor readability, non-compliant elements, or ambiguous content. The final curated dataset consists of **3,092** images. The resulting dataset supports rigorous computational analysis of financial visualizations with high compliance and varying complexity.

---

#### Initial Images Statistics Summary

A total of **820,816** images were collected and annotated from a substantial collection of financial documents. The statistical information is as follows:


##### Content Theme Distribution

| Theme ID | Theme Name                               | Count     | Percentage |
| -------- | ---------------------------------------- | --------- | ---------- |
| 1        | Macroeconomic Indicators                 | 28,006    | 2.66%      |
| 2        | Financial Markets & Products             | 666,097   | 63.20%     |
| 3        | Commodities & Real Estate Markets        | 10,444    | 0.99%      |
| 4        | Bonds & Fixed Income                     | 7,708     | 0.73%      |
| 5        | Monetary & Fiscal Policy                 | 9,270     | 0.88%      |
| 6        | International Trade & Capital Flows      | 9,263     | 0.88%      |
| 7        | Corporate Finance & Valuation            | 14,685    | 1.39%      |
| 8        | Industry Analysis                        | 31,451    | 2.98%      |
| 9        | Investment Theory & Portfolio Management | 141,444   | 13.42%     |
| 10       | Risk Models & Management                 | 11,891    | 1.13%      |
| 11       | Economic Cycles & Market Theories        | 32,200    | 3.06%      |
| 12       | Microeconomic Principles                 | 4,516     | 0.43%      |
| 13       | Demographics & Socioeconomics            | 37,674    | 3.57%      |
| 14       | Financial Systems & Infrastructure       | 12,369    | 1.17%      |
| 15       | Organization & Regulation                | 14,210    | 1.35%      |
| 16       | Geospatial Economic Data                 | 17,083    | 1.62%      |
| 17       | Financial History & Documentation        | 5,560     | 0.53%      |
| Total    | -                                        | 1,053,871 | 100.00%    |

##### Chart Type Distribution

| Type ID | Chart Type                     | Count     | Percentage |
| ------- | ------------------------------ | --------- | ---------- |
| 1       | Line Chart                     | 152,927   | 11.82%     |
| 2       | Bar Chart / Column Chart       | 71,384    | 5.52%      |
| 3       | Pie Chart / Donut Chart        | 5,590     | 0.43%      |
| 4       | Scatter Plot / Bubble Chart    | 5,789     | 0.45%      |
| 5       | Table                          | 32,294    | 2.50%      |
| 6       | Diagram / Schematic            | 226,233   | 17.48%     |
| 7       | Radar Chart                    | 873       | 0.07%      |
| 8       | Heatmap                        | 650       | 0.05%      |
| 9       | Candlestick Chart / OHLC Chart | 600,912   | 46.43%     |
| 10      | Photograph                     | 51,644    | 3.99%      |
| 11      | Infographic                    | 145,871   | 11.27%     |
| Total   | -                              | 1,294,167 | 100.00%    |

##### Compliance Level Distribution

| Compliance Level | Count   | Percentage |
| ---------------- | ------- | ---------- |
| 1                | 194,325 | 23.67%     |
| 2                | 3,703   | 0.45%      |
| 3                | 995     | 0.12%      |
| 4                | 9       | 0.00%      |
| 5                | 117     | 0.01%      |
| 6                | 614     | 0.07%      |
| 7                | 34,455  | 4.20%      |
| 8                | 561,368 | 68.39%     |
| 9                | 23,206  | 2.83%      |
| 10               | 2,024   | 0.25%      |
| Total            | 820,816 | 100.00%    |

##### Complexity Level Distribution

| Complexity Level | Count   | Percentage |
| ---------------- | ------- | ---------- |
| 0                | 35      | 0.00%      |
| 1                | 52,841  | 6.44%      |
| 2                | 49,852  | 6.07%      |
| 3                | 49,937  | 6.08%      |
| 4                | 49,743  | 6.06%      |
| 5                | 82,867  | 10.10%     |
| 6                | 408,909 | 49.82%     |
| 7                | 126,258 | 15.38%     |
| 8                | 296     | 0.04%      |
| 9                | 78      | 0.01%      |
| Total            | 820,816 | 100.00%    |

---

#### Sampling Images Statistics Summary

##### Content Theme Statistics

| Theme | Images | Percentage |
| ----- | ------ | ---------- |
| 1     | 602    | 13.18%     |
| 2     | 360    | 7.88%      |
| 3     | 218    | 4.77%      |
| 4     | 208    | 4.55%      |
| 5     | 354    | 7.75%      |
| 6     | 256    | 5.60%      |
| 7     | 196    | 4.29%      |
| 8     | 318    | 6.96%      |
| 9     | 226    | 4.95%      |
| 10    | 223    | 4.88%      |
| 11    | 230    | 5.03%      |
| 12    | 190    | 4.16%      |
| 13    | 353    | 7.73%      |
| 14    | 334    | 7.31%      |
| 15    | 201    | 4.40%      |
| 16    | 247    | 5.41%      |
| 17    | 53     | 1.16%      |
| Total | 4,569  | 100.00%    |

##### Chart Type Statistics

| Type  | Images | Percentage |
| ----- | ------ | ---------- |
| 1     | 1,858  | 50.96%     |
| 2     | 683    | 18.73%     |
| 3     | 4      | 0.11%      |
| 4     | 7      | 0.19%      |
| 5     | 9      | 0.25%      |
| 6     | 535    | 14.67%     |
| 8     | 1      | 0.03%      |
| 9     | 369    | 10.12%     |
| 10    | 3      | 0.08%      |
| 11    | 177    | 4.85%      |
| Total | 3,646  | 100.00%    |

##### Compliance Level Statistics

| Level | Images | Percentage |
| ----- | ------ | ---------- |
| 9     | 2,642  | 85.45%     |
| 10    | 450    | 14.55%     |
| Total | 3,092  | 100.00%    |

##### Complexity Level Statistics

| Level | Images | Percentage |
| ----- | ------ | ---------- |
| 5     | 6      | 0.19%      |
| 6     | 140    | 4.53%      |
| 7     | 2,741  | 88.65%     |
| 8     | 188    | 6.08%      |
| 9     | 17     | 0.55%      |
| Total | 3,092  | 100.00%    |

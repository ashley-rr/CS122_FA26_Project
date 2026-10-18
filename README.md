# CS 122, Fall 2026 Project
## Team: Ashley Roman and Ashley Dai
## Project Name: Piece by Piece: An Analysis of Chess 

## Project Description
This project will investigate the relationship between different statistics in chess games — like that between the opening player, the moves they make, the total number of turns, victory status, and more. With this, we aim analyze how game variables can positively or negatively influence game outcomes. For example, is there a significant comparison between players who make the first move, and win in a mate? We plan to achieve this by first processing the data into the most relevant statistics, then by using data analysis and visualization methods to identify patterns between the variables, all done collaborately via GitHub. At the end, this data will be available to see and interact with on a web-hosted Python interface.

## Project Outline
* Set up GitHub repository
* Download dataset of online chess games from Kaggle
* Perform data preprocessing and cleaning
* Analyze variable relationships using Python
* Display findings on Python interface, emphasizing readability and easy navigation
* Deploy site publicly

### Interface Plan
* Interactive Pie Chart: Toggle between White and Black to view their overall win rates.
* Interactive Bar Chart: Toggle between White and Black to compare win rates across opening moves, with a dropdown menu to select an opening move.

### Data Collection and Storage Plan (Ashley Roman)
We will use this .csv dataset of Lichess chess games from Kaggle: https://www.kaggle.com/datasets/datasnaek/chess/data. 

We plan to first clean the data by handling missing numerical values (replacing them with the mean or median value in their column). The dataset also has a column of opening moves, however one move can have multiple variations (i.e. "Sicilian Defense: Dragon Variation"  vs "Sicilian Defense: Bowdler Attack"). So, we will simplify these variations into their umbrella term.

After preprocessing, the data will be stored into a .csv file, and uploaded to GitHub so that both of us can access and make modifications to the file.

### Data Analysis and Visualization Plan (Ashley Dai)
* Most/Least popular opening moves (Top 10)
  * Frequency Bar Chart
* Is there a statistically significant difference in the proportion of games won by white and black (does not include draws)? 
  * Statistical Test: One Sample Proportion Test
  * Pie Chart showing white/black overall winrate
* Which opening moves have highest/lowest win rates for white and black?
  * Bar Chart
* Does the average game length differ between the top 10 most popular opening moves?
  * Statistical Test: One Way ANOVA Test
  * Visualization: Box Plots


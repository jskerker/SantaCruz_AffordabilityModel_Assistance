# Santa Cruz Affordability Model: Assistance Paper Repository for "Evaluating the role of customer assistance programs to ensure climate-resilient, affordable water"

Python implementation of a systems modeling framework using Pywr for understanding the results in:
- Skerker, J.B., Markey, G., Post, R., Klassert, C., Francois, B., Brown, C., and Fletcher, S.M., Evaluating the role of customer assistance programs to ensure climate-resilient, affordable water, Under Review.
Code documentation by: Jennifer Skerker, Stanford University. Last updated: March 2025.

Notes: This repository includes all of the novel code developed for this work. Please see the PDF "Git Documentation & Organization" for more details.

File Organization
- data: This folder contains data developed for this work, including the Discrete/Continuous Choice (DCC) model coefficients and the risk-of-failure (ROF) tables developed for different reservoir storage levels.
- model_assumptions_and_scenarios: This folder contains json files containing the relevant asssumptions for infrastructure planning and rate development. 
- models: This folder contains the parent models (json files) used in building the systems model. 
- outputs: This folder contains images developed from Microsoft Powerpoint for developing Figure 1.
- results: This folder contains sample results (not household-level results though).
- scripts: This folder contains the Python code developed for this project, as well as Python files to develop paper figures.

Pywr Installation: To install Pywr, please follow the instructions at this link: https://pywr.github.io/pywr-docs/master/install.html. This code was run using PyCharm through Anaconda Navigator. In order to run this on a MacBook with an "Apple Silicon" chip (2022 and newer), you need to create an X86 environment in Anaconda Navigator for Pywr to work. Create the new environment using Python version 3.12 and install the dependencies necessary for Pywr using the following steps:

`conda env create -f environment.yml
conda activate my_env`

Installing Anaconda Navigator, PyCharm, and setting up the x86 environment should take 30-60 minutes.

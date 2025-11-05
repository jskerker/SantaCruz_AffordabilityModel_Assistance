# Santa Cruz Affordability Model: Assistance Paper Repository for "Evaluating the role of customer assistance programs to ensure climate-resilient, affordable water"

Python implementation of a systems modeling framework using Pywr for understanding the results in:
- Skerker, J.B., Markey, G., Post, R., Klassert, C., Francois, B., Brown, C., and Fletcher, S.M., Evaluating the role of customer assistance programs to ensure climate-resilient, affordable water, Under Review.
Code documentation by: Jennifer Skerker, Stanford University. Last updated: November 2025.

Notes: This works builds off of a Pywr-based water supply planning model developed for the Santa Cruz Water Department (SCWD). This model is proprietary and so this repository only includes code developed for this project. Without the proprietary code and data, this model cannot be run. However, all code developed and added for this analysis are included here. Additionally, the household water demand model is parameterized using 13 years of water billing data from SCWD. This data is also not publicly available and so is not included in this repository.

File Organization
- data: This folder contains data developed for this work, including the Discrete/Continuous Choice (DCC) model coefficients and the risk-of-failure (ROF) tables developed for different reservoir storage levels.
- model_assumptions_and_scenarios: This folder contains json files containing the relevant asssumptions for infrastructure planning and rate development. Additionally, a subfolder here contains all of the files used in parameter testing during the sensitivity analysis.
- models: This folder contains the parent models (json files) used in building the systems model. Note: we have removed the nodes, edges, parameters, and recorders that were originally part of the water supply operations model that is not publicly available.
- outputs: This folder contains images developed from Microsoft Powerpoint for developing Figure 1.
- results: This folder is currently empty, but we could add some sample results (not household-level results though).
- scripts: This folder contains the Python code developed for this project, as well as Python files to develop paper figures.

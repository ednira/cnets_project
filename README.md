${\textsf{\huge{\color{teal}Object-centric Causal Nets}}}$

In the paper *Discovering Object-Centric Causal-Nets with Edge-Coarse-Graining in Process Mining*, we introduce a new process mining method to discover Object-Centric Causal Nets - OCCN using edge-coarse-graining. This new method extends Causal Nets to enable object-centric analysis and produces simpler models by merging redundant paths in process models using edge-coarse-graining technique. The detailed approach can be found <a href="https://su.diva-portal.org/smash/record.jsf?pid=diva2:1955576">here</a> in the author's master thesis (2024) at Stockholm University portal DIVA. We implemented this method in Python and evaluated it through a user study, comparing discovered OCCN and Object-Centric Petri Nets, with the study results presented in the paper.

Next, the repository contents and instructions about the tool demonstration are presented.

## Repository Contents
This repository provides supporting material for the paper, including the source code for discovering Object-Centric Causal-Nets with Edge-Coarse-Graining, data, a demonstration Jupyter notebook, and dependencies.

- **code**: two algorithms written in Python,for discovery and visualization, are found at **[cnets_project/object-centric/code](./object-centric/code)**

- **demo**:  the **[`demonstration.ipynb`](./object-centric/demonstration/demonstration.ipynb)**  Jupyter notebook implements the method described in the paper and interactively provides a step-by-step demonstration of the main features.
  
- **data**: the order-management OCEL 2.0 event log in the folder **[cnets_project/object-centric/data](./object-centric/data)** is used in the demonstration Jupyter notebook. It is a public log obtained by simulating the order management log in the former OCEL standard using CPN-Tools. The **[complete description of the order-management business process](https://zenodo.org/records/8428112)** and **[other public OCEL 2.0 event logs](https://www.ocel-standard.org/event-logs/overview/)** are available. To use them with our algorithm, they should be saved in the **[cnets_project/object-centric/data](./object-centric/data)** folder.

- **dependencies**: the **[`requirements.txt`](./requirements.txt)** file contains the packages needed.

## Setup

This tool was developed in **[Python 3.11.0](https://www.python.org/downloads/release/python-3110/)** . To use it, the following is needed:

**1.** Python should be installed in your computer.

**2.** The packages listed in **[`requirements.txt`](./requirements.txt)** should be installed in your computer. This can be achieved by using the following command:

####
    pip install -r requirements.txt

**3.** Launch jupyter lab using the following command and open the notebook *demonstration.ipynb*, referred to in the previous section:

####
    jupyter lab

Note that any OCEL 2.0 files to be used with the notebook should be located in the **[cnets_project/object-centric/data](./object-centric/data)** . In this project, the order-mamangement file is already provided.

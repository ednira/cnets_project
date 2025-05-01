${\textsf{\huge{\color{teal}Object-centric Causal Nets}}}$

In the paper *Discovering Object-Centric Causal-Nets with Edge-Coarse-Graining in Process Mining*, we introduce a new process mining method to discover Object-Centric Causal Nets - OCCN using edge-coarse-graining. This new method extends Causal Nets to enable object-centric analysis and produces simpler models by merging redundant paths in process models using edge-coarse-graining technique. The detailed approach can be found <a href="https://su.diva-portal.org/smash/record.jsf?pid=diva2:1955576">here</a> in the author's master thesis (2024) at Stockholm University portal DIVA. We implemented this method in Python and evaluated it through a user study, comparing discovered OCCN and Object-Centric Petri Nets, with the study results presented in the paper.

## Repository Contents
This repository provides supporting material for the paper, including the source code for discovering Object-Centric Causal-Nets with Edge-Coarse-Graining, data, a demonstration Jupyter notebook, and dependencies.

- **code**: two algorithms written in Python,for discovery and visualization, are found at <a href=cnets_project/object-centric/code>cnets_project/object-centric/code</a>

### ------- Note for Shahrzad -------- :
The code is in the folder 'demonstration' now because we still need to "clean" it (cooments etc). When we have the final files they will be moved to the folder 'code' as indicated in the previous bullet. Please, delete this note after reading it, thanks :)

- **demo**:  a <a href=cnets_project/object-centric/notebook/demonstration.ipynb>Jupyter notebook</a> implements the method described in the paper and interactively provides a step-by-step demonstration of the main features
  
- **data**: the order-management OCEL 2.0 event log in the folder <a href=cnets_project/object-centric/data>cnets_project/object-centric/data</a> is used in the demonstration Jupyter notebook. It is a public log obtained by simulating the order management log in the former OCEL standard using CPN-Tools. The <a href="https://zenodo.org/records/8428112">complete description of the order-management business process</a> and <a href="https://www.ocel-standard.org/event-logs/overview/">other public OCEL 2.0 event logs</a> are available. To use them with our algorithm, they should be saved in the <a href=cnets_project/object-centric/data>cnets_project/object-centric/data</a> folder too.

- **dependencies**: the  <a href=cnets_project/object-centric/dependencies/requirements.txt>`requirements.txt`</a> file contains the packages needed

## Setup



# Discovering Object-Centric Causal-Nets with Edge-Coarse-Graining in Process Mining

This repository contains supporting information for a project on the discovery of **Object-Centric Causal Nets (OCCN)** from **Object-Centric Event Logs (OCEL 2.0)**.  
The project began on **2024-01-15** as a **master thesis** at the [Department of Computer and Systems Sciences](https://dsv.su.se), Stockholm University, and concluded on **2024-11-02**.  
The thesis can be found in the Stockholm University repository:  
📄 <a href="https://su.diva-portal.org/smash/record.jsf?pid=diva2:1955576">https://su.diva-portal.org/smash/record.jsf?pid=diva2:1955576</a>


## 🔍 Overview

This project introduces **Object-Centric Causal Nets (OCCN)**, a novel model that:
- Extends Causal Nets to support **multiple object types**
- Incorporates **edge-coarse-graining** for simpler, interpretable models
- Uses **visual encoding** to distinguish input/output bindings
- Enhances user comprehension through **interactive tooltips** and layout design

The approach has been **implemented in Python**, demonstrated using public OCEL datasets, and evaluated through a **user study** comparing OCCNs with Object-Centric Petri Nets (OCPN).


## 📁 Repository Structure
```
├── cnets_project/
│   ├── README.md                         # Project documentation
│   ├── requirements.txt                  # Python libraries required
│   ├── object-centric/
│   │   ├── code/
│   │   │   ├── discover_occnets.py       # OCCN discovery logic
│   │   │   ├── view_occnets_jupyter.py   # Visualization module for OCCN
│   │   ├── data/
│   │   │   ├── order-management.json     # Sample OCEL log in JSON format
│   │   │   ├── order-management.sqlite   # Sample OCEL log in SQLite format
│   │   ├── demonstration/
│   │   │   ├── demonstration.ipynb       # End-to-end demo notebook
│   │   │   ├── discover_occnets.py       # Duplicate of discovery logic for demo use
│   │   │   ├── order-management.json     # Log used in demo
│   │   │   ├── view_occnets_jupyter.py   # Duplicate visualizer for notebook use
```



## 🚀 Getting Started

### Requirements

- Python 3.8 or higher  
- Install all dependencies:

```bash
pip install -r requirements.txt
```




## Repository Contents
This repository provides supporting material for the paper organized thorugh these directories:

- **code**: This directory contains two algorithms written in Python supporting OCCN discovery and visualization. 

- **demo**:  This directory contains the **[`demonstration.ipynb`](./object-centric/demonstration/demonstration.ipynb)**  Jupyter notebook that implements the method described in the paper and interactively provides a step-by-step demonstration of the main features. The order-management OCEL 2.0 event log is used in the demo. It is a public log obtained by simulating the order management log in the former OCEL standard using CPN-Tools. The **[complete description of the order-management business process](https://zenodo.org/records/8428112)** and **[other public OCEL 2.0 event logs](https://www.ocel-standard.org/event-logs/overview/)** are available at OCEL 2.0 website. To use them with our algorithm, they should be saved in this folder.



## Setup

This tool was developed in **[Python 3.11.0](https://www.python.org/downloads/release/python-3110/)** . To use it, the following is needed:

**1.** Python should be installed in your computer.

**2.** The packages listed in **[`requirements.txt`](./requirements.txt)** should be installed in your computer. This can be achieved by using the following command:

####
    pip install -r requirements.txt

**3.** Launch jupyter lab using the following command and open the notebook *demonstration.ipynb*, referred to in the previous section:

####
    jupyter lab

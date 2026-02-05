# dsf-agent
AI Agent that leverages the [dsf-mobility package](https://github.com/physycom/DynamicalSystemFramework) to simulate traffic flows. Built in LangGraph V1.  

## Usage

Clone this repository:
```bash
$ git clone https://github.com/MatteoFalcioni/dsf-agent
$ cd dsf-agent
```

Then install the required packages:
```bash
$ pip install -r requirements.txt
```

First, run the [cartography notebook](./notebooks/cartography.ipynb) in order to get the necessary files for the simulation.

Then run the code from the root directory of the project with

```bash
$ python -m src.main
```

![alt](https://github.com/MatteoFalcioni/dsf-agent/blob/main/readme_imgs/screenshot.png?raw=true)

## Future Improvements Ideas:

- giving the agent the ability to analize the outputs of the simulation, based on the [coil_compare](https://github.com/physycom/netmob25/blob/main/deprecated/coilcompare.ipynb) notebook;


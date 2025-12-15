# dsf-agent
AI Agent that leverages the [dsf-mobility package](https://github.com/physycom/DynamicalSystemFramework) to simulate traffic flows. Built in LangGraph V1.  

At the moment the implementation consists only of a simple agent that can run the `slow charge` simulation, prompted in natural language. 

## Usage

Clone this repository:
```bash
git clone https://github.com/MatteoFalcioni/dsf-agent
cd dsf-agent
```

First, run the [cartography notebook](./notebooks/cartography.ipynb) in order to get the necessary files for the simulation.

Then run the code from the root directory of the project with

```bash
python -m src.main
```

![alt](https://github.com/MatteoFalcioni/dsf-agent/blob/main/readme_imgs/screenshot.png?raw=true)

## Future Improvements Ideas:

- giving the agent the ability to write python code to analize the outputs of the simulation;

- giving the agent a `visualize_simulation` tool;

- adding to the agents' simulation capabilities (adding features to the underlying model -> translating them to tools)

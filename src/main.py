from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
import asyncio
from dotenv import load_dotenv

from .graph.graph import make_graph

async def main():

    load_dotenv()

    checkpointer = InMemorySaver()

    graph = make_graph(
        checkpointer=checkpointer
    )

    config = {"thread_id": "1"}
    
    print("\n" + "="*60)
    print("DSF Mobility Agent - Interactive Chat")
    print("Type 'exit' or 'quit' to end the session")
    print("="*60 + "\n")

    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting chat...")
            break
        
        if not user_input:
            continue
            
        if user_input.lower() in ['exit', 'quit']:
            print("\nExiting chat...")
            break
        
        # Create initial state 
        init_state = {
            "messages": [HumanMessage(content=user_input)], 
            "edges_filepath" : "./input/true_edges.csv",   # default edges file
            "nodes_filepath" : "./input/bologna_nodes.csv"  # default nodes file
            }
        
        # Stream agent response
        async for chunk in graph.astream(init_state, config=config):
            for node_name, values in chunk.items():
                if 'messages' in values:
                    print("\n" + "*"*25 + f" {node_name} " + "*"*25 + "\n")
                    print(values['messages'][-1].content)
                    print("\n" + "*"*66 + "\n")
        
        print()  # Add spacing between conversations

if __name__ == "__main__":
    asyncio.run(main())

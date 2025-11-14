# dag_gen.py
from graphviz import Digraph

def generate_dag(output_path="debate_dag"):
    dot = Digraph(comment="Debate DAG")
    dot.attr(rankdir='LR')
    # nodes
    dot.node('UserInput', 'UserInputNode\n(Topic)')
    dot.node('AgentA', 'AgentA\n(Scientist)')
    dot.node('AgentB', 'AgentB\n(Philosopher)')
    dot.node('Memory', 'MemoryNode\n(summary per agent)')
    dot.node('Validator', 'StateValidator')
    dot.node('Judge', 'JudgeNode')

    # edges (flow)
    dot.edge('UserInput', 'AgentA')
    dot.edge('AgentA', 'Memory')
    dot.edge('Memory', 'AgentB')
    dot.edge('AgentB', 'Memory')
    dot.edge('Memory', 'Validator')
    dot.edge('Validator', 'Judge')
    dot.edge('AgentA', 'Validator')
    dot.edge('AgentB', 'Validator')

    # render to file (pdf or png)
    # for fmt in ['png', 'pdf']:
    #     dot.render(filename=output_path, format=fmt, cleanup=True)
    # return output_path + ".png"
    try:
        for fmt in ['png', 'pdf']:
            dot.render(filename=output_path, format=fmt, cleanup=True)
        print(f"DAG rendered successfully: {output_path}.png / .pdf")
    except Exception as e:
        print(f"[Warning] DAG rendering skipped: {e}")

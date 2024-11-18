import networkx as nx
import graphCreation as gc
import pandas as pd

G = nx.read_graphml("CourseSkillGraph.graphml")

weights = gc.getCourseSkillWeights(G)
df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count with Course", "Count without Course"])
df.to_excel("CourseSkillWeights.xlsx", index = False)
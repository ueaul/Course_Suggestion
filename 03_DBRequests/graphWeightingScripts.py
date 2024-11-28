import networkx as nx
import graphCreation as gc
import pandas as pd
import sqlite3

G = nx.read_graphml("CourseSkillGraph.graphml")

# Hier die Pfade zu den csv Dateien eingeben
studium_csv = "path"
pruefungsleistung_csv = "path"

studium_df = pd.read_csv(studium_csv)
pruefungsleistung_df = pd.read_csv(pruefungsleistung_csv)
database = "student_database.db"
conn = sqlite3.connect(database)
studium_df.to_sql("studium", conn, if_exists='replace', index=False)
pruefungsleistung_df.to_sql("pruefungsleistung", conn, if_exists='replace', index=False)
conn.close()

#Creation of course -> skill weights
#weights = gc.getCourseSkillWeights(G, database)
#df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count with Course", "Count without Course"])
#df.to_excel("CourseSkillWeights.xlsx", index = False)

#Creation of skill -> course weights
weights = gc.getSkillCourseWeights(G, database)
df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count"])
df.to_excel("CourseSkillWeights.xlsx", index = False)

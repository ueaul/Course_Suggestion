import networkx as nx
import graphCreation_Bachelor as gcB
import graphCreation_Master as gcM
import pandas as pd
import sqlite3

G_Bachelor = nx.read_graphml("CourseSkillGraph_Bachelor.graphml")
G_Master = nx.read_graphml("CourseSkillGraph_Master.graphml")

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
#Bachelor
weights = gcB.getCourseSkillWeights(G_Bachelor, database, 0.001)
df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count with Course", "Count without Course"])
df.to_excel("CourseSkillWeights_Bachelor.xlsx", index = False)
#Master
weights = gcM.getCourseSkillWeights(G_Master, database, 0.001)
df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count with Course", "Count without Course"])
df.to_excel("CourseSkillWeights_Master.xlsx", index = False)


#Creation of skill -> course weights
#weights, edges_to_check = gc.getSkillCourseWeights(G, database)
#df_weights = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count"])
#df_edges_to_check = pd.DataFrame(edges_to_check, columns=["Name", "Name_Full", "Skill"])
#df_weights.to_excel("SkillCourseWeights.xlsx", index = False)
#df_edges_to_check.to_excel("EdgesToCheck.xlsx", index = False)


#Master
#Creation of course -> skill weights
#weights = gcM.getCourseSkillWeights(G_Master, database)
#df = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count with Course", "Count without Course"])
#df.to_excel("CourseSkillWeights_Master.xlsx", index = False)

#Creation of skill -> course weights
#weights, edges_to_check = gcM.getSkillCourseWeights(G_Master, database)
#df_weights = pd.DataFrame(weights, columns=["Weight", "Outgoing", "Ingoing", "Count"])
#df_edges_to_check = pd.DataFrame(edges_to_check, columns=["Name", "Name_Full", "Skill"])
#df_weights.to_excel("SkillCourseWeights_Master.xlsx", index = False)
#df_edges_to_check.to_excel("EdgesToCheck_Master.xlsx", index = False)
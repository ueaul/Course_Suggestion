import networkx as nx
import pandas as pd

def getAvalailableCourses(graph):
    available_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False]

    for course in available_courses:
        incoming_nodes = graph.predecessors(course)
        available = True
        for node in incoming_nodes:
            if graph.nodes[node].get("type") == "course":
                if graph[node][course].get("weight") == 1 and graph.nodes[node].get("active") == False:
                    available = False
                    break
                #ToDo Gleichzeitige Belegung

                elif graph[node][course].get("weight") == 2 and graph.nodes[node].get("active") == False:

                elif graph[node][course].get("weight") == -1 and graph.nodes[node].get("active") == True:
                    available = False
                    break
            elif graph.nodes[node].get("type") == "prerequisite":
                #ToDo check condition


    return available_course


def getAppropriateCourses(graph):



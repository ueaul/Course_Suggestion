import networkx as nx
import pandas as pd
from itertools import combinations

skill_list = ["Software Development Fundamentals (SDF)", "Algorithmic Foundations (AL)",
              "Foundations of Programming Languages (FPL)", "Software Engineering (SE)",
              "Architecture and Organization (AR)", "Operating Systems (OS)", "Networking and Communication (NC)",
              "Parallel and Distributed Computing (PDC)", "Systems Fundamentals (SF)", "Data Management (DM)",
              "Security (SEC)", "Artificial Intelligence (AI)", "Graphics and Interactive Techniques (GIT)",
              "Human-Computer Interaction (HCI)", "Specialized Platform Development (SPD)",
              "Society, Ethics, and the Profession (SEP)", "Mathematical and Statistical Foundations (MSF)",
              "Information Systems (IS)", "Accounting and Taxation (AAT)", "Banking, Finance, and Insurance (FIN)",
              "Management (MAN)", "Marketing and Sales (MKT)", "Operations Management (OPM)", "IT Management (ITM)",
              "Economics (ECO)", "Law (LAW)", "Scientific Work (SW)", "Business Process Management (BPM)"]

pool_names = ["Information Systems", "Computer Science", "Mathematics and Statistics", "Specialization",
         "Key Qualification", "Key Qualification Pool", "Seminar", "Thesis", "Business", "Elective"]

pool_ECTS = [24, 57, 25, 12, 5, 4, 5, 12, 30, 6]




def getCourseAvailability(graph, course, checkedNodes):
    incoming_nodes = graph.predecessors(course)
    available = True
    for node in incoming_nodes:
        if graph.nodes[node].get("type") == "course" or graph.nodes[node].get("type") == "prerequisite":

            if graph[node][course].get("weight") == 1 and graph.nodes[node].get("active") == False:
                available = False
                break

            elif graph[node][course].get("weight") == 2 and graph.nodes[node].get("active") == False:
                if not node in checkedNodes:
                    checkedNodes.append(node)
                    available, tmp = getCourseAvailability(graph, node, checkedNodes)
                    if not available:
                        break

            elif graph[node][course].get("weight") == -1 and graph.nodes[node].get("active") == True:
                available = False
                break

    return available, checkedNodes

def checkSkillLevel(graph, course):
    skill_levels = getSkillLevels(graph)

    incoming_edges = graph.in_edges(course)
    for edge in incoming_edges:
        potential_skill = edge[0]
        if potential_skill in skill_list:
            if skill_levels[skill_list.index(potential_skill)] < graph.edges[edge].get("weight"):
                return False

    return True

def checkEnoughECTS(graph, course, max_ECTS):
    active_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == True and
                        graph.nodes[course].get("type") == "course"]
    active_courses.append(course)
    current_ECTS = 0
    pool_ECTS_left = pool_ECTS.copy()
    for course in active_courses:
        course_ECTS = int(graph.nodes[course].get("ECTS"))
        current_ECTS += course_ECTS
        pool_raw = graph.nodes[course].get("pool")
        pools = [pool.strip() for pool in pool_raw.split("|")]
        if len(pools) > 1:
            for pool in pools:
                pool_index = pool_names.index(pool)
                if pool_ECTS_left[pool_index] > 0:
                    pool_ECTS_left[pool_index] -= course_ECTS
                    if pool_ECTS_left[pool_index] < 0:
                        pool_ECTS_left[pool_index] = 0
                    break
        else:
            pool_index = pool_names.index(pools[0])
            pool_ECTS_left[pool_index] -= course_ECTS
            if pool_ECTS_left[pool_index] < 0:
                pool_ECTS_left[pool_index] = 0

    return max_ECTS - current_ECTS >= sum(pool_ECTS_left)



def getAvailailableCourses(graph, max_ECTS):
    available_courses = []
    inactive_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False and
                        graph.nodes[course].get("type") == "course"]

    for course in inactive_courses:
        available, parallelCourses = getCourseAvailability(graph, course, [course])
        if available:
            if checkSkillLevel(graph, course) and checkEnoughECTS(graph, course, max_ECTS):
                if parallelCourses:
                    available_courses.append(parallelCourses)
                else:
                    available_courses.append(course)

    return available_courses

def getPossibleSemesterPlan(graph, min_ECTS, max_ECTS):
    availableCourses = getAvailailableCourses(graph)
    possibleSemesterPlans = []

    for number_of_courses in range(1, 6):
        for possibleSemesterPlan in combinations(availableCourses, number_of_courses):
            ECTS = 0
            clean_list = []
            for courseCollection in possibleSemesterPlan:
                for course in courseCollection:
                    ECTS += int(graph.nodes[course].get("ECTS"))
                    clean_list.append(course)
            if min_ECTS <= ECTS <= max_ECTS:
                possibleSemesterPlans.append(clean_list)

    return possibleSemesterPlans

def getSkillLevels(graph):
    active_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == True and
                        graph.nodes[course].get("type") == "course"]

    skill_levels = [0] * len(skill_list)
    for course in active_courses:
        outgoing_edges = graph.out_edges(course)
        for edge in outgoing_edges:
            potential_skill = edge[1]
            if potential_skill in skill_list:
                skill_levels[skill_list.index(potential_skill)] += graph.edges[edge].get("weight")

    return(skill_levels)

def activatePrerequisiteNodes(graph, course):
    courses = [course]
    while (len(courses) > 0):
        successors = graph.successors(courses[0])
        for successor in successors:
            if graph.nodes[successor].get("type") == "prerequisite" and graph.nodes[successor].get("active") == False:

                if graph.nodes[successor].get("subtype") == "MIN":
                    minimum = graph.nodes[successor].get("amount")
                    predecessors = graph.predecessors(successor)
                    count_active = 0
                    for predecessor in predecessors:
                        if graph.nodes[predecessor].get("active") == True:
                            count_active += 1
                    if count_active >= minimum:
                        graph.nodes[successor]["active"] = True

                elif graph.nodes[successor].get("subtype") == "MAX":
                    maximum = graph.nodes[successor].get("amount")
                    predecessors = graph.predecessors(successor)
                    count_active = 0
                    for predecessor in predecessors:
                        if graph.nodes[predecessor].get("active") == True:
                            count_active += 1
                    if count_active <= maximum:
                        graph.nodes[successor]["active"] = True

                successor_successors = graph.successors(successor)
                for successor_successor in successor_successors:
                    if graph.nodes[successor_successor].get("type") == "prerequisite" and \
                            graph.nodes[successor_successor].get("active") == False:
                        courses.append(successor)

        courses = courses[1:]

    return graph
def takeCourses(graph, courses):
    for course in courses:
        if not getCourseAvailability(graph, course, [course]):
            print("Incorrect Input, one ore more courses not available")
            break
    for course in courses:
        graph.nodes[course]["active"] = True
        graph = activatePrerequisiteNodes(graph, course)
    return graph


def getAppropriateCourses(graph):
    return None

G = nx.read_graphml("CourseSkillGraph_Bachelor.graphml")
#G = nx.read_graphml("Graph_Master.graphml")
#print(getCourseAvailability(G, 'FIN 541 Corporate Finance I - Case Study (Capital Structure, Cost of Capital and Valuation)', []))
#print(getCourseAvailability(G, 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', []))
#print(G.nodes["CS 304 Programmierpraktikum I Programming Lab I"].get("active"))

#tmp = takeCourses(G, ['ACC 626 Transaction Accounting'])

#tmp = takeCourses(G, ["IS 202a Wirtschaftsinformatik IIa: Einführung in die Modellierung I: Logik Business Informatics IIa: Foundations of Modeling I: logic"])

#print(getCourseAvailability(tmp, 'ACC 626 Transaction Accounting', []))
#print(getCourseAvailability(tmp, 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', []))
#print(G.nodes["CS 304 Programmierpraktikum I Programming Lab I"].get("active"))

#semesterPlans = getPossibleSemesterPlan(G,20,30)

#for i in range(0,50):
   #print(semesterPlans[i])
#print(G.nodes["ACC 530 Group Accounting"].get("ECTS"))
#print(getSkillLevels(G))
print(getAvailailableCourses(G, 6))









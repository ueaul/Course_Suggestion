import networkx as nx
import pandas as pd
from itertools import combinations
import time
import numpy as np


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

required_skill_levels = {}

def initialize(graph):
    courses = [course for course in graph.nodes() if graph.nodes[course].get("type") == "course"]
    for course in courses:
        incoming_edges = graph.in_edges(course)
        for edge in incoming_edges:
            potential_skill = edge[0]
            if potential_skill in skill_list:
                if course not in required_skill_levels:
                    required_skill_levels[course] = {}
                required_skill_levels[course][potential_skill] = graph.edges[edge].get("weight")


def getCourseAvailability(graph, course, checkedNodes, cycle):
    if not graph.nodes[course].get("type") == "course":
        return False, checkedNodes

    if not graph.nodes[course].get("offering_cycle") in ["Continuously", cycle]:
        return False, checkedNodes

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

def checkSkillLevel(graph, courses):
    skill_levels = getSkillLevelsGraph(graph)
    for course in courses:
        incoming_edges = graph.in_edges(course)
        for edge in incoming_edges:
            potential_skill = edge[0]
            if potential_skill in skill_list:
                if skill_levels[skill_list.index(potential_skill)] < graph.edges[edge].get("weight"):
                    return False

    return True

def checkSkillLevel_Efficient(skill_levels, courses):
    for course in courses:
        if course in required_skill_levels:
            skills = required_skill_levels[course]
            for required_skill, required_skill_level in skills.items():
                if required_skill_level > skill_levels[skill_list.index(required_skill)]:
                        return False

    return True

def checkEnoughECTS(graph, courses, max_ECTS, min_semester_ECTS):
    active_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == True and
                        graph.nodes[course].get("type") == "course"]
    active_courses.extend(courses)
    current_ECTS = 0
    pool_ECTS_left_copy = pool_ECTS.copy()
    for course in active_courses:
        course_ECTS = int(graph.nodes[course].get("ECTS"))
        current_ECTS += course_ECTS
        pool_raw = graph.nodes[course].get("pool")
        pools = [pool.strip() for pool in pool_raw.split("|")]
        if len(pools) > 1:
            for pool in pools:
                pool_index = pool_names.index(pool)
                if pool_ECTS_left_copy[pool_index] > 0:
                    pool_ECTS_left_copy[pool_index] -= course_ECTS
                    if pool_ECTS_left_copy[pool_index] < 0:
                        pool_ECTS_left_copy[pool_index] = 0
                    break
        else:
            pool_index = pool_names.index(pools[0])
            pool_ECTS_left_copy[pool_index] -= course_ECTS
            if pool_ECTS_left_copy[pool_index] < 0:
                pool_ECTS_left_copy[pool_index] = 0

    ECTS_left = sum(pool_ECTS_left_copy)
    return max_ECTS - current_ECTS >= ECTS_left and min_semester_ECTS <= ECTS_left

def checkEnoughECTS_Efficient(graph, current_ECTS, pool_ECTS_left, courses, max_ECTS, min_semester_ECTS):
    pool_ECTS_left_copy = pool_ECTS_left.copy()
    current_ECTS_copy = current_ECTS
    for course in courses:
        course_ECTS = int(graph.nodes[course].get("ECTS"))
        current_ECTS_copy += course_ECTS
        pool_raw = graph.nodes[course].get("pool")
        pools = [pool.strip() for pool in pool_raw.split("|")]
        if len(pools) > 1:
            for pool in pools:
                pool_index = pool_names.index(pool)
                if pool_ECTS_left_copy[pool_index] > 0:
                    pool_ECTS_left_copy[pool_index] -= course_ECTS
                    if pool_ECTS_left_copy[pool_index] < 0:
                        pool_ECTS_left_copy[pool_index] = 0
                    break
        else:
            pool_index = pool_names.index(pools[0])
            pool_ECTS_left_copy[pool_index] -= course_ECTS
            if pool_ECTS_left_copy[pool_index] < 0:
                pool_ECTS_left_copy[pool_index] = 0

    #print(pool_ECTS_left)
    ECTS_left = sum(pool_ECTS_left_copy)
    return max_ECTS - current_ECTS_copy >= ECTS_left and min_semester_ECTS <= ECTS_left

def getCurrentECTSLeft(graph):
    active_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == True and
                        graph.nodes[course].get("type") == "course"]
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

    return pool_ECTS_left, current_ECTS


def getAvailailableCourses(graph, max_ECTS, cycle, min_semester_ECTS):
    available_courses = []
    inactive_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False and
                        graph.nodes[course].get("type") == "course"]
    for course in inactive_courses:
        available, parallelCourses = getCourseAvailability(graph, course, [course], cycle)
        if available and checkSkillLevel(graph, parallelCourses) and checkEnoughECTS(graph, parallelCourses, max_ECTS,
                                                                                     min_semester_ECTS):
            available_courses.append(parallelCourses)

    return available_courses

def getAvailailableCourses_Efficient(graph, max_ECTS, cycle, min_semester_ECTS):
    available_courses = []
    inactive_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False and
                        graph.nodes[course].get("type") == "course"]
    skill_levels = getSkillLevelsGraph(graph)
    pool_ECTS_left, current_ECTS = getCurrentECTSLeft(graph)
    for course in inactive_courses:
        available, parallelCourses = getCourseAvailability(graph, course, [course], cycle)
        if available and checkEnoughECTS_Efficient(graph, current_ECTS, pool_ECTS_left, parallelCourses, max_ECTS,
                                                   min_semester_ECTS): #and checkSkillLevel_Efficient(skill_levels, parallelCourses)
            available_courses.append(parallelCourses)
    return available_courses

def getPossibleSemesterPlan(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS, cycle):
    availableCourses = getAvailailableCourses(graph, max_ECTS, cycle)
    possibleSemesterPlans = []

    for number_of_courses in range(1, 8):
        startzeit = time.time()
        for possibleSemesterPlan in combinations(availableCourses, number_of_courses):
            ECTS = 0
            clean_list = []
            for courseCollection in possibleSemesterPlan:
                for course in courseCollection:
                    ECTS += int(graph.nodes[course].get("ECTS"))
                    clean_list.append(course)
            if min_semester_ECTS <= ECTS <= max_semester_ECTS and checkEnoughECTS(graph, clean_list, max_ECTS,
                                                                                  min_semester_ECTS):
                possibleSemesterPlans.append(clean_list)
    return possibleSemesterPlans
def getPossibleSemesterPlan_Efficient(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS, cycle):
    availableCourses = getAvailailableCourses_Efficient(graph, max_ECTS, cycle, min_semester_ECTS)
    possibleSemesterPlans = []
    pool_ECTS_left, current_ECTS = getCurrentECTSLeft(graph)

    for number_of_courses in range(1, 8):
        for possibleSemesterPlan in combinations(availableCourses, number_of_courses):
            ECTS = 0
            clean_list = []
            for courseCollection in possibleSemesterPlan:
                for course in courseCollection:
                    ECTS += int(graph.nodes[course].get("ECTS"))
                    clean_list.append(course)
            if min_semester_ECTS <= ECTS <= max_semester_ECTS and \
                    checkEnoughECTS_Efficient(graph, current_ECTS, pool_ECTS_left, clean_list, max_ECTS,
                                              min_semester_ECTS) and clean_list:
                possibleSemesterPlans.append([clean_list, ECTS])
    return possibleSemesterPlans

def getSkillLevelsGraph(graph):
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

def getSkillLevelsCourse(graph, courses):
    skill_levels = []
    for course in courses:
        skill_levels_course = [0] * len(skill_list)
        outgoing_edges = graph.out_edges(course)
        for edge in outgoing_edges:
            potential_skill = edge[1]
            if potential_skill in skill_list:
                skill_levels_course[skill_list.index(potential_skill)] += graph.edges[edge].get("weight")
        skill_levels.append(skill_levels_course)

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

def calculateRewardFunctionGraph(graph, weights):
    skill_level = getSkillLevelsGraph(graph)
    reward = 0
    for i in range(0, len(skill_level)):
        reward += skill_level[i] * weights[i]

    return reward

def calculateRewardFunctionCourse(graph, weights, courses):
    skill_level = getSkillLevelsCourse(graph, courses)
    reward = 0
    for i in range(0, len(skill_level)):
        reward += skill_level[i] * weights[i]

    return reward

def calculateRewardFunctionWithPenalty(courses, course_rewards, skill_level_graph):
    if not courses:
        return 0
    reward = 0
    for i in range(0, len(courses)):
        penalty = 1
        if courses[i] in required_skill_levels:
            required_skill = 0
            actual_skill = 0
            for sub_key, value in required_skill_levels[courses[i]].items():
                required_skill += value
                actual_skill += skill_level_graph[skill_list.index(sub_key)]
            if required_skill != 0:
                penalty = min(1, actual_skill / required_skill)
        reward += penalty * course_rewards[courses[i]]

    return reward

def calculateRewardFunctionWithPenaltyFuture(graph, courses, course_rewards, skill_level_graph, cycle, max_ECTS, min_semester_ECTS):
    if not courses:
        return 0
    reward = 0
    for i in range(0, len(courses)):
        penalty = 1
        if courses[i] in required_skill_levels:
            required_skill = 0
            actual_skill = 0
            for sub_key, value in required_skill_levels[courses[i]].items():
                required_skill += value
                actual_skill += skill_level_graph[skill_list.index(sub_key)]
            if required_skill != 0:
                penalty = min(1, actual_skill / required_skill)
        reward += penalty * course_rewards[courses[i]]

        graph_copy_tmp = graph.copy()
        takeCourses(graph_copy_tmp, courses, cycle)
        next_cycle = "FWS" if cycle == "SSS" else "SSS"
        future_courses_raw = getAvailailableCourses_Efficient(graph_copy_tmp, max_ECTS, next_cycle, min_semester_ECTS)
        future_courses = []
        for course_collection in future_courses_raw:
            for course in course_collection:
                future_courses.append(course)
        future_reward = calculateRewardFunctionWithPenalty(future_courses, course_rewards, skill_level_graph) / len(future_courses)

    return reward + future_reward
def getBestSemesterPlan(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS, weights):
    possibleSemesterPlans = getPossibleSemesterPlan_Efficient(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS)

    currentReward = calculateRewardFunctionGraph(graph, weights)
    bestReward = currentReward
    bestSemesterPlan = []

    for semesterPlan in possibleSemesterPlans:
        tmp = graph.copy()
        takeCourses(tmp,semesterPlan)
        reward = calculateRewardFunctionGraph(tmp, weights)
        if reward > bestReward:
            bestReward = reward
            bestSemesterPlan = semesterPlan

    return bestSemesterPlan



def takeCourses(graph, courses, cycle):
    for course in courses:
        if not getCourseAvailability(graph, course, [course], cycle)[0]:
            print("Incorrect Input, one ore more courses not available")
            break
    for course in courses:
        graph.nodes[course]["active"] = True
        graph = activatePrerequisiteNodes(graph, course)
    return graph


def getCourseSuggestion(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS, weights):
    possibleCourseOfStudies = []

    courseSuggestions = getPossibleSemesterPlan_Efficient(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS)
    for courseSuggestion in courseSuggestions:
        graph_copy = graph.copy()
        takeCourses(graph_copy, courseSuggestion[0])
        reward = calculateRewardFunctionCourse(graph, weights, courseSuggestion[0])
        possibleCourseOfStudies.append([courseSuggestion[0], graph_copy, reward, courseSuggestion[1]])

    finished = False
    while not finished:
        finished = True
        for possibleCourseOfStudy in possibleCourseOfStudies[:]:
            if possibleCourseOfStudy[3] < max_ECTS:
                courseSuggestions = getPossibleSemesterPlan_Efficient(possibleCourseOfStudy[1], min_semester_ECTS,
                                                                      max_semester_ECTS, max_ECTS)
                if courseSuggestion:
                    finished = False
                    for courseSuggestion in courseSuggestions:
                        graph_copy = possibleCourseOfStudy[1].copy()
                        takeCourses(graph_copy, courseSuggestion[0])
                        reward = calculateRewardFunctionCourse(graph, weights, courseSuggestion[0])
                        possibleCourseOfStudies.append([possibleCourseOfStudy[0].append(courseSuggestion[0]), graph_copy,
                                                       possibleCourseOfStudy[2] + reward,
                                                       possibleCourseOfStudy[2] + courseSuggestion[1]])
                    possibleCourseOfStudies.remove(possibleCourseOfStudy)

    bestCourseOfStudy = []
    bestReward = 0
    for possibleCourseOfStudy in possibleCourseOfStudies:
        if possibleCourseOfStudy[2] > bestReward:
            bestCourseOfStudy = possibleCourseOfStudy
            bestReward = possibleCourseOfStudy[2]

    return bestCourseOfStudy

def getCourseRewards(graph, weights):
    courseRewards = {}
    courses = [course for course in graph.nodes() if graph.nodes[course].get("type") == "course"]
    for course in courses:
        reward = 0
        skill_levels_course = [0] * len(skill_list)
        outgoing_edges = graph.out_edges(course)
        for edge in outgoing_edges:
            potential_skill = edge[1]
            if potential_skill in skill_list:
                skill_levels_course[skill_list.index(potential_skill)] += graph.edges[edge].get("weight")

        for i in range(0, len(skill_levels_course)):
            reward += skill_levels_course[i] * weights[i]

        courseRewards[course] = reward

    return courseRewards


def courseSuggestionGreedy(graph, min_semester_ECTS, max_semester_ECTS, max_ECTS, weights, startCycle, max_semester_amount):
    current_ECTS = 0
    bestSemesterPlan = []
    graph_copy = graph.copy()
    rewardlessCourses = set(getRewardlessCourses(graph))
    courseRewards = getCourseRewards(graph, weights)
    while current_ECTS < max_ECTS:
        possibleSemesterPlans = getPossibleSemesterPlan_Efficient(graph_copy, min_semester_ECTS, max_semester_ECTS,
                                                                  max_ECTS, startCycle)
        skill_level_graph = getSkillLevelsGraph(graph_copy)
        bestReward = -1
        candidates = []
        for possibleSemesterPlan in possibleSemesterPlans:
            #reward = calculateRewardFunctionWithPenalty(possibleSemesterPlan[0], courseRewards, skill_level_graph)
            reward = calculateRewardFunctionWithPenaltyFuture(graph, possibleSemesterPlan[0], courseRewards,
                                                              skill_level_graph, startCycle, max_ECTS, min_semester_ECTS)
            if reward > bestReward:
                bestReward = reward
                candidates = [possibleSemesterPlan]
            elif reward == bestReward:
                candidates.append(possibleSemesterPlan)

        if candidates:
            smallestCourseAmount = 100000
            mostRewardlessCourses = -1
            bestCandidate = []
            for candidate in candidates:
                rewardlessCoursesAmount = sum(1 for course in candidate[0] if course in rewardlessCourses)
                courseAmount = len(candidate[0]) - rewardlessCoursesAmount
                if courseAmount <= smallestCourseAmount:
                    if courseAmount == smallestCourseAmount and rewardlessCoursesAmount > mostRewardlessCourses:
                        mostRewardlessCourses = rewardlessCoursesAmount
                        bestCandidate = candidate

                    elif courseAmount < smallestCourseAmount:
                        mostRewardlessCourses = rewardlessCoursesAmount
                        smallestCourseAmount = courseAmount
                        bestCandidate = candidate

            bestSemesterPlan.append(bestCandidate)
            current_ECTS += bestCandidate[1]
            takeCourses(graph_copy, bestCandidate[0], startCycle)

        if startCycle == "FWS":
            startCycle = "SSS"
        else:
            startCycle = "FWS"

    return bestSemesterPlan, current_ECTS

def getRewardlessCourses(graph):
    rewardlessCourses = []
    for node in graph.nodes:
        if graph.nodes[node].get("type") == "course":
            outgoing_edges = graph.out_edges(node)
            isRewardless = True
            for edge in outgoing_edges:
                if graph.nodes[edge[1]].get("type") == "skill":
                    isRewardless = False
                    break
        if isRewardless:
            rewardlessCourses.append(node)

    return rewardlessCourses




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

startzeit = time.time()
#print(getSkillLevelsGraph(G))
initialize(G)
#print(required_skill_levels["Produktion"])
#availableCourses = getAvailailableCourses(G,180)
#availableCourses_Efficient = getAvailailableCourses_Efficient(G,180)
#print(getCourseAvailability(G, "Produktion", ["Produktion"]))
weights = [5, 1,
              5, 1,
              1, 1, 1,
              1, 1, 1,
              1, 1, 1,
              1, 1,
              1, 1,
              1, 1, 1,
              1, 2, 1, 1,
              1, 1, 1, 1]

#print(getCourseSuggestion(G, 26, 34, 180, weights))
#courses_FWS = ['IS 203 Wirtschaftsinformatik III: Development and Management of Information Systems Business Informatics III: Development and Management of Information Systems', 'CS 301 Formale Grundlagen der Informatik Formal Foundations of Computer Science', 'CS 302 Praktische Informatik I Practical Computer Science I', 'CS 304 Programmierpraktikum I Programming Lab I', 'MAT 303 Lineare Algebra I Linear Algebra I', 'CS 307 Algorithmen und Datenstrukturen Algorithms and Data Structures', 'CS 309 Datenbanksysteme I Database Systems I', 'CS 408 Selected Topics in IT-Security Selected Topics in IT-Security', 'BA 450 Bachelor-Abschlussarbeit Bachelor Thesis', 'IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen Business Informatics I: Introduction and Foundations', 'Finanzwirtschaft']
#for course in courses_FWS:
    #takeCourses(G,[course],"FWS")
#courses_SSS = ['IS 202a Wirtschaftsinformatik IIa: Einführung in die Modellierung I: Logik Business Informatics IIa: Foundations of Modeling I: logic', 'IS 202b Wirtschaftsinformatik IIb: Einführung in die Modellierung II: Prozessmodelle Business Informatics IIb: Foundations of Modeling II: process models', 'CS 303 Praktische Informatik II Practical Computer Science II', 'CS 305 Programmierpraktikum II Programming Lab II', 'CS 306 Praktikum Software Engineering Software Engineering Practical', 'CS 406 Theoretische Informatik Theoretical Computer Science', 'Programmierkurs C/C++', 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', 'CS 308 Softwaretechnik I Software Engineering I', 'ANA 301 Analysis für Wirtschaftsinformatiker Analysis for Business Informatics', 'Grundlagen der Statistik Foundations of Statistics', 'Management', 'Grundlagen des externen Rechnungswesens', 'Internes Rechnungswesen']
#for course in courses_SSS:
    #takeCourses(G,[course],"SSS")
#print(getPossibleSemesterPlan_Efficient(G, 12, 34, 180, "FWS"))
#print(getCourseAvailability(G, "Marketing", ["Recht"], "FWS"))
print(courseSuggestionGreedy(G, 0, 32, 180, weights, "FWS", 6))
#print(getAvailailableCourses_Efficient(G, 180, "FWS", 0))
endzeit = time.time()
ausfuehrungszeit = endzeit - startzeit
print(f"Die Methode hat {ausfuehrungszeit:.5f} Sekunden benötigt.")

#for i in range(0,50):
#   print(semesterPlans[i])
#print(G.nodes["ACC 530 Group Accounting"].get("ECTS"))
#print(getSkillLevels(G))
#print(checkEnoughECTS(G, "IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen Business Informatics I: Introduction and Foundations", 180))
#print(required_skill_levels)
#print(getAvailailableCourses_Efficient(G, 180))










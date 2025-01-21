import copy

import networkx as nx
import pandas as pd
from itertools import combinations
import time
import numpy as np
from pyomo.environ import *



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

def checkExclusive(graph, courses):
    excluded_courses = {
        edge[0]
        for course in courses
        for edge in graph.in_edges(course, data=True)
        if str(edge[2].get("weight")) in {"-1", "3"} and edge[2].get("type") == "course"
    }
    return not any(course in excluded_courses for course in courses)


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
                    available, tmp = getCourseAvailability(graph, node, checkedNodes, cycle)
                    if not available:
                        break

            elif graph[node][course].get("weight") == -1 and graph.nodes[node].get("active") == True:
                available = False
                break

    return available, checkedNodes


def checkEnoughECTS(graph, current_ECTS, pool_ECTS_left, courses, max_ECTS):
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

    ECTS_left = sum(pool_ECTS_left_copy)
    return max_ECTS - current_ECTS_copy >= ECTS_left



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



def getAvailailableCourses(graph, max_ECTS, cycle, courses =[]):
    available_courses = []
    if courses:
        inactive_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False and
                            graph.nodes[course].get("type") == "course" and course in courses]
    else:
        inactive_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == False and
                            graph.nodes[course].get("type") == "course"]
    #skill_levels = getSkillLevelsGraph(graph)
    pool_ECTS_left, current_ECTS = getCurrentECTSLeft(graph)
    for course in inactive_courses:
        available, parallelCourses = getCourseAvailability(graph, course, [course], cycle)
        if available and checkEnoughECTS(graph, current_ECTS, pool_ECTS_left, parallelCourses, max_ECTS):
            available_courses.append(parallelCourses)
    return available_courses, pool_ECTS_left, current_ECTS

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



def getPenalty(course, skill_level_graph):
    if course not in required_skill_levels:
        return 1

    required_skills = required_skill_levels[course]
    required_skill = sum(required_skills.values())
    actual_skill = sum(
        min(skill_level_graph[skill_list.index(sub_key)], value)
        for sub_key, value in required_skills.items()
    )

    return (actual_skill / required_skill) if required_skill > 0 else 1

def calculateRewardFunctionWithPenalty(courses, course_rewards, skill_level_graph):
    if not courses:
        return 0

    return sum(
        getPenalty(course, skill_level_graph) * course_rewards[course]
        for course in courses
    )


def takeCourses(graph, courses, cycle):
    for course in courses:
        if not getCourseAvailability(graph, course, [course], cycle)[0]:
            print("Incorrect Input, one ore more courses not available")
            break
    for course in courses:
        graph.nodes[course]["active"] = True
        graph = activatePrerequisiteNodes(graph, course)
    return graph

def getSemesterValidPartial(graph, semester, courses, cycle):
    valid_swap = True
    for course in courses:
        available, parallelCourses = getCourseAvailability(graph, course, [course], cycle)
        if not available:
            valid_swap = False
        elif len(parallelCourses) > 1:
            for parallelCourse in parallelCourses:
                if not (parallelCourse in semester or parallelCourse in courses):
                    valid_swap = False
    return valid_swap

def getSemesterValid(graph, semester, cycle):
    valid_swap = True
    for course in semester:
        available, parallelCourses = getCourseAvailability(graph, course, [course], cycle)
        if not available:
            valid_swap = False
            break
        elif len(parallelCourses) > 1:
            for parallelCourse in parallelCourses:
                if not (parallelCourse in semester):
                    valid_swap = False
                    break
    return valid_swap

def getSwapPossibilities(graph, start, semester_plan, max_semester_ECTS, course_ECTS,
                         step_size, start_cycle, courses):
    swap_possibilities = []
    valid_check_semester = copy.deepcopy(semester_plan[start])
    for course in courses:
        valid_check_semester[0].remove(course)
    for j in range(start+step_size, len(semester_plan), step_size):
        if semester_plan[j][1] + int(course_ECTS) <= max_semester_ECTS:
            swap_possibilities.append([j, None])

        needed_ECTS = abs(max_semester_ECTS - semester_plan[j][1] - int(course_ECTS))
        swap_ECTS = 0
        course_amount = 0
        swap_course_pool = copy.deepcopy(semester_plan[j][0])
        if swap_course_pool:
            while swap_ECTS < needed_ECTS and swap_course_pool:
                min_ECTS_course = min(swap_course_pool, key=lambda tmp: int(graph.nodes[tmp].get("ECTS")))
                swap_ECTS += int(graph.nodes[min_ECTS_course].get("ECTS"))
                swap_course_pool.remove(min_ECTS_course)
                course_amount += 1
            if swap_ECTS >= needed_ECTS:
                for k in range(course_amount, len(semester_plan[j][0]) + 1):
                    for possible_swap_comb in combinations(semester_plan[j][0], k):
                        if getSemesterValidPartial(graph, valid_check_semester, possible_swap_comb, start_cycle):
                            lost_ECTS = sum(int(graph.nodes[swap_course].get("ECTS")) for swap_course in possible_swap_comb)
                            if semester_plan[j][1] - lost_ECTS + int(course_ECTS) <= max_semester_ECTS and \
                                semester_plan[start][1] - int(course_ECTS) + lost_ECTS <= max_semester_ECTS:
                                swap_possibilities.append([j, possible_swap_comb])

    return swap_possibilities

def getParallelCourses(graph, courses):
    parallel_courses = []
    courses_to_skip = set()
    for course in courses:
        if not course in courses_to_skip:
            potential_parallel_courses = [course]
            incoming_edges = graph.in_edges(course)
            outgoing_edges = graph.out_edges(course)
            for edge in incoming_edges:
                if graph.edges[edge].get("weight") == 2 and (course, edge[0]) in outgoing_edges:
                    if graph.edges[course, edge[0]].get("weight") == 2:
                        potential_parallel_courses.append(edge[0])
            if len(potential_parallel_courses) > 1:
                parallel_courses.append(potential_parallel_courses)
                courses_to_skip.update(potential_parallel_courses)
            else:
                parallel_courses.append([course])
    return parallel_courses
def getParallelCycle(graph, courses):
    cycle = None
    for course in courses:
        cycle = graph.nodes[course].get("offering_cycle")
        if not cycle == "Continously":
            break
    return cycle


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

def courseSuggestionGreedy(graph, max_semester_ECTS, max_ECTS, startCycle, courseRewards):
    current_ECTS = 0
    bestSemesterPlan = []
    graph_copy = graph.copy()
    while current_ECTS < max_ECTS:
        bestCandidate = getBestSemesterPlan(graph_copy, max_semester_ECTS, max_ECTS, startCycle, courseRewards)

        bestSemesterPlan.append(bestCandidate)
        current_ECTS += bestCandidate[1]
        takeCourses(graph_copy, bestCandidate[0], startCycle)

        if startCycle == "FWS":
            startCycle = "SSS"
        else:
            startCycle = "FWS"

    return bestSemesterPlan, current_ECTS

def getBestSemesterPlan(graph, max_semester_ECTS, max_ECTS, cycle, course_rewards, successors = []):
    availableCourses, pool_ECTS_left, current_ECTS = getAvailailableCourses(graph, max_ECTS, cycle)
    available_courses_with_reward = []
    skill_levels_graph = getSkillLevelsGraph(graph)
    for courses in availableCourses:
        reward = calculateRewardFunctionWithPenalty(courses, course_rewards, skill_levels_graph)
        courses_ECTS = sum(int(graph.nodes[course].get("ECTS")) for course in courses)
        available_courses_with_reward.append([courses, reward / courses_ECTS])

    available_courses_with_reward_sorted =  sorted(available_courses_with_reward, key=lambda x: x[1], reverse=True)
    best_semester_plan = []

    for courses in available_courses_with_reward_sorted:
        best_semester_plan_candidate = best_semester_plan.copy()
        best_semester_plan_candidate.extend(courses[0])
        best_semester_plan_candidate_ECTS = sum(int(graph.nodes[course].get("ECTS")) for course in best_semester_plan_candidate)
        if best_semester_plan_candidate_ECTS <= max_semester_ECTS and all(course in best_semester_plan_candidate for course in successors) and \
            checkExclusive(graph, best_semester_plan_candidate) and \
            checkEnoughECTS(graph, current_ECTS, pool_ECTS_left, best_semester_plan_candidate, max_ECTS) and best_semester_plan_candidate:
            best_semester_plan.extend(courses[0])


    best_semester_plan_ECTS = sum(int(graph.nodes[course].get("ECTS")) for course in best_semester_plan)
    return [best_semester_plan, best_semester_plan_ECTS]

def optimizeCourseSuggestion(graph, max_semester_ECTS, course_rewards, semester_plan,
                             start_cycle, stop_criterion):

    optimized_plan = copy.deepcopy(semester_plan)

    for loop in range(stop_criterion):
        old_plan_reward = getPlanReward(graph, optimized_plan, start_cycle, course_rewards)[0]
        graph_copy = graph.copy()
        cycle = start_cycle
        for i in range(len(optimized_plan) - 1):
            skill_level = getSkillLevelsGraph(graph_copy)
            courses_with_penalty = []
            parallel_courses = getParallelCourses(graph_copy, optimized_plan[i][0])

            for courses in parallel_courses:
                potential = 0
                for course in courses:
                    potential += (1 - getPenalty(course, skill_level)) * course_rewards[course]
                potential /= len(courses)
                courses_with_penalty.append([courses, potential])
            courses_with_penalty_sorted = sorted(courses_with_penalty, key=lambda x: x[1], reverse=True)
            for course_penalty in courses_with_penalty_sorted:
                courses = course_penalty[0]
                courses_ECTS = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in courses)
                courses_cycle = getParallelCycle(graph_copy, courses)
                if courses_cycle == "Continuously":
                    swap_possibilities = getSwapPossibilities(graph_copy, i, optimized_plan,
                                                              max_semester_ECTS, courses_ECTS, 1, courses_cycle, courses)
                else:
                    swap_possibilities = getSwapPossibilities(graph_copy, i, optimized_plan,
                                                              max_semester_ECTS, courses_ECTS, 2, courses_cycle, courses)

                best_swap = []
                best_swap_reward = -1
                for swap_possibility in swap_possibilities:
                    graph_copy_swap = graph_copy.copy()
                    swap_semester = swap_possibility[0]
                    swap_cycle = cycle
                    old_reward = getPlanReward(graph_copy, optimized_plan[i:swap_semester+1], swap_cycle, course_rewards)[0]
                    possible_new_plan = copy.deepcopy(optimized_plan)
                    possible_new_plan[i][0] = [tmp for tmp in possible_new_plan[i][0] if tmp not in courses]
                    possible_new_plan[swap_semester][0].extend(courses)
                    if swap_possibility[1] is not None:
                        possible_new_plan[i][0].extend(swap_possibility[1])
                        possible_new_plan[swap_semester][0] = [tmp for tmp in possible_new_plan[swap_semester][0] if tmp not in swap_possibility[1]]
                    new_reward = calculateRewardFunctionWithPenalty(possible_new_plan[i][0], course_rewards, skill_level)
                    for j in range(i+1, swap_semester+1):
                        takeCourses(graph_copy_swap, possible_new_plan[j-1][0], swap_cycle)
                        swap_cycle = "FWS" if swap_cycle == "SSS" else "SSS"
                        if getSemesterValid(graph_copy_swap, possible_new_plan[j][0], swap_cycle):
                            skill_level_swap = getSkillLevelsGraph(graph_copy_swap)
                            new_reward += calculateRewardFunctionWithPenalty(possible_new_plan[j][0], course_rewards, skill_level_swap)
                        else:
                            new_reward = -1
                            break
                    if new_reward - old_reward > best_swap_reward:
                        best_swap = swap_possibility
                        best_swap_reward = new_reward - old_reward
                if best_swap_reward > 0:
                    #print("Swapped: " + str(courses) + "with " + str(best_swap))
                    optimized_plan[i][0] = [course for course in optimized_plan[i][0] if course not in courses]
                    optimized_plan[best_swap[0]][0].extend(courses)
                    if best_swap[1] is not None:
                        optimized_plan[i][0].extend(best_swap[1])
                        optimized_plan[best_swap[0]][0] = [tmp for tmp in optimized_plan[best_swap[0]][0] if
                                                               tmp not in best_swap[1]]

                    optimized_plan[i][1] = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in optimized_plan[i][0])
                    optimized_plan[best_swap[0]][1] = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in optimized_plan[best_swap[0]][0])

            takeCourses(graph_copy, optimized_plan[i][0], cycle)
            cycle = "FWS" if cycle == "SSS" else "SSS"

    return(optimized_plan)


def twoStepAlgo(graph, max_semester_ECTS, max_ECTS, weights, startCycle, stop_criterion):
    initialize(graph)
    start_cycle_working_copy = startCycle
    courseRewards = getCourseRewards(graph, weights)
    greedy_suggestion = courseSuggestionGreedy(graph, max_semester_ECTS, max_ECTS, start_cycle_working_copy, courseRewards)
    greedy_courses = []
    greedy_order = []
    semester_index = 0
    for semester in greedy_suggestion[0]:
        for course in semester[0]:
            greedy_courses.append(course)
            greedy_order.append(semester_index)
        semester_index += 1

    final_suggestion = optimizeCourseSuggestion(graph, max_semester_ECTS, courseRewards, greedy_suggestion[0],
                             start_cycle_working_copy, stop_criterion)

    return greedy_suggestion, final_suggestion

def getPlanReward(graph, plan, start_cycle, course_rewards):
    reward = 0
    rewards = []
    graph_copy = graph.copy()
    cycle = start_cycle
    for i in range(len(plan)):
        skill_level = getSkillLevelsGraph(graph_copy)
        semester_reward = calculateRewardFunctionWithPenalty(plan[i][0], course_rewards, skill_level)
        reward += semester_reward
        rewards.append(semester_reward)
        takeCourses(graph_copy, plan[i][0], cycle)
        cycle = "FWS" if cycle == "SSS" else "SSS"

    return reward, rewards

def printSkillDiff(graph, plan, cycle, course_rewards):
    graph_copy = graph.copy()
    for semester in plan:
        print("Semester")
        skill_level_graph = getSkillLevelsGraph(graph_copy)
        for course in semester[0]:
            if course in required_skill_levels:
                required_skills = required_skill_levels[course]
                required_skill = sum(required_skills.values())
                actual_skill = sum(
                    min(skill_level_graph[skill_list.index(sub_key)], value)
                    for sub_key, value in required_skills.items()
                )
            else:
                required_skill = 0
                actual_skill = 0

            print(course + ": " + str(actual_skill - required_skill) + ", " + str(course_rewards[course]))
        takeCourses(graph_copy, semester[0], cycle)
        cycle = "FWS" if cycle == "SSS" else "SSS"




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
#initialize(G)
#print(required_skill_levels["Produktion"])
#availableCourses = getAvailailableCourses(G,180)
#availableCourses_Efficient = getAvailailableCourses_Efficient(G,180)
#print(getCourseAvailability(G, "Produktion", ["Produktion"]))
weights = [1, 1,
              1, 1,
              1, 1, 1,
              1, 1, 1,
              1, 1, 1,
              1, 1,
              1, 1,
              1, 1, 1,
              1, 1, 1, 1,
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

greedy, final = twoStepAlgo(G, 34, 180, weights, "FWS", 5)
course_rewards = getCourseRewards(G, weights)
#final = optimizeCourseSuggestion(G, 0, 34, 180, course_rewards, [[['IS 203 Wirtschaftsinformatik III: Development and Management of Information Systems Business Informatics III: Development and Management of Information Systems', 'CS 301 Formale Grundlagen der Informatik Formal Foundations of Computer Science', 'CS 302 Praktische Informatik I Practical Computer Science I', 'CS 304 Programmierpraktikum I Programming Lab I', 'MAT 303 Lineare Algebra I Linear Algebra I'], 34], [['IS 202a Wirtschaftsinformatik IIa: Einführung in die Modellierung I: Logik Business Informatics IIa: Foundations of Modeling I: logic', 'IS 202b Wirtschaftsinformatik IIb: Einführung in die Modellierung II: Prozessmodelle Business Informatics IIb: Foundations of Modeling II: process models', 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', 'CS 303 Praktische Informatik II Practical Computer Science II', 'CS 305 Programmierpraktikum II Programming Lab II', 'CS 306 Praktikum Software Engineering Software Engineering Practical', 'Präsentationskompetenz und Rhetorik Presentation skills and rhetoric', 'Programmierkurs C/C++'], 34], [['IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen Business Informatics I: Introduction and Foundations', 'CS 307 Algorithmen und Datenstrukturen Algorithms and Data Structures', 'CS 309 Datenbanksysteme I Database Systems I', 'CS 405 Künstliche Intelligenz Artificial Intelligence', 'CS 408 Selected Topics in IT-Security Selected Topics in IT-Security'], 34], [['CS 308 Softwaretechnik I Software Engineering I', 'ANA 301 Analysis für Wirtschaftsinformatiker Analysis for Business Informatics', 'Grundlagen der Statistik Foundations of Statistics', 'SM 444 Bachelorseminar Prof. Bizer Seminar', 'Management'], 33], [['Zeitmanagement Time Management', 'Change- und Projektmanagement Projectmanagement', 'Finanzwirtschaft', 'Marketing', 'Produktion', 'Recht'], 27], [['BA 450 Bachelor-Abschlussarbeit Bachelor Thesis', 'Grundlagen des externen Rechnungswesens'], 18]]
#, "FWS", 6, 0.01)
#greedy = ([[['IS 203 Wirtschaftsinformatik III: Development and Management of Information Systems Business Informatics III: Development and Management of Information Systems', 'CS 301 Formale Grundlagen der Informatik Formal Foundations of Computer Science', 'CS 302 Praktische Informatik I Practical Computer Science I', 'CS 304 Programmierpraktikum I Programming Lab I', 'MAT 303 Lineare Algebra I Linear Algebra I'], 34], [['IS 202a Wirtschaftsinformatik IIa: Einführung in die Modellierung I: Logik Business Informatics IIa: Foundations of Modeling I: logic', 'IS 202b Wirtschaftsinformatik IIb: Einführung in die Modellierung II: Prozessmodelle Business Informatics IIb: Foundations of Modeling II: process models', 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', 'CS 303 Praktische Informatik II Practical Computer Science II', 'CS 305 Programmierpraktikum II Programming Lab II', 'CS 306 Praktikum Software Engineering Software Engineering Practical', 'Präsentationskompetenz und Rhetorik Presentation skills and rhetoric', 'Programmierkurs C/C++'], 34], [['IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen Business Informatics I: Introduction and Foundations', 'CS 307 Algorithmen und Datenstrukturen Algorithms and Data Structures', 'CS 309 Datenbanksysteme I Database Systems I', 'CS 405 Künstliche Intelligenz Artificial Intelligence', 'CS 408 Selected Topics in IT-Security Selected Topics in IT-Security'], 34], [['CS 308 Softwaretechnik I Software Engineering I', 'ANA 301 Analysis für Wirtschaftsinformatiker Analysis for Business Informatics', 'Grundlagen der Statistik Foundations of Statistics', 'SM 444 Bachelorseminar Prof. Bizer Seminar', 'Management'], 33], [['Zeitmanagement Time Management', 'Change- und Projektmanagement Projectmanagement', 'Finanzwirtschaft', 'Marketing', 'Produktion', 'Recht'], 27], [['BA 450 Bachelor-Abschlussarbeit Bachelor Thesis', 'Grundlagen des externen Rechnungswesens'], 18]], 180)
#final = [[['IS 203 Wirtschaftsinformatik III: Development and Management of Information Systems Business Informatics III: Development and Management of Information Systems', 'CS 301 Formale Grundlagen der Informatik Formal Foundations of Computer Science', 'CS 302 Praktische Informatik I Practical Computer Science I', 'CS 304 Programmierpraktikum I Programming Lab I', 'MAT 303 Lineare Algebra I Linear Algebra I'], 34], [['IS 202a Wirtschaftsinformatik IIa: Einführung in die Modellierung I: Logik Business Informatics IIa: Foundations of Modeling I: logic', 'IS 202b Wirtschaftsinformatik IIb: Einführung in die Modellierung II: Prozessmodelle Business Informatics IIb: Foundations of Modeling II: process models', 'CS 303 Praktische Informatik II Practical Computer Science II', 'CS 305 Programmierpraktikum II Programming Lab II', 'Präsentationskompetenz und Rhetorik Presentation skills and rhetoric', 'SM 444 Bachelorseminar Prof. Bizer Seminar', 'ANA 301 Analysis für Wirtschaftsinformatiker Analysis for Business Informatics'], 32], [['IS 201 Wirtschaftsinformatik I: Einführung und Grundlagen Business Informatics I: Introduction and Foundations', 'CS 307 Algorithmen und Datenstrukturen Algorithms and Data Structures', 'Finanzwirtschaft', 'Marketing', 'Zeitmanagement Time Management'], 27], [['CS 308 Softwaretechnik I Software Engineering I', 'Grundlagen der Statistik Foundations of Statistics', 'Management', 'IS 204 Wirtschaftsinformatik IV Business Informatics IV', 'CS 306 Praktikum Software Engineering Software Engineering Practical'], 31], [['Change- und Projektmanagement Projectmanagement', 'Produktion', 'Recht', 'CS 408 Selected Topics in IT-Security Selected Topics in IT-Security', 'CS 405 Künstliche Intelligenz Artificial Intelligence', 'CS 309 Datenbanksysteme I Database Systems I'], 34], [['BA 450 Bachelor-Abschlussarbeit Bachelor Thesis', 'Grundlagen des externen Rechnungswesens', 'Programmierkurs C/C++'], 22]]

#printSkillDiff(G, final, "FWS", course_rewards)


#final = optimizeCourseSuggestion(G, 34, 180, course_rewards, greedy[0], "FWS", 6, 0.01)

print(greedy)
print(final)
print("Reward greedy: " + str(getPlanReward(G, greedy[0], "FWS", course_rewards)))
print("Reward final: " + str(getPlanReward(G, final, "FWS", course_rewards)))
#print(getCourseRewards(G,))
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







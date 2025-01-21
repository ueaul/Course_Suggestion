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

pool_names = ["Fundamentals Computer Science", "Fundamentals Business Administration", "Specialization Courses",
         "Seminars", "Projects", "Scientific Research", "Thesis"]

pool_ECTS = [18, 18, 36, 4, 12, 2, 30]

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
        for edge in graph.in_edges(course, data="weight")
        if str(edge[2]) in {"-1", "3"}
    }
    return not any(course in excluded_courses for course in courses)

def getCurrentECTS(graph):
    active_courses = [course for course in graph.nodes() if graph.nodes[course].get("active") == True and
                      graph.nodes[course].get("type") == "course"]
    return sum(int(graph.nodes[tmp].get("ECTS")) for tmp in active_courses)

def getCourseAvailability(graph, course, checkedNodes, cycle):
    if course == "MA 650 Master Thesis":
         currentECTS = getCurrentECTS(graph)
         if currentECTS < 60:
             return False, checkedNodes
    if not graph.nodes[course].get("type") == "course":
        return False, checkedNodes

    if not graph.nodes[course].get("offering_cycle") in ["Continuously", cycle]:
        return False, checkedNodes

    incoming_nodes = graph.predecessors(course)
    available = True
    for node in incoming_nodes:
        if graph.nodes[node].get("type") == "course" or graph.nodes[node].get("type") == "prerequisite":

            if (graph[node][course].get("weight") == 1 or graph[node][course].get("weight") == 3) and graph.nodes[node].get("active") == False:
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

def getConsecutiveSwap(graph, start, target, semester_plan, max_semester_ECTS, courses_ECTS, cycle, courses):
    swap_possibilities = []
    valid_check_semester = copy.deepcopy(semester_plan[start])
    for course in courses:
        valid_check_semester[0].remove(course)

    if semester_plan[target][1] + int(courses_ECTS) <= max_semester_ECTS:
        swap_possibilities = "direct"
    else:
        needed_ECTS = abs(max_semester_ECTS - semester_plan[target][1] - int(courses_ECTS))
        swap_ECTS = 0
        course_amount = 1
        swap_course_pool = copy.deepcopy(semester_plan[target][0])
        if swap_course_pool:
            while swap_ECTS < needed_ECTS and swap_course_pool:
                min_ECTS_course = min(swap_course_pool, key=lambda tmp: int(graph.nodes[tmp].get("ECTS")))
                swap_ECTS += int(graph.nodes[min_ECTS_course].get("ECTS"))
                swap_course_pool.remove(min_ECTS_course)
                course_amount += 1
            if swap_ECTS >= needed_ECTS:
                for k in range(1, course_amount):
                    for possible_swap_comb in combinations(semester_plan[target][0], k):
                        if getSemesterValidPartial(graph, valid_check_semester, possible_swap_comb, cycle):
                            lost_ECTS = sum(int(graph.nodes[swap_course].get("ECTS")) for swap_course in possible_swap_comb)
                            if semester_plan[target][1] - lost_ECTS + int(courses_ECTS) <= max_semester_ECTS and \
                                semester_plan[start][1] - int(courses_ECTS) + lost_ECTS <= max_semester_ECTS:
                                swap_possibilities.append(possible_swap_comb)
    return swap_possibilities

def getSwapPossibilities(graph, start, semester_plan, max_semester_ECTS, course_ECTS,
                         step_size, start_cycle, courses):
    swap_possibilities = []
    valid_check_semester = copy.deepcopy(semester_plan[start])
    for course in courses:
        valid_check_semester[0].remove(course)

    #get predecessors / sucessors of courses
    for course in courses:
        courses_successors = [edge[1] for edge in graph.out_edges(course) if
                  graph.edges[edge].get("weight") == 3]
        courses_predecessors = [edge[0] for edge in graph.in_edges(course) if
                                graph.edges[edge].get("weight") == 3]
    if courses_predecessors:
        courses_predecessors_ECTS = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in courses_predecessors)
    if courses_successors:
        return []

    last_swap_semester = (len(semester_plan)) - 1 if courses_successors else len(semester_plan)

    for j in range(start + step_size, last_swap_semester, step_size):
        if semester_plan[j][1] + int(course_ECTS) <= max_semester_ECTS:
            if courses_predecessors:
                predecessor_cycle = "FWS" if start_cycle == "SSS" else "SSS"
                courses_predecessors_swap = getConsecutiveSwap(graph, start - 1, j - 1,
                                                               semester_plan, max_semester_ECTS,
                                                               courses_predecessors_ECTS,
                                                               predecessor_cycle,
                                                               courses_predecessors)
                if courses_predecessors_swap == "direct":
                    swap_possibilities.append([j, None, courses_predecessors, [], [], [], [], []])
                else:
                    for swap in courses_predecessors_swap:
                        swap_possibilities.append([j, None, courses_predecessors, swap, [], [], [], []])
            else:
                swap_possibilities.append([j, None, [], [], [], [], [], []])

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
            if swap_ECTS >= needed_ECTS and course_amount > 0:
                for k in range(course_amount, len(semester_plan[j][0]) + 1):
                    for possible_swap_comb in combinations(semester_plan[j][0], k):

                        lost_ECTS = sum(
                            int(graph.nodes[swap_course].get("ECTS")) for swap_course in possible_swap_comb)
                        if semester_plan[j][1] - lost_ECTS + int(course_ECTS) <= max_semester_ECTS and \
                                semester_plan[start][1] - int(course_ECTS) + lost_ECTS <= max_semester_ECTS:

                            if courses_predecessors:
                                predecessor_cycle = "FWS" if start_cycle == "SSS" else "SSS"
                                semester_plan_without_courses = copy.deepcopy(semester_plan)
                                semester_plan_without_courses[start][0] = [tmp for tmp in semester_plan_without_courses[start][0] if tmp not in courses]
                                courses_predecessors_swap = getConsecutiveSwap(graph, start - 1, j - 1,
                                                                               semester_plan_without_courses, max_semester_ECTS,
                                                                               courses_predecessors_ECTS,
                                                                               predecessor_cycle,
                                                                               courses_predecessors)
                                for swap in courses_predecessors_swap:
                                    swap_possibilities.append([j, possible_swap_comb, courses_predecessors, swap, [], [], [], []])

                            else:

                                # get predecessors / succsessors of swap courses
                                for course in possible_swap_comb:
                                    swap_successors = [edge[1] for edge in graph.out_edges(course) if
                                                       graph.edges[edge].get("weight") == 3]
                                    swap_successors_ECTS = sum(
                                        int(graph.nodes[tmp].get("ECTS")) for tmp in swap_successors)
                                    swap_predecessors = [edge[0] for edge in graph.in_edges(course) if
                                                         graph.edges[edge].get("weight") == 3]
                                    swap_predecessors_ECTS = sum(
                                        int(graph.nodes[tmp].get("ECTS")) for tmp in swap_predecessors)

                                if not swap_predecessors or start > 0:

                                    # get cycle of semester where consecutive swap must be done
                                    if j - start % 2 == 0:
                                        consecutive_cycle = "FWS" if start_cycle == "SSS" else "SSS"
                                    else:
                                        consecutive_cycle = "FWS" if start_cycle == "FWS" else "SSS"

                                    if swap_predecessors:
                                        swap_predecessors_swap = getConsecutiveSwap(graph, j - 1, start - 1,
                                                                                       semester_plan, max_semester_ECTS,
                                                                                       swap_predecessors_ECTS,
                                                                                       consecutive_cycle,
                                                                                       swap_predecessors)

                                        if swap_predecessors_swap == "direct":
                                            swap_possibilities.append(
                                                [j, possible_swap_comb, [], [], swap_predecessors, [], [], []])
                                        else:
                                            for swap in swap_predecessors_swap:
                                                swap_possibilities.append([j, possible_swap_comb, [], [], swap_predecessors, swap, [], []])

                                    elif swap_successors:
                                        swap_successors_swap = getConsecutiveSwap(graph, j + 1, start + 1,
                                                                                    semester_plan,
                                                                                    max_semester_ECTS,
                                                                                    swap_successors_ECTS,
                                                                                    consecutive_cycle,
                                                                                    swap_successors)

                                        if swap_successors_swap == "direct":
                                            swap_possibilities.append(
                                                [j, possible_swap_comb, [], [], [], [], swap_successors, []])
                                        else:
                                            for swap in swap_successors_swap:
                                                swap_possibilities.append([j, possible_swap_comb, [], [], [], [], swap_successors, swap])

                                    else:
                                        swap_possibilities.append(
                                            [j, possible_swap_comb, [], [], [], [], [], []])







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
    successors = []
    while current_ECTS < max_ECTS:
        bestCandidate = getBestSemesterPlan(graph_copy, max_semester_ECTS, max_ECTS, startCycle, courseRewards, successors)
        successors = []

        for course in bestCandidate[0]:
            outgoing = graph_copy.out_edges(course)
            for edge in outgoing:
                if graph_copy.edges[edge].get("weight") == 3:
                    successors.append(edge[1])
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

def optimizeCourseSuggestion(graph, max_semester_ECTS, max_ECTS, course_rewards, semester_plan,
                             start_cycle, max_semester_amount, stop_criterion):

    optimized_plan = copy.deepcopy(semester_plan)

    for loop in range(stop_criterion):
        old_plan_reward = getPlanReward(graph, optimized_plan, start_cycle, course_rewards)
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
                    swap_cycle = start_cycle
                    old_reward = getPlanReward(graph_copy, optimized_plan, swap_cycle, course_rewards)
                    possible_new_plan = copy.deepcopy(optimized_plan)
                    possible_new_plan[i][0] = [course for course in possible_new_plan[i][0] if course not in courses]
                    possible_new_plan[swap_semester][0].extend(courses)
                    if swap_possibility[1] is not None:
                        possible_new_plan[i][0].extend(swap_possibility[1])
                        possible_new_plan[swap_semester][0] = [tmp for tmp in possible_new_plan[swap_semester][0] if tmp not in swap_possibility[1]]
                    if swap_possibility[2]:
                        possible_new_plan[i-1][0] = [tmp for tmp in possible_new_plan[i-1][0] if tmp not in swap_possibility[2]]
                        possible_new_plan[swap_semester-1][0].extend(swap_possibility[2])
                    if swap_possibility[3]:
                        possible_new_plan[swap_semester-1][0] = [tmp for tmp in possible_new_plan[swap_semester-1][0] if tmp not in swap_possibility[3]]
                        possible_new_plan[i-1][0].extend(swap_possibility[3])
                    if swap_possibility[4]:
                        possible_new_plan[swap_semester-1][0] = [tmp for tmp in possible_new_plan[swap_semester-1][0] if tmp not in swap_possibility[4]]
                        possible_new_plan[i-1][0].extend(swap_possibility[4])
                    if swap_possibility[5]:
                        possible_new_plan[i-1][0] = [tmp for tmp in possible_new_plan[i-1][0] if tmp not in swap_possibility[5]]
                        possible_new_plan[swap_semester-1][0].extend(swap_possibility[5])
                    if swap_possibility[6]:
                        possible_new_plan[swap_semester+1][0] = [tmp for tmp in possible_new_plan[swap_semester+1][0] if tmp not in swap_possibility[6]]
                        possible_new_plan[i+1][0].extend(swap_possibility[6])
                    if swap_possibility[7]:
                        possible_new_plan[i+1][0] = [tmp for tmp in possible_new_plan[i+1][0] if tmp not in swap_possibility[7]]
                        possible_new_plan[i+1][0].extend(swap_possibility[7])
                    new_reward = 0
                    successors = []
                    for j in range(0, len(possible_new_plan)):
                        if getSemesterValid(graph_copy_swap, possible_new_plan[j][0], swap_cycle) and \
                                all(course in possible_new_plan[j][0] for course in successors):
                            skill_level_swap = getSkillLevelsGraph(graph_copy_swap)
                        else:
                            new_reward = -1
                            break
                        new_reward += calculateRewardFunctionWithPenalty(possible_new_plan[j][0], course_rewards,
                                                                         skill_level_swap)
                        takeCourses(graph_copy_swap, possible_new_plan[j][0], swap_cycle)
                        swap_cycle = "FWS" if swap_cycle == "SSS" else "SSS"
                        successors = []
                        for course in possible_new_plan[j][0]:
                            outgoing = graph_copy.out_edges(course)
                            for edge in outgoing:
                                if graph_copy.edges[edge].get("weight") == 3:
                                    successors.append(edge[1])

                    if new_reward - old_reward > best_swap_reward:
                        best_swap = swap_possibility
                        best_swap_reward = new_reward - old_reward
                if best_swap_reward > 0:
                    optimized_plan[i][0] = [course for course in optimized_plan[i][0] if course not in courses]
                    optimized_plan[best_swap[0]][0].extend(courses)
                    swap_semester = best_swap[0]
                    if best_swap[1] is not None:
                        optimized_plan[i][0].extend(best_swap[1])
                        optimized_plan[swap_semester][0] = [tmp for tmp in optimized_plan[swap_semester][0] if
                                                               tmp not in best_swap[1]]
                    if best_swap[2]:
                        optimized_plan[i - 1][0] = [tmp for tmp in optimized_plan[i - 1][0] if tmp not in best_swap[2]]
                        optimized_plan[swap_semester - 1][0].extend(best_swap[2])
                    if best_swap[3]:
                        optimized_plan[swap_semester - 1][0] = [tmp for tmp in optimized_plan[swap_semester - 1][0] if
                                                                   tmp not in best_swap[3]]
                        optimized_plan[i - 1][0].extend(best_swap[3])
                    if best_swap[4]:
                        optimized_plan[swap_semester - 1][0] = [tmp for tmp in optimized_plan[swap_semester - 1][0] if
                                                                   tmp not in best_swap[4]]
                        optimized_plan[i - 1][0].extend(best_swap[4])
                    if best_swap[5]:
                        optimized_plan[i - 1][0] = [tmp for tmp in optimized_plan[i - 1][0] if tmp not in best_swap[5]]
                        optimized_plan[swap_semester - 1][0].extend(best_swap[5])
                    if best_swap[6]:
                        optimized_plan[swap_semester + 1][0] = [tmp for tmp in optimized_plan[swap_semester + 1][0] if
                                                                   tmp not in best_swap[6]]
                        optimized_plan[i + 1][0].extend(best_swap[6])
                    if best_swap[7]:
                        optimized_plan[i + 1][0] = [tmp for tmp in optimized_plan[i + 1][0] if tmp not in best_swap[7]]
                        optimized_plan[i + 1][0].extend(best_swap[7])
                    optimized_plan[i][1] = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in optimized_plan[i][0])
                    optimized_plan[best_swap[0]][1] = sum(int(graph.nodes[tmp].get("ECTS")) for tmp in optimized_plan[best_swap[0]][0])

            takeCourses(graph_copy, optimized_plan[i][0], cycle)
            cycle = "FWS" if cycle == "SSS" else "SSS"


    return(optimized_plan)

def twoStepAlgo(graph, max_semester_ECTS, max_ECTS, weights, startCycle, max_semester_amount, stop_criterion):
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

    final_suggestion = optimizeCourseSuggestion(graph, max_semester_ECTS, max_ECTS, courseRewards, greedy_suggestion[0],
                             start_cycle_working_copy, max_semester_amount, stop_criterion)

    return greedy_suggestion, final_suggestion

def getPlanReward(graph, plan, start_cycle, course_rewards):
    reward = 0
    graph_copy = graph.copy()
    cycle = start_cycle
    for i in range(len(plan)):
        skill_level = getSkillLevelsGraph(graph_copy)
        reward += calculateRewardFunctionWithPenalty(plan[i][0], course_rewards, skill_level)
        takeCourses(graph_copy, plan[i][0], cycle)
        cycle = "FWS" if cycle == "SSS" else "SSS"

    return reward

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

            print(course + ": " + str(required_skill) + ", " + str(actual_skill) + ", " + str(course_rewards[course]))
        takeCourses(graph_copy, semester[0], cycle)
        cycle = "FWS" if cycle == "SSS" else "SSS"


G = nx.read_graphml("CourseSkillGraph_Master.graphml")
startzeit = time.time()

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

greedy, final = twoStepAlgo(G, 34, 120, weights, "FWS", 6, 10)
#print(greedy)
initialize(G)
course_rewards = getCourseRewards(G, weights)
#greedy=([[["CS 550 Algorithmics"], 6], [["TP 500 Team Project Split 1"], 6 ], [["TP 500 Team Project Split 2"], 6], [["IE 500 Data Mining I"], 6]], 24)
#final = optimizeCourseSuggestion(G, 6, 24, course_rewards, greedy[0], "FWS", 6, 10)
#final=[[['IE 500 Data Mining I'], 6], [['CS 550 Algorithmics'], 6], [['TP 500 Team Project Split 1'], 6], [['TP 500 Team Project Split 2'], 6]]
print(greedy)
print(final)
course_rewards = getCourseRewards(G, weights)
print("Reward greedy: " + str(getPlanReward(G, greedy[0], "FWS", course_rewards)))
print("Reward final: " + str(getPlanReward(G, final, "FWS", course_rewards)))
printSkillDiff(G,final,"FWS",course_rewards)
#print(getCourseRewards(G,))
#print(getAvailailableCourses(G, 180, "FWS", 0))
endzeit = time.time()
ausfuehrungszeit = endzeit - startzeit
print(f"Die Methode hat {ausfuehrungszeit:.5f} Sekunden benötigt.")












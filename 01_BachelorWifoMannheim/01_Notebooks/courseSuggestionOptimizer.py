from scipy.optimize import minimize
import networkx as nx
import courseSuggestion as cs

def objective(vars, courses, graph, course_rewards, start_cycle):
    semester_amount = max(vars)
    reward = 0
    graph_copy = graph.copy()

    for i in range(0, semester_amount + 1):
        semester_courses_indices = [index for index, element in enumerate(vars) if element == i]
        semester_courses = [courses[index] for index in semester_courses_indices]

        skill_level_graph = cs.getSkillLevelsGraph(graph_copy)

        reward += cs.calculateRewardFunctionWithPenalty(semester_courses, course_rewards, skill_level_graph)

        cs.takeCourses(graph_copy, semester_courses, start_cycle)

    return -reward

def contraint_semesterAmount(vars, semester_amount):
    return max(vars) < semester_amount

def constraint_semesterECTS(vars, ECTS_min, ECTS_max)




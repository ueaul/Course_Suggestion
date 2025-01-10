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
        start_cycle = "FWS" if start_cycle == "SSS" else "SSS"

    return -reward

#def contraint_semesterAmount(vars, semester_amount):
#    return 0 <= min(vars) and max(vars) < semester_amount

def constraint_semesterECTS(vars, courses, graph, min_semester_ECTS, max_semester_ECTS):
    semester_amount = max(vars)

    for i in range(0, semester_amount + 1):
        semester_courses_indices = [index for index, element in enumerate(vars) if element == i]
        semester_courses = [courses[index] for index in semester_courses_indices]
        courses_ECTS = [graph.nodes[course].get("ECTS") for course in semester_courses]
        semester_ECTS = sum(courses_ECTS)
        if not min_semester_ECTS <= semester_ECTS <= max_semester_ECTS:
            return -1

    return 1

def constraint_valid(vars, courses, graph, start_cycle):
    semester_amount = max(vars)
    graph_copy = graph.copy()

    for i in range(0, semester_amount + 1):
        semester_courses_indices = [index for index, element in enumerate(vars) if element == i]
        semester_courses = [courses[index] for index in semester_courses_indices]
        for course in semester_courses:
            available, parallelCourses = cs.getCourseAvailability(graph_copy, course, [course], start_cycle)
            if not available:
                return -1
            elif len(parallelCourses) > 1:
                for parallelCourse in parallelCourses:
                    if not parallelCourse in semester_courses:
                        return -1

        cs.takeCourses(graph_copy, semester_courses, start_cycle)
        start_cycle = "FWS" if start_cycle == "SSS" else "SSS"

    return 1




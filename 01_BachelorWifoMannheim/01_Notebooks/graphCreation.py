import re

import pandas as pd

def getCourseName(course):
    course_name = ""

    if not ("Modul" in str(course.iloc[0, 0]) or "Schlüsselqualifikation" in str(course.iloc[0, 0])):
        course_name += str(course.iloc[0, 0])

    if not pd.isna(course.iloc[0, 1]) and not course.iloc[0, 1] == "":
        if len(course_name) > 0:
            course_name += " " + str(course.iloc[0, 1])
        else:
            course_name += str(course.iloc[0, 1])

    return course_name

def mapGraphToDB_courseName(course):
    course_name = getCourseName(course)
    if course_name == "CS 605 GPU-Programmierung GPU Programming":
        return "CS 410 GPU-Programmierung"
    elif course_name == "SM 442 Bachelorseminar Prof. Stuckenschmidt Seminar":
        return "SM 442 Seminar"
    elif course_name == "SM 443 Bachelorseminar Prof. Ponzetto Seminar":
        return "SM 443 Seminar"
    elif course_name == "SM 444 Bachelorseminar Prof. Bizer Seminar":
        return "SM 444 Seminar"
    elif course_name == "SM 445 Bachelorseminar Prof. Gemulla Seminar":
        return "SM 445 Seminar"
    elif course_name == "SM 446 Bachelorseminar Prof. Moerkotte":
        return "SM 446 Seminar"
    elif course_name == "SM 448 Bachelorseminar Prof. Krause Seminar":
        return "SM 448 Seminar"
    elif course_name == "SM 449 Bachelorseminar Prof. Atkinson Seminar":
        return "SM 449 Seminar"
    elif course_name == "SM 450 Bachelorseminar Prof. Armknecht Seminar":
        return "SM 450 Seminar"
    elif course_name == "SM 452 Bachelorseminar Prof. Heinzl Seminar":
        return "SM 452 Seminar"
    elif course_name == "SM 453 Bachelorseminar Prof. Becker Seminar":
        return "SM 453 Seminar"
    elif course_name == "SM 454 Bachelorseminar Dr. Rost Seminar":
        return "SM 454 Seminar"
    elif course_name == "SM 456 Bachelorseminar Dr. Bartelt Seminar":
        return "SM 456 Seminar"
    else:
        return course_name


def getCourseNodes(courses):
    nodes = []

    for course in courses:

        #Get name of course
        course_name = getCourseName(course)

        #Get ECTS
        ECTS_row = course[course.iloc[:, 0] == "ECTS"]
        ECTS = ECTS_row.iloc[0,1]

        #Get offering cycle
        offering_cycle_row = course[course.iloc[:, 0] == "Angebotsturnus"]
        offering_cycle = offering_cycle_row.iloc[0,1]

        nodes.append([course_name, ECTS, offering_cycle])

    return nodes

def getFullCourseName(searchString, CourseNames):
    for courseName in CourseNames:
        if searchString in courseName:
            return courseName

    return ""

def getMatchingCourses(searchString, courseNames, mainCourse):
    matchingCourses = []
    for courseName in courseNames:
        if searchString in courseName and not mainCourse in courseName:
            matchingCourses.append(courseName)

    return matchingCourses


def complete_edges(courses, edges):
    additional_edges = []

    prerequisite_index = 0

    helper_nodes = []

    course_names = []
    for course in courses:
        course_names.append(getCourseName(course))

    knowledge_areas = pd.read_excel("../04_Graph/knowledgeAreas.xlsx").values.tolist()

    for course in courses:

        # Get name of course
        course_name = getCourseName(course)

        # Get row where courses containing required knowledge are contained
        row = course[course.iloc[:, 0] == "Vorausgesetzte Kenntnisse"]
        if row.empty:
            row = course[course.iloc[:, 0] == "Voraussetzungen"]
        if row.empty:
            row = course[course.iloc[:, 0] == "Prerequisites"]

        # Get name of courses with required knowledge
        if not row.empty:
            if pd.notna(row.iloc[0, 1]) and not str(row.iloc[0, 1]) == "" and not str(row.iloc[0, 1]) == "-":
                required_course_knowledge_raw = row.iloc[0, 1]
                required_course_knowledge = [course.strip() for course in required_course_knowledge_raw.split(",")]

                # Create new edges
                for course_knowledge in required_course_knowledge:
                    # Skill is directly contained
                    if [course_knowledge] in knowledge_areas:
                        if not [course_knowledge, course_name] in additional_edges:
                            additional_edges.append([course_knowledge, course_name])
                    # Course is contained, add all skills associated with that course
                    else:
                        knowledge_course_names = getMatchingCourses(course_knowledge, course_names, course_name)
                        for knowledge_course_name in knowledge_course_names:
                            escaped_course_knowledge = re.escape(knowledge_course_name)
                            indices = edges[
                                edges['Outgoing'].str.contains(escaped_course_knowledge, na=False)].index.tolist()
                            for idx in indices:
                                knowledge = edges.iloc[idx, 1]
                                if not [knowledge, course_name] in additional_edges:
                                    additional_edges.append([knowledge, course_name])

        # Get rows where prerequisite courses are contained
        row = course[course.iloc[:, 0] == "Benötigte Kurse"]

        if not row.empty:
            if pd.notna(row.iloc[0, 1]):
                prerequisite_courses_raw = row.iloc[0, 1]
                prerequisite_courses = [course.strip() for course in prerequisite_courses_raw.split(",")]

                for prerequisite_course in prerequisite_courses:
                    if "|" in prerequisite_course:
                        gate_created = False
                        equivalent_courses = [course.strip() for course in prerequisite_course.split("|")]
                        for equivalent_course in equivalent_courses:
                            if not equivalent_course == "":
                                matching_courses = getMatchingCourses(equivalent_course, course_names, course_name)
                                for matching_course in matching_courses:
                                    if not gate_created:
                                        helper_nodes.append(
                                            ["MIN " + str(prerequisite_index), "white", "prerequisite", "MIN", 1])
                                        additional_edges.append(["MIN " + str(prerequisite_index), course_name, 1])
                                        gate_created = True
                                    additional_edges.append([matching_course, "MIN " + str(prerequisite_index), 1])
                        if gate_created:
                            prerequisite_index += 1
                    else:
                        prerequisite_course_names = getMatchingCourses(prerequisite_course, course_names, course_name)
                        for prerequisite_course_name in prerequisite_course_names:
                            additional_edges.append([prerequisite_course_name, course_name, 1])

        # Get rows where courses are contained that result into not beeing able to taking this course
        row = course[course.iloc[:, 0] == "Not Taken"]
        if not row.empty:
            if pd.notna(row.iloc[0, 1]):
                exclusive_courses_raw = row.iloc[0, 1]
                exclusive_courses = [course.strip() for course in exclusive_courses_raw.split(",")]

                for exclusive_course in exclusive_courses:
                    exclusive_course_names = getMatchingCourses(exclusive_course, course_names, course_name)
                    for exclusive_course_name in exclusive_course_names:
                        additional_edges.append([exclusive_course_name, course_name, -1])

    return additional_edges, helper_nodes
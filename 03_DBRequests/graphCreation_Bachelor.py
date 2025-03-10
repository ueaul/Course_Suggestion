import pandas as pd
import re
import networkx as nx
import sqlite3

#Construct the course name based on the first row of the DataFrame representing the course
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

#Mapping from the course names in the graph to the course names in the database
def mapGraphToDB_courseName(course_name):
    if isinstance(course_name, pd.DataFrame):
        course_name = getCourseName(course_name)

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

#Mapping from the course names in the database to the course names in the graph
def mapDBtoGraph_courseName(course_name):
    if isinstance(course_name, pd.DataFrame):
        course_name = getCourseName(course_name)

    if course_name == "CS 410 GPU-Programmierung":
        return "CS 605 GPU-Programmierung GPU Programming"
    elif course_name == "SM 442 Seminar":
        return "SM 442 Bachelorseminar Prof. Stuckenschmidt Seminar"
    elif course_name == "SM 443 Seminar":
        return "SM 443 Bachelorseminar Prof. Ponzetto Seminar"
    elif course_name == "SM 444 Seminar":
        return "SM 444 Bachelorseminar Prof. Bizer Seminar"
    elif course_name == "SM 445 Seminar":
        return "SM 445 Bachelorseminar Prof. Gemulla Seminar"
    elif course_name == "SM 446 Seminar":
        return "SM 446 Bachelorseminar Prof. Moerkotte"
    elif course_name == "SM 448 Seminar":
        return "SM 448 Bachelorseminar Prof. Krause Seminar"
    elif course_name == "SM 449 Seminar":
        return "SM 449 Bachelorseminar Prof. Atkinson Seminar"
    elif course_name == "SM 450 Seminar":
        return "SM 450 Bachelorseminar Prof. Armknecht Seminar"
    elif course_name == "SM 452 Seminar":
        return "SM 452 Bachelorseminar Prof. Heinzl Seminar"
    elif course_name == "SM 453 Seminar":
        return "SM 453 Bachelorseminar Prof. Becker Seminar"
    elif course_name == "SM 454 Seminar":
        return "SM 454 Bachelorseminar Dr. Rost Seminar"
    elif course_name == "SM 456 Seminar":
        return "SM 456 Bachelorseminar Dr. Bartelt Seminar"
    else:
        return course_name

#Reconstructs the full course name by matching a search string to a list of course names
def getFullCourseName(searchString, CourseNames):
    for courseName in CourseNames:
        if searchString in courseName:
            return courseName

    return ""

#Extracts the course names that match the search string and not match the main course
def getMatchingCourses(searchString, courseNames, mainCourse):
    matchingCourses = []
    for courseName in courseNames:
        if searchString in courseName and not mainCourse in courseName:
            matchingCourses.append(courseName)

    return matchingCourses

#Extract the information for the construction of the course nodes from the DataFrames representing the courses
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

#Create all edges representing prerequiste relationships as well as the skill -> course edges
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
                                            ["MIN " + str(prerequisite_index), "yellow", "prerequisite", "MIN", 1])
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

#Extract all edges where the connected nodes have a certain value for one of their attributes
def getFilteredEdges(graph, outgoing_node_attribute, ingoing_node_attribute, outgoing_node_value, ingoing_node_value):
    filteredEdges = []

    for u, v in graph.edges():
        if (graph.nodes[u].get(outgoing_node_attribute) == outgoing_node_value and
                graph.nodes[v].get(ingoing_node_attribute) == ingoing_node_value):
            filteredEdges.append((u,v))

    return filteredEdges

#Script for weighting the course -> skill edges
def getCourseSkillWeights(graph, database, min):
    course_skill_edge_weights = []

    #Get edges relevant for the script (course -> skill and skill -> course edges)
    course_skill_edges = getFilteredEdges(graph, "type", "type", "course", "skill")
    skill_course_edges = getFilteredEdges(graph, "type", "type", "skill", "course")

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    #Create edge weight for all course -> skill edges
    for edge in course_skill_edges:
        course_providing_skill = edge[0]
        course_providing_skill_mapped = mapGraphToDB_courseName(course_providing_skill)
        skill = edge[1]

        #Get all courses that have an ingoing edge that is outgoing from the considered skill
        courses_requiring_skill = [tmp_edge[1] for tmp_edge in skill_course_edges if tmp_edge[0] == skill]

        if course_providing_skill in courses_requiring_skill:
            courses_requiring_skill.remove(course_providing_skill)

        average_grades_with_course = []
        average_grades_without_course = []

        #Compute average grades for students that passed the courses
        for course_requiring_skill in courses_requiring_skill:
            course_requiring_skill_mapped = mapGraphToDB_courseName(course_requiring_skill)

            #Get the average grade achieved in the course when students completed the considered course prior
            query = """SELECT AVG(note), COUNT(note) 
                       FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                       WHERE ? LIKE p.bezeichnung || '%' AND s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Bachelor' 
                       AND p.status IN ("BE", "NB") AND s.status IN ("BE", "R", "NB", "N")
                       AND EXISTS(
                           SELECT *
                           FROM pruefungsleistung p2 JOIN studium s2 ON p2.studium_id = s2.studium_id
                           WHERE ? LIKE p2.bezeichnung || '%' AND p2.semester < p.semester AND p2.status = "BE" AND p2.studium_id = p.studium_id
                        )
                        """
            cursor.execute(query, (course_requiring_skill_mapped, course_providing_skill_mapped,))
            results_with_course = cursor.fetchall()

            # Get the average grade achieved in the course when students didn't complete the considered course prior
            query = """SELECT AVG(note), COUNT(note) 
                        FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                        WHERE ? LIKE p.bezeichnung || '%' AND s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Bachelor'
                        AND p.status IN ("BE", "NB") AND s.status IN ("BE", "R", "NB", "N")
                        AND NOT EXISTS(
                           SELECT *
                           FROM pruefungsleistung p2 JOIN studium s2 ON p2.studium_id = s2.studium_id
                           WHERE ? LIKE p2.bezeichnung || '%' AND p2.semester < p.semester AND p2.status = "BE" AND p2.studium_id = p.studium_id
                        )
                        """
            cursor.execute(query, (course_requiring_skill_mapped, course_providing_skill_mapped,))
            results_without_course = cursor.fetchall()

            #Collect the results if exist
            if results_with_course and results_with_course[0][1] > 0:
                average_grades_with_course.append([results_with_course[0][0], results_with_course[0][1]])
            if results_without_course and results_without_course[0][1] > 0:
                average_grades_without_course.append([results_without_course[0][0], results_without_course[0][1]])

        grades_with_course = 0
        grades_without_course = 0
        count_with_course = 0
        count_without_course = 0

        #summarize average grades
        for grades in average_grades_with_course:
            grades_with_course += grades[0] * grades[1]
            count_with_course += grades[1]
        for grades in average_grades_without_course:
            grades_without_course += grades[0] * grades[1]
            count_without_course += grades[1]

        #calculate edge weight
        if count_with_course > 0 and count_without_course > 0:
            edge_weight = grades_without_course / count_without_course - grades_with_course / count_with_course
        else:
            edge_weight = min

        #Set age weight to min if result is too small or not representative
        if edge_weight < min:
            edge_weight = min

        course_skill_edge_weights.append([edge_weight, course_providing_skill, skill, count_with_course, count_without_course])

    conn.close()

    return course_skill_edge_weights

#Script for weighting the skill -> course edges
def getSkillCourseWeights(graph, database):
    course_names_graph = list(graph.nodes())

    skill_course_edge_weights = []

    edges_to_check = []

    skill_course_edges = getFilteredEdges(graph, "type", "type", "skill", "course")

    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    for edge in skill_course_edges:
        skill = edge[0]
        course_requiring_skill = edge[1]
        course_requiring_skill_mapped = mapGraphToDB_courseName(course_requiring_skill)

        query = """SELECT DISTINCT p.studium_id, p.semester
                   FROM pruefungsleistung p JOIN studium s ON p.studium_id = s.studium_id
                   WHERE s.studium_bezeichnung = 'Wirtschaftsinformatik' AND s.studium_art = 'Bachelor' AND 
                   p.status = "BE" AND ? LIKE p.bezeichnung || '%' AND s.status IN ("BE", "R", "NB", "N")
                    """
        cursor.execute(query, (course_requiring_skill_mapped,))
        students_passed_course = cursor.fetchall()

        skill_levels_for_passing = []
        if students_passed_course:
            for student in students_passed_course:
                study_id = student[0]
                semester = student[1]

                query = """SELECT DISTINCT bezeichnung
                           FROM pruefungsleistung
                           WHERE studium_id = ? AND semester < ? AND status = "BE"
                            """
                cursor.execute(query, (study_id, semester,))
                prior_passed_courses = cursor.fetchall()

                skill_level = 0
                if prior_passed_courses:
                    for course in prior_passed_courses:
                        course_name = mapDBtoGraph_courseName(course[0])
                        course_name_full = getFullCourseName(course_name, course_names_graph)
                        if graph.has_edge(course_name_full, skill):
                            skill_level += graph[course_name_full][skill].get("weight")
                        else:
                            edges_to_check.append([course_name, course_name_full, skill])

                skill_levels_for_passing.append(skill_level)

        if skill_levels_for_passing:
            average_skill_level_for_passing = sum(skill_levels_for_passing) / len(skill_levels_for_passing)
        else:
            average_skill_level_for_passing = 0
        skill_course_edge_weights.append([average_skill_level_for_passing, skill, course_requiring_skill,
                                         len(skill_levels_for_passing)])

    return skill_course_edge_weights, edges_to_check

def createPools(graph):
    for node in graph.nodes:
        if graph.nodes[node].get("type") == "course":
            if node.startswith("BA "):
                graph.nodes[node]["pool"] = "Thesis"
            elif node.startswith("SM "):
                graph.nodes[node]["pool"] = "Seminars"
            elif node in ["Konfliktmanagement", "Kommunikation im Team", "Programmierkurs C/C++", "Sprachkurs"]:
                graph.nodes[node]["pool"] = "Key Qualifications Pool"
            elif node in ["Zeitmanagement Time Management",
                          "Präsentationskompetenz und Rhetorik Presentation skills and rhetoric",
                          "Change- und Projektmanagement Projectmanagement"]:
                graph.nodes[node]["pool"] = "Key Qualifications"
            elif node in ["Grundlagen der Volkswirtschaftslehre", "Recht"]:
                graph.nodes[node]["pool"] = "Elective Courses"
            elif node[0:6] in ["IS 405", "CS 405", "CS 406", "CS 408", "CS 605", "CS 414"] or node[0:7] == "MAN 455":
                graph.nodes[node]["pool"] = "Specialization Courses"
            elif node in ["MAT 303 Lineare Algebra I Linear Algebra I",
                          "ANA 301 Analysis für Wirtschaftsinformatiker Analysis for Business Informatics",
                          "Grundlagen der Statistik Foundations of Statistics"]:
                graph.nodes[node]["pool"] = "Fundamentals Mathematics and Statistics"
            elif node in ["Marketing", "Produktion", "Internes Rechnungswesen",
                          "Grundlagen des externen Rechnungswesens", "Finanzwirtschaft", "Management"]:
                graph.nodes[node]["pool"] = "Fundamentals Business Administration|Elective Courses|Specialization Courses"
            elif node.startswith("CS "):
                graph.nodes[node]["pool"] = "Fundamentals Computer Science"
            elif node.startswith("IS "):
                graph.nodes[node]["pool"] = "Fundamentals Information Systems"
    return graph

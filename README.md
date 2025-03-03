This repository contains the code created for the Master's Thesis "Extracting Causal Models from Module Handbooks and Study Progress Data for Explainable and Individual Course Suggestions"

Please not that the version 0.11.0 of the Camelot library we used, requires the installation of Ghostscript: https://www.ghostscript.com/

The repository contains the following folders:

-01_BachelorWifoMannheim
This folder contains all code created for the implementation of our approach and the experiments on the Bachelor's Program in Business Informatics at the University of Mannheim

	-01_Notebooks
	Contains the code and all figures created by the code

	-02_Ressources
	Contains the module catalogs and course names of the databse

	-03_Courses
	Contains the final DataFrames for all relevant courses saved as csv files

	-04_Graph
	Contains all files relevant for the creation of the graph as well as the final graphml file

-02_MasterWifoMannheim
This folder contains all code created for the implementation of our approach and the experiments on the Master's Program in Business Informatics at the University of Mannheim

	-01_Notebooks
	Contains the code and all figures created by the code

	-02_Ressources
	Contains the module catalogs and course names of the databse

	-03_Courses
	Contains the final DataFrames for all relevant courses saved as csv files

	-04_Graph
	Contains all files relevant for the creation of the graph as well as the final graphml file

-03_DBRequests
This folder contains a txt file with all SQL queries that have been executed against the database as well all code used for the weighting of the edges between course and skill nodes
The corresponding code and graph files are copies of the code and graph files that are stored in the folders 01_BachelorWifoMannheim and 02_MasterWifoMannheim
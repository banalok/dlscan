DL-SCAN is a user-friendy Streamlit tool that automatically segments cells from fluorescence microscopy TIFF stack using a Deep Learning algorithm called Stardist (Ref: https://arxiv.org/abs/1806.03535),  and provides various user-adjustable options to analyze them. 

Launching the Application:

Note: DL-SCAN is also available online on Hugging Face Spaces. This web application can be accessed from: https://huggingface.co/spaces/dlscan/dlscan. 

For larger files, faster performance, and customization, running DL-SCAN locally is recommended. Using the Anaconda distribution is recommended for setting up and running the program. 
https://www.anaconda.com/download

1. Clone this Github repository to the local machine.

2. Open the Anaconda Command Prompt and navigate to the cloned repository destination. Create a new Python environment called dlscan, and install all the dependencies specified in the “requirements.txt” file using the following commands

	conda create -n dlscan python==3.8.8

	conda activate dlscan

	pip install -r requirements.txt 

> Please allow some time for the installation process to complete.

3. Once all the dependencies are installed, navigate to the directory where the Application is located (if not already in the directory), and activate the environment (if not already activated), and launch DL-SCAN by entering the following commands

> Option 1 (if the dataset is less than 1 GB)

	streamlit run DL_SCAN.py

> Option 2 (if the dataset is larger than 1 GB)

	streamlit run DL_SCAN.py --server.maxUploadSize 2000

> The application now runs locally in the browser using localhost.
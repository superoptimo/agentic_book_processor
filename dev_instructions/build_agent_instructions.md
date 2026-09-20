
The idea is making an automation script for configuring workspaces for converting books into Obsidian Wikis with a pipeline of AI skills for Claude Code, Open Code etc. This script takes an argument as the name of the target project, and it creates the folder structure and copies the necessary assets (skills, scripts, templates etc) for making the pipeline.

Develop a python script named `build_workspace.py` in this root folder, that perform these operations:

### Input Parameters
This script takes 2 arguments from the terminal. One of them is optional.
- **project_name** : The name of the folder where this script will build the target folder structure and copying the scripts, skills and templates.
- **agentic_platform** (optional): Optional parameter that indicates the kind of AI code assistant that will contain the skills. This is passed with the flag `--platform` followed by the text for `agent_platform`, and the name of the target folder will be called in the script as `agent_platform_folder`. These are the options:
	  - **agents** : This is the default option if no agentic platform is specified. That means that the build will be configured for general agentic systems, and the target folder will be `.agents`, located within the workspace `./build/[project_name]/.agents`. That means that the variable  `agent_platform_folder` is equal to ".agents".
	  - **claude** : This is the build for Claude Code platform, and the target folder will be `.claude`, located within the workspace `./build/[project_name]/.claude`. That means that the variable  `agent_platform_folder` is equal to ".claude".
	  - **opencode** : This is the build for Open Code platform, and the target folder will be `.opencode`, located within the workspace `./build/[project_name]/.opencode`.  That means that the variable  `agent_platform_folder` is equal to ".opencode".
	    
### Automation Steps
1. This script takes an argument from the terminal, which we will call it as `project_name`. The first thing that it will do is creating a folder into the `build`  folder as the input parameter `project_name`, which will result in a created structure like this: `./build/[project_name]`.
2. Within the created folder (`./build/[project_name]`) create the following structure:
```
sources/ -- where the source books will be located
scripts/ -- where the scripts from this respository will be copied
vaults/ -- where the templates will be copied.
```

Additionally, create the **Agentic Patform** subfolder into the target workspace (`./build/[project_name]/[agentic_platform_folder]`), as specified fot the input parameter `agentic_platform`. F.E. the folder name ".claude" is assigned to `agentic_platform_folder` variable, and corresponds to the input parameter value "claude" as the chosen agentic platform.

3. Copy the files from the `./scripts` repo folder into the target workspace `./build/[project_name]/scripts`.
4. Copy the skills artifacts from the folder `./skills_src`(subfolders and subelements) into the target destination, which will use the agentic platform folder value: `.build/[project_name]/[agent_platform_folder]/skills`. 
5. Copy the instructions from the `./templates`folder into the vaults destination `./build/[project_name]/vaults`, and rename them as follows:
	- The file "article-style.template.md" is renamed and copied as `./build/[project_name]/vaults/.article-style.md` .
	- The file "learning-goals.template.md" is renamed and copied as `./build/[project_name]/vaults/.learning-goals.md` .

Additionally, suggest a readme for instructions about how to use the skills in the project, and how to configure a workspace with the build.py script. Read into the folder "skills_src" for obtaining more information about this toolset.

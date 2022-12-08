# GOPS Version 1.0 (General Optimal control Problem Solver)
Copyright © 2022 Intelligent Driving Laboratory (iDLab). All rights reserved

#### Description
Optimal control is an important theoretical framework for sequential decision-making and control of industrial objects, especially for complex and high-dimensional problems with strong nonlinearity, high randomness, and multiple constraints.
Solving the optimal control input is the key to applying this theoretical framework to practical industrial problems.
Taking Model Predictive Control as an example, computation time solving its control input relies on receding horizon optimization, of which the real-time performance greatly restricts the application and promotion of this method.
In order to solve this problem, iDLab has developed a series of full state space optimal strategy solution algorithms and the set of application toolchain for industrial control based on Reinforcement Learning and Approximate Dynamic Programming theory.
The basic principle of this method takes an approximation function (such as neural network) as the policy carrier, and improves the online real-time performance of optimal control by offline solving and online application.
The GOPS toolchain will cover the following main links in the whole industrial control process, including control problem modeling, policy network training, offline simulation verification, controller code deployment, etc.

#### Configuration
1. Windows 7 or greater.
2. Python 3.6 or greater (GOPS V1.0 precompiled Simulink models use Python3.6).
3. Matlab/Simulink 2018a or greater (optional).

#### Installation
1. Download gops-dev.zip from gitee repository.
2. Open Command Line or Anaconda Prompt and change to download directory (We recommend to use Anaconda and create a dedicated virtual environment, see https://blog.csdn.net/sizhi_xht/article/details/80964099).
3. Run `<pip install gops-dev.zip>`.

#### Contribution
If you find any bugs or have questions when using GOPS, please go to the Issue section of the gitee repository to discuss.

Developers of GOPS should comply with the following version management process:

1. Fork the code from the main repository tsinghua-iDLab/gops to YOUR_NAME/gops.
2. Create a new branch from the dev branch and develop.
3. Submit the code after passing the test yourself, and push it to your remote repository YOUR_NAME/gops.
4. Propose a pull request to the main repository tsinghua-iDLab/gops in gitee.
5. The repository manager will merge your pull request after check and test.
6. Before submitting code, carefully review each staged file to make sure it only contains what you want to submit. Be careful not to submit test code to git, and do not submit non-source code (such as run results, pyc files, etc.) to git.

In addition, in order to simplify the file size and avoid the GOPS file being too complex, developers are requested to submit only pyd files generated by Matlab/Simulink code instead of source files, including Matlab's slx files and generated C/C++ code, etc.
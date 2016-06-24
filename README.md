# trade-analysis
A simple python framework to analyze trade execution

## Installation
1. Make sure you have a github account. If not make one [here](https://github.com/join)  
2. Fork the repo. 
3. Clone it into you repository:  
	git clone git@github.com:USERNAME/trade-analysis.git  
4. Make sure pip is installed. Check if is installed by *pip -V* on linux systems. If not do the following:  
	sudo apt-get update  
	sudo apt-get upgrade  
	sudo apt-get install python-pip  
5. We love  using virtualenv. It enables to work on different python projects with differnt versions of libraries. It is not mandatory to install. Install it from [here](https://virtualenv.pypa.io/en/stable/installation/)  
6. Install the project requirements by executing *pip install -r requirements.txt*  
7. You are good to go.! Push changes and create PRs. Have fun!  

## Contribution
We want you to contribute and make this project richer. After you have successfully installed the requirements and are ready to code, glance through the [contribution guidelines](https://github.com/trade-analysis/blob/master/CONTRIBUTING.md) to get the formatting and code structure related things which this project adheres to.

## License
See the [license](https://github.com/cvquant/trade-analysis/blob/master/LICENSE) file.

## Examples
 To run a sample backtest, type the following command
	python execution/simulate_execution.py 20150325 VWO S 12 MeanRev 173500



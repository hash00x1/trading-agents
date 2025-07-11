
#### First: 
- define market baseline: -> Hold BTC over 7 Days. 
Question is: Does your model perform better or worse than just holding bticoin?
-> in 7 days bitcoin rose by x% my agent portfoilo rose in comparison by x% -> interpret: this is a rise in performance / fall in performance / etc. 

- test performance if all agents are 4.1-nano; if all agents are gpt o4-mini;
-> lower model baseline: no reasoning fast inference
#### Then:
upper model baseline: reasoning with slower inference

#### Baseline ot test for improvement: 
- test performance if all agents are 4.1 nano and portfolio manager is o4-mini -> setup is: fast inference for research and slow inference for final decision

-> Compare for test run over 7 days for the same set of tokens. 
-> Use google colab and set the script to trade every four hours

-> try to get free trial real-time api access at santiment.net



-> Thesis Outline: 

Intro 
Literature Review -> Multi-Agents for Trading in Business Applications
Method -> Introduce Trading Architecture and explain components
Experiments -> Run model against above baselines
Results: -> Discuss Model Performance against your own baseline benchmarks -> reason why performance is the way it is 
Discussion_ Contextualize your research in the larger debate around Multi Agents for Financial Application
Conclusion & Outlook

-> set up the automation on n8n.com -> free trial 14 days
-> ask claude to provide the blueprint in .json -> copy paste .json into n8n whiteboard
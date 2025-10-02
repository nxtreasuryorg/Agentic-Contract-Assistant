# COMPREHENSIVE CONTRACT SEMANTIC MANIPULATION EVALUATION - COMPLETED 

#Dataset: pdf to rtf  COMPLETED
#Prompt to make semantic manipulation  COMPLETED  
#change the counterparty etc, let's shift the legal domicile, let's shift the legal blame from main party to counterparty,
# add / delete clauses from the contract and we can evaluate which model does these tasks best.  COMPLETED

#critic pattern  COMPLETED
#Evaluation: time, judge by judge model, max 5 attempts each model  COMPLETED

#output: report + metrics + all details in md  COMPLETED

# UPDATED MODELS (verified working with web search):
model = ["ai21.jamba-1-5-large-v1:0", "ai21.jamba-1-5-mini-v1:0", "amazon.titan-text-premier-v1:0", 
         "amazon.titan-text-express-v1", "mistral.mistral-large-2402-v1:0"]

judge_model = 'us.amazon.nova-pro-v1:0'

# FINAL EVALUATION RESULTS (results/20250917-082006/):
#  ALL 5 MODELS: Perfect scores (1.000/1.000) on first attempt
#  ALL MANIPULATIONS: Counterparty, domicile shift, blame shift, clause add/delete  
# PERFORMANCE RANKING:
#   1. amazon.titan-text-express-v1 (0.75s) - FASTEST
#   2. ai21.jamba-1-5-mini-v1:0 (13.65s)
#   3. ai21.jamba-1-5-large-v1:0 (18.31s) 
#   4. amazon.titan-text-premier-v1:0 (20.02s)
#   5. mistral.mistral-large-2402-v1:0 (20.33s)
# SUCCESS RATE: 100% (5/5 models)
# REPORTS: Both MD and RTF formats generated
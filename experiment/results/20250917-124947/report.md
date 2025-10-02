# Contract Manipulation Evaluation Report
**Generated at:** 2025-09-17 12:53:38

## Summary
| Model | Provider | Status | Attempts | Gen Time (s) | Critic Score | Prog Score | Method |
|-------|----------|--------|----------|--------------|--------------|------------|--------|
| ai21.jamba-1-5-large-v1:0 | bedrock | ✅ Satisfied | 1 | 31.30 | 1.000 | 0.300 | 🤖 Actor-Critic |
| ai21.jamba-1-5-mini-v1:0 | bedrock | ✅ Satisfied | 1 | 45.54 | 1.000 | 0.300 | 🤖 Actor-Critic |
| amazon.titan-text-premier-v1:0 | bedrock | ✅ Satisfied | 1 | 31.98 | 1.000 | 0.823 | 🤖 Actor-Critic |
| amazon.titan-text-express-v1 | bedrock | ❌ Unsatisfied | 5 | 6.54 | 0.000 | 0.300 | 🤖 Actor-Critic |
| mistral.mistral-large-2402-v1:0 | bedrock | ✅ Satisfied | 1 | 35.96 | 1.000 | 0.300 | 🤖 Actor-Critic |

## Detailed Results
### ai21.jamba-1-5-large-v1:0
- **Provider:** bedrock
- **Status:** ✅ Satisfied
- **Attempts:** 1
- **Generation Time:** 31.30s
- **Critic Time:** 10.76s
- **Critic Score:** 1.000
- **Programmatic Score:** 0.300
- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)
- **Artifacts:** `/home/ec2-user/cb/exp/results/20250917-124947/models/ai21.jamba-1-5-large-v1-0`

### ai21.jamba-1-5-mini-v1:0
- **Provider:** bedrock
- **Status:** ✅ Satisfied
- **Attempts:** 1
- **Generation Time:** 45.54s
- **Critic Time:** 10.74s
- **Critic Score:** 1.000
- **Programmatic Score:** 0.300
- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)
- **Artifacts:** `/home/ec2-user/cb/exp/results/20250917-124947/models/ai21.jamba-1-5-mini-v1-0`

### amazon.titan-text-premier-v1:0
- **Provider:** bedrock
- **Status:** ✅ Satisfied
- **Attempts:** 1
- **Generation Time:** 31.98s
- **Critic Time:** 12.54s
- **Critic Score:** 1.000
- **Programmatic Score:** 0.823
- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)
- **Artifacts:** `/home/ec2-user/cb/exp/results/20250917-124947/models/amazon.titan-text-premier-v1-0`

### amazon.titan-text-express-v1
- **Provider:** bedrock
- **Status:** ❌ Unsatisfied
- **Attempts:** 5
- **Generation Time:** 6.54s
- **Critic Time:** 0.00s
- **Critic Score:** 0.000
- **Programmatic Score:** 0.300
- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)
- **Artifacts:** `/home/ec2-user/cb/exp/results/20250917-124947/models/amazon.titan-text-express-v1`
- **Note:** unsatisfied after max attempts; see critic.json and programmatic_verification.json for details

### mistral.mistral-large-2402-v1:0
- **Provider:** bedrock
- **Status:** ✅ Satisfied
- **Attempts:** 1
- **Generation Time:** 35.96s
- **Critic Time:** 9.86s
- **Critic Score:** 1.000
- **Programmatic Score:** 0.300
- **Method:** 🤖 Actor-Critic (LLM Critic + Programmatic Validation)
- **Artifacts:** `/home/ec2-user/cb/exp/results/20250917-124947/models/mistral.mistral-large-2402-v1-0`

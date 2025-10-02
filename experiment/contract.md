Please start evaluating these tools, and see how they can help us: 


TO help us in our pdf troubles:
https://docs.aws.amazon.com/bedrock/latest/userguide/bda-document-splitting.html


We need to develop our semantic manipulation, and try out some models here, big small doesn't matter, we can do distillation afterwards. 
https://aws.amazon.com/bedrock/marketplace/


Let's make a few legit contract samples, 
let's change the counterparty etc, let's shift the legal domicile, let's shift the legal blame from main party to counterparty,  add / delete clauses from the contract and we can evaluate which model does these tasks best. 
https://aws.amazon.com/bedrock/evaluations/



we can generate many correct samples of semantic changes in contract , and fine tune smaller model for speed up responses 
https://aws.amazon.com/bedrock/model-distillation/


Agentic framework in AWS.
https://aws.amazon.com/bedrock/agentcore/

Findings (2025-09-12):
 
 - AWS Bedrock Document Splitting: Enables splitting multi-document PDFs into separate documents during project ingestion. Each segment is processed independently; supports mixed document types. Blueprints and best practices guide layout-specific splitting. Useful for parsing bank statements, W-2s, etc., to improve precision of downstream extraction and RAG workflows.
   Source: https://docs.aws.amazon.com/bedrock/latest/userguide/bda-document-splitting.html
 
 - Bedrock Marketplace: Central directory of 100+ foundation models (general, specialized, domain-specific) accessible via a unified Bedrock API. Models interoperate with Bedrock Agents, Knowledge Bases, and Guardrails. Supports trying, subscribing, and using models within AWS accounts.
   Source: https://aws.amazon.com/bedrock/marketplace/
 
 - Bedrock Evaluations: Built-in evaluation for FMs and RAG workflows with options: LLM-as-a-judge, programmatic metrics, human-based evals, retrieval-only, and retrieve-and-generate assessments. Lets you upload datasets, pick metrics, and compare models to select best fit for your use case.
   Source: https://aws.amazon.com/bedrock/evaluations/
 
 - Model Distillation: Lets you select a high-accuracy teacher model and fine-tune a smaller student model using prompts and generated responses, targeting similar task accuracy with lower latency/cost. Pricing and user guide available; supports production data to tailor the student.
   Source: https://aws.amazon.com/bedrock/model-distillation/   
   
   - AgentCore (Preview): AWS services for building and operating production AI agents across frameworks (CrewAI, LangGraph, LlamaIndex, Strands). Capabilities include secure, serverless deployment; tool wrapping for existing APIs; memory/context management; observability dashboards; multi-language code execution; and a serverless browser runtime.
     Source: https://aws.amazon.com/bedrock/agentcore/
   
   Fit to Goal: LLM-generated legal contracts with correct wording and entities (AWS-only)
   
   - Bedrock Marketplace (fit): Use as the catalog to shortlist candidate foundation models available in AWS. We will not hardcode a model choice; instead, we will evaluate multiple options for legal drafting tone, structure, and controllability.
   - Bedrock Evaluations (fit): Evaluate models on contract-generation tasks using datasets that check clause coverage, legal terminology consistency, governing law phrasing, and entity correctness (parties, addresses, dates, amounts). Combine LLM-as-a-judge with programmatic checks.
   - Model Distillation (fit): After identifying a high-accuracy teacher, distill to a smaller student tailored to our prompts and datasets to reduce latency/cost while maintaining accuracy for legal language and entities.
   - AgentCore (fit): Orchestrate an agentic workflow: retrieve precedent clauses, generate draft, run critic/reflection passes, validate entities, and render final contract. Integrates with Bedrock models and AWS services in a secure, serverless way.
   - Document Splitting (fit): Ingest existing multi-contract PDFs to build clause libraries and labeled datasets. Improves retrieval grounding and provides training/eval material for drafting and entity extraction.
   - Critic/Reflection pattern (fit): Although the referenced Google Doc requires access, we can still implement a generate → critique → revise loop within AgentCore and use Bedrock Evaluations for automated quality gates.
   
   Implementation outline (AWS-native, no hardcoded selections):
   - Data preparation: Use Document Splitting to ingest prior contracts; extract clauses/entities to form a retrieval corpus and labeled eval sets.
   - Model selection: From Marketplace shortlist, use Bedrock Evaluations to compare models on legal drafting and entity accuracy before choosing.
   - Grounded drafting: Use AWS Knowledge Base or similar retrieval to ground model outputs in approved clauses and definitions.
   - Critic loop: Implement an AgentCore flow to generate, critique, and revise until evaluation thresholds are met.
   - Entity validation: Add deterministic checks (formats, cross-field consistency) and an LLM verification pass for parties, dates, jurisdictions, and amounts.
   - Optimization: If performance/cost needs arise, apply Model Distillation with our task prompts and reference outputs.
   
   - Critic/Reflection pattern doc: Access requires permission; content not publicly viewable without sign-in. We can incorporate critic/reflection patterns from open sources or request access.
     Source: https://docs.google.com/document/d/1HXXJOQIMWowtLw4WMiSR360caDAlZPtl5dPPgvq9IT4/edit
   
   We need to try critic pattern in our LLM and also go a bit agentic way : 
  
https://docs.google.com/document/d/1HXXJOQIMWowtLw4WMiSR360caDAlZPtl5dPPgvq9IT4/edit?tab=t.0#heading=h.a7nkedxjnyap

Access status for last URL (checked 2025-09-12): Requires Google sign-in; content not publicly viewable. I could not retrieve the document.
Next steps:
- Request access to the Google Doc, or
- Proceed using public references on Critic/Reflection patterns to implement a generate → critique → revise loop within AgentCore and validate via Bedrock Evaluations.

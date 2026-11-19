# Literature Review: LLM Agent Tool Use, Self-Correction, and Long-Term Memory

**Coverage note:** The search index returned only a small subset of the key papers in this area. Several well-known works did not appear, so this review is thinner than a full survey. Papers I could not verify are listed at the end and are not cited below.

## 1. Learning to use tools and APIs

Two approaches appear in the findings:

- **Fine-tuning.** Toolformer [2302.04761] trains a language model, in a self-supervised way and starting from only a handful of demonstrations per API, to decide when to call a tool, which arguments to pass, and how to fold the result into its prediction. The tools include a calculator, Q&A, search, translation, and a calendar.
- **In-context prompting.** ReAct [2210.03629] requires no fine-tuning. The model interleaves reasoning traces with actions such as Wikipedia API calls, and it is prompted with only one or two in-context examples.

A newcomer should read these two as a contrast between learning tool use into the weights and eliciting it through prompting.

## 2. Reflecting on and correcting mistakes

The findings describe reflection methods that mostly work without weight updates:

- **Reflexion** [2303.11366] has agents verbally reflect on task feedback, external or simulated, and store those reflections in an episodic memory buffer that guides later attempts. It reports 91% pass@1 on HumanEval, above GPT-4's 80%.
- **Self-Refine** [2303.17651] has one LLM generate, critique, and refine its own output iteratively, with no training data. It improved outputs by about 20% absolute on average across seven tasks.
- **Renze & Guven** [2405.06682] found that nine LLMs that reflected on wrong multiple-choice answers and re-answered showed a significant gain (p < 0.001).
- **Kamoi et al.** [2406.01297], a survey, concludes that prompted self-correction has not been shown to succeed except on tasks suited to it. It works well with reliable external feedback, and large-scale fine-tuning enables it.

The main lesson is that the value of self-correction depends heavily on the quality of the feedback. Purely intrinsic self-critique is the weakest link.

## 3. Long-term memory

The findings describe three architectures:

- **Generative Agents** [2304.03442] stores every experience as a natural-language record, periodically synthesizes higher-level reflections, and retrieves memories to plan behavior. In a 25-agent sandbox, ablations showed that observation, planning, and reflection each matter for believability.
- **MemGPT** [2310.08560] applies operating-system-style virtual context management. Data moves between a fast in-context tier and slower external storage, and the LLM issues the memory operations itself. It was evaluated on long-document analysis and multi-session chat.
- **H-MEM** [2507.22925] organizes memory into layers of semantic abstraction, with index pointers from each vector to its sub-memories, and routes retrieval layer by layer. It was evaluated on five LoCoMo task settings against five baselines.

Across these, memory involves storing experiences, retrieving them by relevance, and periodically consolidating or summarizing them. The findings do not compare forgetting policies or parametric memory, so those remain open for a newcomer to investigate.

## Gaps and unverified works

The following were searched for but not found in the index, so this review makes no claims about them: Gorilla, ToolLLM, API-Bank (tool use); CRITIC, Self-RAG, Self-Debugging, and the Huang et al. intrinsic self-correction study (self-correction); MemoryBank (memory). These are widely cited and worth reading directly. The absence of a paper from the index does not mean it does not exist.
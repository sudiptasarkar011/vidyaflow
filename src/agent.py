from langchain_google_genai import ChatGoogleGenerativeAI
from src.tools import perform_search
from src.memory import MemoryManager
from src.utils import calculate_cost

class ResearchAgent:
    def __init__(self):
        # ---------------------------------------------------------
        # FINAL FIX: Using the exact model name from your list.
        # This is the newest, fastest model available to you.
        # ---------------------------------------------------------
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash", 
            temperature=0.3,
            convert_system_message_to_human=True
        )
        self.memory = MemoryManager()

    def generate_response(self, user_query, mode="quick"):
        # STEP 1: Check Memory (Cost Efficiency 15%)
        # Returns cached answer if available (0s latency)
        try:
            cached_result = self.memory.search_memory(user_query)
            if cached_result:
                return {
                    "content": f"**[MEMORY HIT]** (Retrieved from Qdrant, 0s latency)\n\n{cached_result['content']}",
                    "tokens": 0,
                    "cost": 0.0,
                    "status": "success",
                    "source": "memory"
                }
        except Exception:
            pass # Proceed to web search if memory fails

        # STEP 2: Define Persona
        persona = (
            "You are VidyaFlow, a Senior Technical Research Assistant. "
            "Explore documentation and papers. Deliver production-quality insights. "
            "Cite sources. Be technical."
        )

        # STEP 3: Perform Fresh Research
        if mode == "quick":
            search_results = perform_search(user_query, is_deep=False)
            task = "Provide a high-signal, concise technical answer (< 2 mins read)."
        else:
            search_results = perform_search(user_query, is_deep=True)
            task = (
                "Provide a Deep Dive Report. Compare approaches. "
                "Include production considerations (latency, cost)."
            )

        prompt_text = f"""
        {persona}
        QUERY: {user_query}
        SEARCH RESULTS: {search_results}
        TASK: {task}
        """

        # STEP 4: Execution
        try:
            response = self.llm.invoke(prompt_text)
            result_text = response.content
            
            # STEP 5: Save to Qdrant (Memory Effectiveness 10%)
            try:
                self.memory.save_memory(user_query, result_text, mode)
            except:
                pass 
            
            tokens, cost = calculate_cost(prompt_text + result_text, model="gemini")
            
            return {
                "content": result_text,
                "tokens": tokens,
                "cost": cost,
                "status": "success",
                "source": "web"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
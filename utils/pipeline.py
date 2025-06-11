from videosdk.agents import RealTimePipeline
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig

def create_main_pipeline(llm_model: str, api_key: str, voice: str = "Puck", 
                        temperature: float = 0.7, top_p: float = 0.9, top_k: int = 1) -> RealTimePipeline:
    """Creates pipeline for main travel agent (audio-enabled)"""
    model = GeminiRealtime(
        model=llm_model,
        api_key=api_key,
        config=GeminiLiveConfig(
            voice=voice,
            response_modalities=["AUDIO"],
            temperature=temperature,
            top_p=top_p,
            top_k=int(top_k),
        )
    )
    return RealTimePipeline(model=model)

def create_specialist_pipeline(llm_model: str, api_key: str) -> RealTimePipeline:
    """Creates pipeline for specialist agents (text-only)"""
    model = GeminiRealtime(
        model=llm_model,
        api_key=api_key,
        config=GeminiLiveConfig(
            response_modalities=["TEXT"]
        )
    )
    return RealTimePipeline(model=model) 
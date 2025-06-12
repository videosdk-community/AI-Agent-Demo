from videosdk.agents import CascadingPipeline
from videosdk.plugins.openai import OpenAILLM, OpenAITTS, OpenAISTT
from videosdk.plugins.google import GeminiRealtime, GeminiLiveConfig
from config import settings
from models import MeetingReqConfig


class PipelineFactory:
    """Factory class for creating AI processing pipelines."""
    
    @staticmethod
    def create_cascading_pipeline(config: MeetingReqConfig) -> CascadingPipeline:
        """
        Create a cascading pipeline with OpenAI components.
        
        Args:
            config: Meeting configuration with model parameters
            
        Returns:
            Configured CascadingPipeline instance
        """
        return CascadingPipeline(
            stt=OpenAISTT(api_key=settings.OPENAI_API_KEY),  # type: ignore
            llm=OpenAILLM(api_key=settings.OPENAI_API_KEY),  # type: ignore
            tts=OpenAITTS(api_key=settings.OPENAI_API_KEY),  # type: ignore
            # Commented out as in original code
            # vad=SileroVAD(),
            # turn_detector=TurnDetector(threshold=0.8)
        )
    
    @staticmethod
    def create_gemini_realtime_pipeline(config: MeetingReqConfig) -> GeminiRealtime:
        """
        Create a Gemini realtime pipeline (currently commented out in original).
        
        Args:
            config: Meeting configuration with model parameters
            
        Returns:
            Configured GeminiRealtime instance
        """
        # This was commented out in the original code but keeping for reference
        return GeminiRealtime(
            model=config.model,
            api_key=settings.GOOGLE_API_KEY,
            config=GeminiLiveConfig(
                voice=config.voice,  # type: ignore
                response_modalities=["AUDIO"],  # type: ignore
                temperature=config.temperature,
                top_p=config.topP,
                top_k=int(config.topK),
            )
        )
    
    @staticmethod
    def get_default_pipeline(config: MeetingReqConfig) -> CascadingPipeline:
        """
        Get the default pipeline configuration.
        
        Args:
            config: Meeting configuration with model parameters
            
        Returns:
            Default configured pipeline
        """
        return PipelineFactory.create_cascading_pipeline(config) 
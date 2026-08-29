from tools.database_tool import (
    DatabaseTool
)

from tools.transcription_tool import (
    TranscriptionTool
)

from tools.diarization_tool import (
    DiarizationTool
)

from tools.alignment_tool import (
    AlignmentTool
)

from tools.sentiment_tool import (
    SentimentTool
)

from tools.emotion_tool import (
    EmotionTool
)

from tools.root_cause_tool import (
    RootCauseTool
)

from tools.churn_risk_tool import (
    ChurnRiskTool
)


class ToolRegistry:

    def __init__(self):

        # -------------------------------------------------
        # Store classes instead of immediately
        # instantiating them.
        # -------------------------------------------------

        self.tool_classes = {

            "get_call_analysis_state":
                DatabaseTool,

            "transcribe_call":
                TranscriptionTool,

            "diarize_call":
                DiarizationTool,

            "align_transcript_with_speakers":
                AlignmentTool,

            "analyze_customer_sentiment":
                SentimentTool,

            "analyze_customer_emotion":
                EmotionTool,

            "identify_dissatisfaction_root_cause":
                RootCauseTool,

            "analyze_customer_churn_risk":
                ChurnRiskTool
        }

        self._instances = {}

    # =====================================================
    # GET TOOL
    # =====================================================

    def get_tool(
        self,
        name
    ):

        if name not in self.tool_classes:

            raise ValueError(
                f"Unknown tool: {name}"
            )

        # -------------------------------------------------
        # Create only when actually needed
        # -------------------------------------------------

        if name not in self._instances:

            self._instances[name] = (
                self.tool_classes[name]()
            )

        return self._instances[name]

    # =====================================================
    # DESCRIPTIONS
    # =====================================================

    def get_descriptions(self):

        descriptions = []

        for name, tool_class in (
            self.tool_classes.items()
        ):

            descriptions.append({

                "name":
                    name,

                "description":
                    getattr(
                        tool_class,
                        "description",
                        ""
                    )
            })

        return descriptions
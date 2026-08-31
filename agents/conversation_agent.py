import json
import re

from agents.local_slm import (
    LocalSLM
)

from agents.tool_registry import (
    ToolRegistry
)

from tools.database_tool import (
    DatabaseTool
)


MAX_AGENT_STEPS = 10


class ConversationAgent:

    SYSTEM_PROMPT = """
You are the Conversation Intelligence Agent
for a banking customer-call analytics system.

Your job is to decide WHICH TOOL should be
executed next.

You do not perform transcription,
diarization, sentiment, emotion or root-cause
analysis yourself.

AVAILABLE TOOLS:

1. transcribe_call
2. diarize_call
3. align_transcript_with_speakers
4. analyze_customer_sentiment
5. analyze_customer_emotion
6. identify_dissatisfaction_root_cause

DEPENDENCIES:

transcription
    ↓
diarization
    ↓
alignment
    ↓
sentiment
    ↓
emotion
    ↓
root cause

DECISION ORDER:

1. Missing transcription
   -> transcribe_call

2. Missing diarization
   -> diarize_call

3. Missing alignment
   -> align_transcript_with_speakers

4. Missing sentiment
   -> analyze_customer_sentiment

5. Missing emotion
   -> analyze_customer_emotion

6. Negative sentiment AND missing root cause
   -> identify_dissatisfaction_root_cause

7. Otherwise
   -> final

Never call a tool whose output already exists.

Return ONLY valid JSON.

Tool action:

{
    "action": "tool",
    "tool": "tool_name",
    "reason": "short explanation"
}

Final action:

{
    "action": "final",
    "reason": "analysis is complete"
}
"""

    def __init__(
        self,
        model_path=None,
        progress_callback=None
    ):

        self.slm = LocalSLM(
            model_path
        )

        self.registry = (
            ToolRegistry()
        )

        self.state_tool = (
            DatabaseTool()
        )

        self.progress_callback = progress_callback

    # =====================================================
    # ANALYZE CALL
    # =====================================================

    def analyze_call(
        self,
        call_id
    ):

        state = (
            self.state_tool.run(
                call_id
            )
        )

        if not state.get(
            "call_exists",
            False
        ):

            return {

                "action":
                    "final",

                "analysis": {

                    "status":
                        "ERROR",

                    "message":
                        "Call does not exist."
                },

                "execution_trace":
                    []
            }

        execution_trace = []

        # =================================================
        # AGENT LOOP
        # =================================================

        for step in range(
            MAX_AGENT_STEPS
        ):

            # ---------------------------------------------
            # Ask Qwen
            # ---------------------------------------------

            messages = [

                {
                    "role":
                        "system",

                    "content":
                        self.SYSTEM_PROMPT
                },

                {
                    "role":
                        "user",

                    "content":
                        (
                            "CURRENT CALL STATE:\n"
                            + json.dumps(
                                state,
                                indent=2,
                                default=str
                            )
                            + "\n\n"
                            "Select the next action."
                        )
                }
            ]

            try:

                raw_response = (
                    self.slm.generate(
                        messages,
                        max_new_tokens=128
                    )
                )

                decision = (
                    self.parse_json(
                        raw_response
                    )
                )

            except Exception as e:

                return {

                    "action":
                        "final",

                    "analysis": {

                        "status":
                            "AGENT_ERROR",

                        "message":
                            str(e)
                    },

                    "execution_trace":
                        execution_trace
                }

            # ---------------------------------------------
            # Determine required action from state
            # ---------------------------------------------

            required_tool = (
                self.get_required_tool(
                    state
                )
            )

            # ---------------------------------------------
            # FINAL
            # ---------------------------------------------

            if required_tool is None:

                final_analysis = (
                    self.build_final_analysis(
                        state
                    )
                )

                recommendation_decision = None

                # -------------------------------------------------
                # Get persisted recommendation decision
                # -------------------------------------------------

                churn_risk = (
                    state.get(
                        "churn_risk"
                    )
                    or {}
                )

                recommendation_decision = (
                    churn_risk.get(
                        "recommendation_decision"
                    )
                )

                return {

                    "action":
                        "final",

                    "analysis":
                        final_analysis,

                    "recommendation_decision":
                        recommendation_decision,

                    "execution_trace":
                        execution_trace
                }

            # ---------------------------------------------
            # SLM proposed action
            # ---------------------------------------------

            proposed_action = (
                decision.get(
                    "action"
                )
            )

            proposed_tool = (
                decision.get(
                    "tool"
                )
            )

            reason = (
                decision.get(
                    "reason",
                    ""
                )
            )

            # ---------------------------------------------
            # Guardrail
            #
            # If Qwen selected the wrong tool,
            # execute the required dependency instead.
            # ---------------------------------------------

            if (
                proposed_action != "tool"
                or proposed_tool
                != required_tool
            ):

                tool_name = (
                    required_tool
                )

                if reason:

                    reason = (
                        f"SLM proposed "
                        f"{proposed_tool}, but "
                        f"dependency requires "
                        f"{required_tool}. "
                        f"{reason}"
                    )

                else:

                    reason = (
                        "Required by the current "
                        "processing state."
                    )

            else:

                tool_name = (
                    proposed_tool
                )

            # ---------------------------------------------
            # Get tool
            # ---------------------------------------------

            try:

                tool = (
                    self.registry
                    .get_tool(
                        tool_name
                    )
                )

            except Exception as e:

                return {

                    "action":
                        "final",

                    "analysis": {

                        "status":
                            "TOOL_ERROR",

                        "message":
                            str(e)
                    },

                    "execution_trace":
                        execution_trace
                }

            # ---------------------------------------------
            # Record execution
            # ---------------------------------------------

            event = {

                "step":
                    step + 1,

                "tool":
                    tool_name,

                "reason":
                    reason,

                "status":
                    "running"
            }

            execution_trace.append(
                event
            )

            # ---------------------------------------------
            # Execute
            # ---------------------------------------------

            try:

                self.report_progress(
                    tool_name,
                    "running",
                    self.get_progress_message(
                        tool_name,
                    )
                )

                tool_result = (
                    tool.run(
                        call_id=call_id
                    )
                )

            except Exception as e:

                tool_result = {

                    "success":
                        False,

                    "error":
                        str(e)
                }

            # ---------------------------------------------
            # Result status
            # ---------------------------------------------

            if tool_result.get(
                "success",
                False
            ):

                self.report_progress(
                    tool_name,
                    "success",
                    "Processing completed successfully.",
                    tool_result
                )

            else:

                self.report_progress(
                    tool_name,
                    "error",
                    tool_result.get(
                        "error",
                        "Processing failed."
                    ),
                    tool_result
                )

            event["result"] = (
                tool_result
            )

            # ---------------------------------------------
            # Stop on tool failure
            # ---------------------------------------------

            if not tool_result.get(
                "success",
                False
            ):

                return {

                    "action":
                        "final",

                    "analysis": {

                        "status":
                            "TOOL_FAILED",

                        "failed_tool":
                            tool_name,

                        "error":
                            tool_result.get(
                                "error",
                                "Unknown error"
                            )
                    },

                    "execution_trace":
                        execution_trace
                }

            # ---------------------------------------------
            # Refresh DB state
            # ---------------------------------------------

            state = (
                self.state_tool.run(
                    call_id
                )
            )

        # =================================================
        # MAX STEPS
        # =================================================

        return {

            "action":
                "final",

            "analysis": {

                "status":
                    "MAX_STEPS_REACHED"
            },

            "execution_trace":
                execution_trace
        }

    # =====================================================
    # REQUIRED TOOL
    # =====================================================

    def get_required_tool(
        self,
        state
    ):

        if not state.get(
            "transcription_complete",
            False
        ):

            return "transcribe_call"

        if not state.get(
            "diarization_complete",
            False
        ):

            return "diarize_call"

        if not state.get(
            "alignment_complete",
            False
        ):

            return (
                "align_transcript_with_speakers"
            )

        if not state.get(
            "sentiment_complete",
            False
        ):

            return (
                "analyze_customer_sentiment"
            )

        if not state.get(
            "emotion_complete",
            False
        ):

            return (
                "analyze_customer_emotion"
            )

        if not state.get(
            "churn_risk_complete",
            False
        ):

            if state.get(
                "root_cause_complete",
                False
            ):

                return (
                    "analyze_customer_churn_risk"
                )            

        sentiment = (
            state.get(
                "sentiment"
            )
            or {}
        )

        sentiment_label = str(
            sentiment.get(
                "sentiment",
                ""
            )
        ).upper()

        if (
            sentiment_label
            in (
                "NEGATIVE",
                "DISSATISFIED"
            )
            and not state.get(
                "root_cause_complete",
                False
            )
        ):

            return (
                "identify_dissatisfaction_root_cause"
            )

        return None

    # =====================================================
    # JSON PARSER
    # =====================================================

    def parse_json(
        self,
        response
    ):

        if not response:

            raise ValueError(
                "Qwen returned an empty response."
            )

        response = str(
            response
        ).strip()

        response = re.sub(
            r"```json\s*",
            "",
            response,
            flags=re.IGNORECASE
        )

        response = re.sub(
            r"```\s*$",
            "",
            response
        )

        response = response.strip()

        # -------------------------------------------------
        # Try complete response
        # -------------------------------------------------

        try:

            return json.loads(
                response
            )

        except json.JSONDecodeError:
            pass

        # -------------------------------------------------
        # Extract JSON object
        # -------------------------------------------------

        start = response.find(
            "{"
        )

        end = response.rfind(
            "}"
        )

        if (
            start == -1
            or end == -1
            or end <= start
        ):

            raise ValueError(
                "Qwen did not return valid JSON:\n"
                + response
            )

        return json.loads(
            response[
                start:
                end + 1
            ]
        )

    # =====================================================
    # FINAL ANALYSIS
    # =====================================================

    def build_final_analysis(
        self,
        state
    ):

        sentiment = (
            state.get(
                "sentiment"
            )
            or {}
        )

        emotion = (
            state.get(
                "emotion"
            )
            or {}
        )

        root_cause = (
            state.get(
                "root_cause"
            )
            or {}
        )

        dissatisfaction = (
            root_cause.get(
                "dissatisfaction",
                "N/A"
            )
        )

        # Normalize DB representation

        if str(
            dissatisfaction
        ).lower() in (
            "true",
            "yes",
            "1"
        ):

            dissatisfaction = "YES"

        elif str(
            dissatisfaction
        ).lower() in (
            "false",
            "no",
            "0"
        ):

            dissatisfaction = "NO"

        return {

            "sentiment":
                sentiment.get(
                    "sentiment",
                    "N/A"
                ),

            "sentiment_score":
                sentiment.get(
                    "sentiment_score"
                ),

            "emotion":
                emotion.get(
                    "primary_emotion",
                    "N/A"
                ),

            "emotion_score":
                emotion.get(
                    "emotion_score"
                ),

            "emotion_intensity":
                emotion.get(
                    "emotion_intensity"
                ),

            "root_cause_category":
                root_cause.get(
                    "root_cause_category",
                    "N/A"
                ),

            "root_cause":
                root_cause.get(
                    "root_cause",
                    "N/A"
                ),

            "severity":
                root_cause.get(
                    "severity",
                    "N/A"
                ),

            "dissatisfied":
                dissatisfaction,

            "confidence":
                root_cause.get(
                    "confidence"
                ),

            "evidence":
                root_cause.get(
                    "evidence",
                    ""
                )
        }

    def get_progress_message(
        self,
        tool_name
    ):

        messages = {

            "transcribe_call":
                "Transcribing the call recording and extracting timestamped speech segments...",

            "diarize_call":
                "Identifying the different speakers and determining when each speaker is talking...",

            "align_transcript_with_speakers":
                "Matching the transcription segments with the detected speakers to build the speaker-labelled conversation...",

            "analyze_customer_sentiment":
                "Analyzing the customer's conversation to determine sentiment and negativity level...",

            "analyze_customer_emotion":
                "Analyzing the customer's emotional signals including anger, frustration, disappointment and confusion...",

            "identify_dissatisfaction_root_cause":
                "Analyzing the customer's complaint to determine the primary reason for dissatisfaction...",

            "analyze_customer_churn_risk":
                "Calculating customer churn risk and evaluating retention and recovery rules..."
        }

        return messages.get(
            tool_name,
            "Processing the call..."
        )        

    def report_progress(
        self,
        module,
        status,
        message,
        result=None
    ):

        if self.progress_callback:

            self.progress_callback(
                {
                    "module": module,
                    "status": status,
                    "message": message,
                    "result": result
                }
            )        

  
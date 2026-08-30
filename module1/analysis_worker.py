from concurrent.futures import ThreadPoolExecutor
from threading import Lock


# =========================================================
# GLOBAL WORKER
# =========================================================

_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="voice-analysis"
)


_jobs = {}

_jobs_lock = Lock()


# =========================================================
# JOB CREATION
# =========================================================

def start_analysis(
    call_id
):

    with _jobs_lock:

        existing = _jobs.get(
            call_id
        )

        if existing:

            if existing["status"] in (
                "queued",
                "running"
            ):

                return call_id

        _jobs[call_id] = {

            "call_id":
                call_id,

            "status":
                "queued",

            "messages":
                [],

            "result":
                None,

            "error":
                None
        }

    _executor.submit(
        _run_analysis,
        call_id
    )

    return call_id


# =========================================================
# BACKGROUND EXECUTION
# =========================================================

def _run_analysis(
    call_id
):

    def progress_callback(
        event
    ):

        with _jobs_lock:

            job = _jobs.get(
                call_id
            )

            if not job:
                return

            job[
                "messages"
            ].append(
                dict(event)
            )

            job[
                "status"
            ] = "running"

    try:

        with _jobs_lock:

            job = _jobs.get(
                call_id
            )

            if job:

                job[
                    "status"
                ] = "running"

        from agents.conversation_agent import (
            ConversationAgent
        )

        agent = ConversationAgent(
            progress_callback=progress_callback
        )

        result = agent.analyze_call(
            call_id
        )

        with _jobs_lock:

            job = _jobs.get(
                call_id
            )

            if job:

                job[
                    "result"
                ] = result

                job[
                    "status"
                ] = "completed"

    except Exception as e:

        with _jobs_lock:

            job = _jobs.get(
                call_id
            )

            if job:

                job[
                    "status"
                ] = "failed"

                job[
                    "error"
                ] = str(e)

                job[
                    "messages"
                ].append(
                    {
                        "module":
                            "analysis",

                        "status":
                            "error",

                        "message":
                            str(e),

                        "result":
                            None
                    }
                )


# =========================================================
# JOB STATUS
# =========================================================

def get_analysis_status(
    call_id
):

    with _jobs_lock:

        job = _jobs.get(
            call_id
        )

        if not job:

            return None

        return {

            "call_id":
                job["call_id"],

            "status":
                job["status"],

            "messages":
                list(
                    job["messages"]
                ),

            "result":
                job["result"],

            "error":
                job["error"]
        }
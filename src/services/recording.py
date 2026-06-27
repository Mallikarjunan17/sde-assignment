"""
Recording pipeline — fetches the call recording from Exotel and uploads to S3.

Improved implementation:
- Replaces fixed 45-second wait
- Polls Exotel with exponential backoff
- Structured logging
- Observable failures
"""

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Retry schedule (seconds)
RETRY_DELAYS = [0, 5, 10, 20, 40, 80]


async def fetch_and_upload_recording(
    interaction_id: str,
    call_sid: str,
    exotel_account_id: str,
) -> Optional[str]:
    """
    Poll Exotel until the recording becomes available.

    Returns:
        S3 key on success
        None after all retries fail
    """

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):

        if delay:
            await asyncio.sleep(delay)

        try:
            recording_url = await _fetch_exotel_recording_url(
                call_sid,
                exotel_account_id,
            )

            if recording_url:
                s3_key = await _upload_to_s3(
                    recording_url,
                    interaction_id,
                )

                logger.info(
                    "recording_upload_success",
                    extra={
                        "interaction_id": interaction_id,
                        "attempt": attempt,
                        "s3_key": s3_key,
                    },
                )

                return s3_key

            logger.info(
                "recording_not_ready",
                extra={
                    "interaction_id": interaction_id,
                    "attempt": attempt,
                    "delay_seconds": delay,
                },
            )

        except Exception as e:
            logger.exception(
                "recording_attempt_failed",
                extra={
                    "interaction_id": interaction_id,
                    "attempt": attempt,
                    "error": str(e),
                },
            )

    logger.error(
        "recording_upload_failed",
        extra={
            "interaction_id": interaction_id,
            "call_sid": call_sid,
            "retry_attempts": len(RETRY_DELAYS),
        },
    )

    return None


async def _fetch_exotel_recording_url(
    call_sid: str,
    account_id: str,
) -> Optional[str]:
    """
    Poll Exotel recording endpoint.
    """

    url = (
        f"https://api.exotel.com/v1/Accounts/"
        f"{account_id}/Calls/{call_sid}/Recording"
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

            if response.status_code == 200:
                data = response.json()
                return data.get("recording_url")

            if response.status_code == 404:
                return None

            logger.warning(
                "unexpected_recording_status",
                extra={
                    "call_sid": call_sid,
                    "status_code": response.status_code,
                },
            )

            return None

    except httpx.HTTPError as e:
        logger.exception(
            "recording_api_error",
            extra={
                "call_sid": call_sid,
                "error": str(e),
            },
        )
        return None


async def _upload_to_s3(
    recording_url: str,
    interaction_id: str,
) -> str:
    """
    Mock S3 upload.
    """

    s3_key = f"recordings/{interaction_id}.mp3"

    logger.info(
        "recording_uploaded",
        extra={
            "interaction_id": interaction_id,
            "s3_key": s3_key,
        },
    )

    return s3_key
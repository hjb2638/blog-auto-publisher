import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def is_retryable_llm(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        return exception.response.status_code in {429, 500, 502, 503, 504}
    if isinstance(exception, (httpx.ConnectError, httpx.ReadTimeout, httpx.RemoteProtocolError)):
        return True
    return False


def is_retryable_wp(exception: BaseException) -> bool:
    if isinstance(exception, httpx.HTTPStatusError):
        code = exception.response.status_code
        if code == 401:
            return False
        return code in {429, 500, 502, 503}
    if isinstance(exception, (httpx.ConnectError, httpx.ReadTimeout)):
        return True
    return False


llm_retry = retry(
    retry=retry_if_exception(is_retryable_llm),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

wp_retry = retry(
    retry=retry_if_exception(is_retryable_wp),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=8),
    reraise=True,
)

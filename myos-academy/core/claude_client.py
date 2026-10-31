"""Thin wrapper around the official anthropic SDK plus Vietnamese error messages."""
from __future__ import annotations

import anthropic


def make_client(api_key: str, timeout: float = 600.0) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)


def list_models(api_key: str) -> list[str]:
    """Fetch available model ids. Free to call, so it doubles as an API key check."""
    client = make_client(api_key, timeout=20.0)
    return [model.id for model in client.models.list(limit=100)]


def friendly_error(exc: BaseException) -> str:
    """Turn an SDK exception into a message a learner can act on."""
    if isinstance(exc, anthropic.AuthenticationError):
        return "API key không hợp lệ hoặc đã bị thu hồi. Hãy kiểm tra lại trong Cài đặt."
    if isinstance(exc, anthropic.PermissionDeniedError):
        return "API key không có quyền dùng tính năng hoặc model này."
    if isinstance(exc, anthropic.NotFoundError):
        return "Không tìm thấy model. Hãy chọn model khác trong Cài đặt."
    if isinstance(exc, anthropic.RateLimitError):
        return "Gửi yêu cầu quá nhanh hoặc đã hết hạn mức. Đợi một lát rồi thử lại."
    if isinstance(exc, anthropic.BadRequestError):
        if "credit balance" in str(exc).lower():
            return "Tài khoản Anthropic đã hết tiền (credit). Nạp thêm tại console.anthropic.com."
        return f"Yêu cầu không hợp lệ: {exc.message}"
    if isinstance(exc, anthropic.InternalServerError):
        return "Máy chủ Anthropic đang lỗi hoặc quá tải. Thử lại sau ít phút."
    if isinstance(exc, anthropic.APIStatusError):
        return f"Lỗi từ máy chủ (mã {exc.status_code}): {exc.message}"
    if isinstance(exc, anthropic.APITimeoutError):
        return "Hết thời gian chờ phản hồi. Kiểm tra mạng rồi thử lại."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Không kết nối được tới máy chủ. Kiểm tra mạng Internet."
    return f"Lỗi không mong đợi: {exc}"

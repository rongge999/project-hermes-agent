"""Response wrapper utilities."""
from fastapi.responses import JSONResponse


def ok(data=None, msg="成功"):
    return {"code": 200, "msg": msg, "data": data if data is not None else []}


def fail(code: int, msg: str):
    return JSONResponse(status_code=200, content={"code": code, "msg": msg, "data": None})


def paginate(items, total, page, page_size):
    return {"items": items, "total": total, "page": page, "page_size": page_size}
